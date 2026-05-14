#!/usr/bin/env python3
"""Multi-session coordination for Claude Code (M1: state library + SessionStart).

Single-file design: state library + hook dispatcher. Invoked by Claude Code
via settings.json hook commands like:
    python multi_session.py session-start

Hook input arrives on stdin as JSON. Output to stdout (if any) is parsed by
Claude Code as JSON to influence behavior. Exit 0 = success; exit 2 = block.

State storage: ~/.claude/multi-session-coord/<encoded-cwd>/
  registry.json          ← global: active sessions + lease holdings
  sessions/<id>.json     ← per-session: intent / touched / inbox / heartbeat
  archive/YYYY-MM-DD/    ← ended sessions, archived when caller is solo
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STALE_THRESHOLD_MIN = 30
ROOT_DIR_NAME = "multi-session-coord"


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def encode_cwd(cwd: str) -> str:
    """Map a working-directory path to a filesystem-safe slug.

    Rule: replace [:\\/_ ] with '-'. Case preserved. Matches the inferred
    Claude Code convention closely enough that the encoded names look
    familiar, but this is OUR encoding — we don't depend on Claude Code's
    internal scheme.
    """
    return re.sub(r"[:\\/_ ]", "-", cwd)


def _base_dir() -> Path:
    """Resolve the root of all per-project state dirs.

    Honors $MULTI_SESSION_BASE if set (used by tests to isolate state into
    a temp dir). Otherwise defaults to ~/.claude/multi-session-coord/.
    """
    override = os.environ.get("MULTI_SESSION_BASE")
    if override:
        return Path(override)
    return Path.home() / ".claude" / ROOT_DIR_NAME


def project_root(cwd: str) -> Path:
    """Return the per-project concurrency directory; create if missing."""
    base = _base_dir() / encode_cwd(cwd)
    (base / "sessions").mkdir(parents=True, exist_ok=True)
    return base


def registry_path(cwd: str) -> Path:
    return project_root(cwd) / "registry.json"


def session_path(cwd: str, session_id: str) -> Path:
    return project_root(cwd) / "sessions" / f"{session_id}.json"


def archive_dir(cwd: str, date_str: str | None = None) -> Path:
    date_str = date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    d = project_root(cwd) / "archive" / date_str
    d.mkdir(parents=True, exist_ok=True)
    return d


def normalize_target(cwd: str, target: str) -> str:
    """Reduce a tool's file_path to a project-relative form (forward slashes).

    - Absolute path under cwd → relative path
    - Already-relative path → kept (just unified to forward slashes)
    - Absolute path outside cwd → kept absolute (won't accidentally match a
      relative lease)
    """
    if not target:
        return target
    cwd_norm = os.path.normpath(cwd).replace("\\", "/").rstrip("/")
    target_norm = os.path.normpath(target).replace("\\", "/")
    # Case-insensitive prefix check on Windows; case-sensitive elsewhere.
    if os.name == "nt":
        if target_norm.lower().startswith(cwd_norm.lower() + "/"):
            return target_norm[len(cwd_norm) + 1:]
        if target_norm.lower() == cwd_norm.lower():
            return ""
    else:
        if target_norm.startswith(cwd_norm + "/"):
            return target_norm[len(cwd_norm) + 1:]
        if target_norm == cwd_norm:
            return ""
    return target_norm


# ---------------------------------------------------------------------------
# Atomic JSON I/O
# ---------------------------------------------------------------------------

def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def write_json(path: Path, data: dict[str, Any]) -> None:
    """Atomic write: temp file in same dir + os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(s: str) -> datetime | None:
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def age_minutes(iso_ts: str) -> float | None:
    t = parse_iso(iso_ts)
    if t is None:
        return None
    return (datetime.now(timezone.utc) - t).total_seconds() / 60.0


# ---------------------------------------------------------------------------
# Registry / session primitives
# ---------------------------------------------------------------------------

def empty_registry() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "active_sessions": []}


def empty_session(session_id: str, status: str = "discussion") -> dict[str, Any]:
    ts = now_iso()
    return {
        "schema_version": SCHEMA_VERSION,
        "session_id": session_id,
        "started_at": ts,
        "last_heartbeat": ts,
        "status": status,
        "mode": "discussion",
        "intent_summary": None,
        "scope_hint": None,
        "claimed_paths": [],
        "touched_files": [],
        "inbox": [],
        "outbox_log": [],
        "commits": [],
    }


def load_registry(cwd: str) -> dict[str, Any]:
    return read_json(registry_path(cwd)) or empty_registry()


def save_registry(cwd: str, reg: dict[str, Any]) -> None:
    write_json(registry_path(cwd), reg)


def load_session(cwd: str, session_id: str) -> dict[str, Any] | None:
    return read_json(session_path(cwd, session_id))


def save_session(cwd: str, session: dict[str, Any]) -> None:
    write_json(session_path(cwd, session["session_id"]), session)


def register_session(cwd: str, session_id: str, status: str = "discussion") -> dict[str, Any]:
    """Create or refresh a session entry in registry + sessions/."""
    reg = load_registry(cwd)
    existing = next(
        (s for s in reg["active_sessions"] if s["session_id"] == session_id), None
    )
    ts = now_iso()
    if existing is None:
        entry = {
            "session_id": session_id,
            "started_at": ts,
            "last_heartbeat": ts,
            "status": status,
            "mode": "discussion",
            "intent_summary": None,
            "lease_paths": [],
        }
        reg["active_sessions"].append(entry)
    else:
        existing["last_heartbeat"] = ts
        existing["status"] = status
    save_registry(cwd, reg)

    session = load_session(cwd, session_id)
    if session is None:
        session = empty_session(session_id, status)
    else:
        session["last_heartbeat"] = ts
        session["status"] = status
    save_session(cwd, session)
    return session


def update_heartbeat(cwd: str, session_id: str) -> None:
    ts = now_iso()
    reg = load_registry(cwd)
    for s in reg["active_sessions"]:
        if s["session_id"] == session_id:
            s["last_heartbeat"] = ts
            break
    save_registry(cwd, reg)

    session = load_session(cwd, session_id)
    if session is not None:
        session["last_heartbeat"] = ts
        save_session(cwd, session)


def is_stale(entry: dict[str, Any], stale_min: int = STALE_THRESHOLD_MIN) -> bool:
    age = age_minutes(entry.get("last_heartbeat", ""))
    return age is not None and age > stale_min


def active_sessions(cwd: str, exclude: str | None = None, stale_min: int = STALE_THRESHOLD_MIN) -> list[dict[str, Any]]:
    reg = load_registry(cwd)
    return [
        s for s in reg["active_sessions"]
        if s.get("session_id") != exclude
        and s.get("status") != "ended"
        and not is_stale(s, stale_min)
    ]


# ---------------------------------------------------------------------------
# Lease primitives
# ---------------------------------------------------------------------------

def _path_overlaps(a: str, b: str) -> bool:
    """Return True if either path is a prefix of the other (dir-style)."""
    a = a.rstrip("/\\")
    b = b.rstrip("/\\")
    if a == b:
        return True
    # 'foo/' is a prefix of 'foo/bar' (treat trailing slash as directory)
    return a.startswith(b + "/") or b.startswith(a + "/")


def add_lease(cwd: str, session_id: str, path: str) -> None:
    reg = load_registry(cwd)
    for s in reg["active_sessions"]:
        if s["session_id"] == session_id:
            if path not in s["lease_paths"]:
                s["lease_paths"].append(path)
            break
    save_registry(cwd, reg)


def remove_lease(cwd: str, session_id: str, path: str) -> None:
    reg = load_registry(cwd)
    for s in reg["active_sessions"]:
        if s["session_id"] == session_id:
            s["lease_paths"] = [p for p in s["lease_paths"] if p != path]
            break
    save_registry(cwd, reg)


def find_lease_holder(cwd: str, path: str, stale_min: int = STALE_THRESHOLD_MIN) -> dict[str, Any] | None:
    """Return the session entry holding (or overlapping) `path`, ignoring stale."""
    for s in active_sessions(cwd, stale_min=stale_min):
        for held in s.get("lease_paths", []):
            if _path_overlaps(path, held):
                return s
    return None


def add_touched_file(cwd: str, session_id: str, path: str) -> None:
    """Append a file path to the session's touched_files (dedup)."""
    if not path:
        return
    session = load_session(cwd, session_id)
    if session is None:
        return
    if path not in session.setdefault("touched_files", []):
        session["touched_files"].append(path)
    save_session(cwd, session)


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

def invoke_cleanup(cwd: str, self_session_id: str | None = None, stale_min: int = STALE_THRESHOLD_MIN) -> dict[str, Any]:
    """Run stale cleanup + maybe archive.

    Returns a report dict: {released_leases, ended_count, archived_count, kept_count}
    """
    reg = load_registry(cwd)
    report = {"released_leases": [], "ended": [], "archived": [], "kept_count": 0}

    # Pass 1: detect stale -> release leases + mark ended
    for s in reg["active_sessions"]:
        if s.get("status") == "ended":
            continue
        if is_stale(s, stale_min):
            for path in s.get("lease_paths", []):
                report["released_leases"].append({"session_id": s["session_id"], "path": path})
            s["lease_paths"] = []
            s["status"] = "ended"
            report["ended"].append(s["session_id"])
            # Also update sessions/<id>.json
            session = load_session(cwd, s["session_id"])
            if session is not None:
                session["status"] = "ended"
                save_session(cwd, session)

    save_registry(cwd, reg)

    # Pass 2: count truly active (heartbeat fresh, not ended, not self)
    fresh_others = [
        s for s in reg["active_sessions"]
        if s["session_id"] != self_session_id
        and s.get("status") != "ended"
        and not is_stale(s, stale_min)
    ]
    report["kept_count"] = len(fresh_others)

    # Pass 3: if we're the only fresh session -> archive ended entries
    if not fresh_others:
        adir = archive_dir(cwd)
        new_active = []
        for s in reg["active_sessions"]:
            if s.get("status") == "ended" or is_stale(s, stale_min):
                src = session_path(cwd, s["session_id"])
                if src.exists():
                    dst = adir / src.name
                    try:
                        os.replace(src, dst)
                        report["archived"].append(s["session_id"])
                    except OSError:
                        pass
            else:
                new_active.append(s)
        reg["active_sessions"] = new_active
        save_registry(cwd, reg)

    return report


# ---------------------------------------------------------------------------
# Hook handlers
# ---------------------------------------------------------------------------

def hook_session_start(payload: dict[str, Any]) -> dict[str, Any]:
    """Handle SessionStart event.

    1. Cleanup stale entries
    2. Register self (status=discussion)
    3. Return additionalContext listing other active sessions
    """
    cwd = payload.get("cwd") or os.getcwd()
    session_id = payload.get("session_id") or str(uuid.uuid4())

    cleanup_report = invoke_cleanup(cwd, self_session_id=session_id)
    register_session(cwd, session_id, status="discussion")

    others = active_sessions(cwd, exclude=session_id)
    if not others:
        body = "No other active Claude Code sessions in this project."
    else:
        lines = ["Other active Claude Code sessions in this project:"]
        for s in others:
            leases = s.get("lease_paths") or []
            lease_str = f"holds [{', '.join(leases)}]" if leases else "no leases"
            # Intent lives in per-session file (registry holds only the
            # short summary mirror; per-session is authoritative).
            full_session = load_session(cwd, s["session_id"]) or {}
            intent = full_session.get("intent_summary") or "(no intent declared yet)"
            lines.append(
                f"  - {s['session_id'][:8]} status={s.get('status', 'unknown')} {lease_str} — {intent}"
            )
        body = "\n".join(lines)

    if cleanup_report["archived"]:
        body += f"\n\n[cleanup] Archived {len(cleanup_report['archived'])} ended session(s)."
    elif cleanup_report["ended"]:
        body += f"\n\n[cleanup] Marked {len(cleanup_report['ended'])} stale session(s) as ended (will archive on next solo start)."

    return {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": body,
        }
    }


def _extract_tool_path(payload: dict[str, Any]) -> str | None:
    """Pull file_path out of a PreToolUse/PostToolUse payload.

    Edit / Write / MultiEdit all carry tool_input.file_path. Return None
    if missing (defensive — hook will then no-op).
    """
    ti = payload.get("tool_input") or {}
    fp = ti.get("file_path")
    return fp if isinstance(fp, str) and fp else None


def hook_pre_tool_edit(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Handle PreToolUse for Edit / Write / MultiEdit.

    Check whether the target file_path is held by another active session's
    lease. If yes, deny the tool call with permissionDecision so the agent
    sees a structured rejection and can decide (let / claim later / pick
    different work).
    """
    cwd = payload.get("cwd") or os.getcwd()
    self_id = payload.get("session_id") or ""
    target_raw = _extract_tool_path(payload)
    if not target_raw:
        return None  # no path -> nothing to check

    target = normalize_target(cwd, target_raw)
    holder = find_lease_holder(cwd, target)
    if holder is None or holder.get("session_id") == self_id:
        # No conflict (or it's our own lease) — allow.
        return None

    intent = (load_session(cwd, holder["session_id"]) or {}).get("intent_summary") or "(no intent declared)"
    reason = (
        f"File '{target}' is leased by session {holder['session_id'][:8]} "
        f"(status={holder.get('status', 'unknown')}, intent: {intent}). "
        "Coordinate via inbox (write a release_request to that session) "
        "or work on a non-overlapping path."
    )
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def hook_post_tool_edit(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Handle PostToolUse for Edit / Write / MultiEdit.

    Append the touched file to self.touched_files; refresh heartbeat. No
    output (hook does not influence Claude further on PostToolUse).
    """
    cwd = payload.get("cwd") or os.getcwd()
    self_id = payload.get("session_id") or ""
    target_raw = _extract_tool_path(payload)
    if not target_raw or not self_id:
        return None

    target = normalize_target(cwd, target_raw)
    # Make sure the session exists (defensive — SessionStart should have
    # registered already; if not, create a stub).
    if load_session(cwd, self_id) is None:
        register_session(cwd, self_id, status="discussion")
    add_touched_file(cwd, self_id, target)
    update_heartbeat(cwd, self_id)
    return None


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

HOOK_HANDLERS = {
    "session-start": hook_session_start,
    "pre-tool-edit": hook_pre_tool_edit,
    "post-tool-edit": hook_post_tool_edit,
}


def read_payload() -> dict[str, Any]:
    """Read hook input from stdin. Returns empty dict on parse failure."""
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: multi_session.py <hook-name>", file=sys.stderr)
        return 1

    hook = argv[1]
    handler = HOOK_HANDLERS.get(hook)
    if handler is None:
        print(f"unknown hook: {hook}", file=sys.stderr)
        return 1

    payload = read_payload()
    try:
        result = handler(payload)
    except Exception as e:  # never block agent on hook failure
        print(f"[multi_session] hook '{hook}' failed: {e}", file=sys.stderr)
        return 0

    if result:
        json.dump(result, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
