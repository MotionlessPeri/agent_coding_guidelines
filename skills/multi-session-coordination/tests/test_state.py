"""Unit tests for multi_session.py state library + SessionStart hook.

Tests set $MULTI_SESSION_BASE to a temp dir so they never touch the real
~/.claude/multi-session-coord/.

Run from skill root:
    python -m unittest tests.test_state -v
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Make the skill root importable.
SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

import multi_session as ms  # noqa: E402


CWD_SAMPLE = "e:\\xd_projects\\test_project"


class TempBaseTestCase(unittest.TestCase):
    """Test base class that isolates state into a temp dir via env var."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.base = Path(self.tmpdir.name)
        self._old_env = os.environ.get("MULTI_SESSION_BASE")
        os.environ["MULTI_SESSION_BASE"] = str(self.base)

    def tearDown(self) -> None:
        if self._old_env is None:
            os.environ.pop("MULTI_SESSION_BASE", None)
        else:
            os.environ["MULTI_SESSION_BASE"] = self._old_env
        self.tmpdir.cleanup()


# ---------------------------------------------------------------------------
# Path encoding
# ---------------------------------------------------------------------------

class TestEncodeCwd(unittest.TestCase):
    def test_windows_path(self):
        self.assertEqual(
            ms.encode_cwd("e:\\xd_projects\\agent_coding_guidelines"),
            "e--xd-projects-agent-coding-guidelines",
        )

    def test_unix_path(self):
        self.assertEqual(
            ms.encode_cwd("/home/user/my_project"),
            "-home-user-my-project",
        )

    def test_mixed_separators(self):
        # The encoder replaces both : \ / _, so 'e:/foo_bar' -> 'e--foo-bar'
        self.assertEqual(ms.encode_cwd("e:/foo_bar"), "e--foo-bar")


# ---------------------------------------------------------------------------
# Atomic JSON IO
# ---------------------------------------------------------------------------

class TestAtomicJSON(TempBaseTestCase):
    def test_read_missing_returns_none(self):
        self.assertIsNone(ms.read_json(self.base / "nonexistent.json"))

    def test_read_corrupt_returns_none(self):
        p = self.base / "corrupt.json"
        p.write_text("{not valid json")
        self.assertIsNone(ms.read_json(p))

    def test_roundtrip(self):
        p = self.base / "rt.json"
        data = {"a": 1, "b": [1, 2, 3], "c": {"nested": "value"}}
        ms.write_json(p, data)
        self.assertEqual(ms.read_json(p), data)

    def test_atomic_write_leaves_no_temp_files(self):
        target = self.base / "atomic.json"
        ms.write_json(target, {"x": 1})
        tmp_files = list(self.base.glob(f".{target.name}.*.tmp"))
        self.assertEqual(tmp_files, [], f"unexpected temp files: {tmp_files}")

    def test_write_unicode(self):
        p = self.base / "uni.json"
        data = {"intent": "处理 AGENTS.md 更新", "scope": "中文 path"}
        ms.write_json(p, data)
        self.assertEqual(ms.read_json(p), data)


# ---------------------------------------------------------------------------
# Session registration / heartbeat
# ---------------------------------------------------------------------------

class TestRegistration(TempBaseTestCase):
    def test_register_creates_registry_and_session(self):
        ms.register_session(CWD_SAMPLE, "sess-A")
        reg = ms.load_registry(CWD_SAMPLE)
        self.assertEqual(len(reg["active_sessions"]), 1)
        self.assertEqual(reg["active_sessions"][0]["session_id"], "sess-A")
        s = ms.load_session(CWD_SAMPLE, "sess-A")
        self.assertIsNotNone(s)
        self.assertEqual(s["session_id"], "sess-A")

    def test_register_existing_refreshes(self):
        ms.register_session(CWD_SAMPLE, "sess-A")
        first_hb = ms.load_registry(CWD_SAMPLE)["active_sessions"][0]["last_heartbeat"]
        # Re-register
        ms.register_session(CWD_SAMPLE, "sess-A", status="active")
        reg = ms.load_registry(CWD_SAMPLE)
        self.assertEqual(len(reg["active_sessions"]), 1)
        self.assertEqual(reg["active_sessions"][0]["status"], "active")

    def test_update_heartbeat_changes_both_registry_and_session(self):
        ms.register_session(CWD_SAMPLE, "sess-A")
        # Manually back-date heartbeat to verify update overwrites
        reg = ms.load_registry(CWD_SAMPLE)
        old_ts = "2020-01-01T00:00:00Z"
        reg["active_sessions"][0]["last_heartbeat"] = old_ts
        ms.save_registry(CWD_SAMPLE, reg)

        ms.update_heartbeat(CWD_SAMPLE, "sess-A")
        new_ts = ms.load_registry(CWD_SAMPLE)["active_sessions"][0]["last_heartbeat"]
        self.assertNotEqual(new_ts, old_ts)


# ---------------------------------------------------------------------------
# active_sessions filtering
# ---------------------------------------------------------------------------

class TestActiveSessions(TempBaseTestCase):
    def _backdate(self, session_id: str, minutes_ago: int) -> None:
        ts = (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        reg = ms.load_registry(CWD_SAMPLE)
        for s in reg["active_sessions"]:
            if s["session_id"] == session_id:
                s["last_heartbeat"] = ts
        ms.save_registry(CWD_SAMPLE, reg)

    def test_excludes_self(self):
        ms.register_session(CWD_SAMPLE, "sess-A")
        ms.register_session(CWD_SAMPLE, "sess-B")
        others = ms.active_sessions(CWD_SAMPLE, exclude="sess-A")
        ids = [s["session_id"] for s in others]
        self.assertEqual(ids, ["sess-B"])

    def test_excludes_stale(self):
        ms.register_session(CWD_SAMPLE, "sess-A")
        ms.register_session(CWD_SAMPLE, "sess-stale")
        self._backdate("sess-stale", 120)
        active = ms.active_sessions(CWD_SAMPLE)
        ids = [s["session_id"] for s in active]
        self.assertEqual(ids, ["sess-A"])

    def test_excludes_ended(self):
        ms.register_session(CWD_SAMPLE, "sess-A")
        ms.register_session(CWD_SAMPLE, "sess-ended")
        reg = ms.load_registry(CWD_SAMPLE)
        for s in reg["active_sessions"]:
            if s["session_id"] == "sess-ended":
                s["status"] = "ended"
        ms.save_registry(CWD_SAMPLE, reg)
        active = ms.active_sessions(CWD_SAMPLE)
        ids = [s["session_id"] for s in active]
        self.assertEqual(ids, ["sess-A"])


# ---------------------------------------------------------------------------
# Lease primitives
# ---------------------------------------------------------------------------

class TestLeases(TempBaseTestCase):
    def test_add_remove_lease(self):
        ms.register_session(CWD_SAMPLE, "sess-A")
        ms.add_lease(CWD_SAMPLE, "sess-A", "AGENTS.md")
        reg = ms.load_registry(CWD_SAMPLE)
        self.assertIn("AGENTS.md", reg["active_sessions"][0]["lease_paths"])
        ms.remove_lease(CWD_SAMPLE, "sess-A", "AGENTS.md")
        reg = ms.load_registry(CWD_SAMPLE)
        self.assertNotIn("AGENTS.md", reg["active_sessions"][0]["lease_paths"])

    def test_add_lease_dedup(self):
        ms.register_session(CWD_SAMPLE, "sess-A")
        ms.add_lease(CWD_SAMPLE, "sess-A", "AGENTS.md")
        ms.add_lease(CWD_SAMPLE, "sess-A", "AGENTS.md")
        reg = ms.load_registry(CWD_SAMPLE)
        self.assertEqual(
            reg["active_sessions"][0]["lease_paths"].count("AGENTS.md"), 1
        )

    def test_find_lease_holder_exact(self):
        ms.register_session(CWD_SAMPLE, "sess-A")
        ms.add_lease(CWD_SAMPLE, "sess-A", "AGENTS.md")
        holder = ms.find_lease_holder(CWD_SAMPLE, "AGENTS.md")
        self.assertIsNotNone(holder)
        self.assertEqual(holder["session_id"], "sess-A")

    def test_find_lease_holder_dir_prefix(self):
        ms.register_session(CWD_SAMPLE, "sess-A")
        ms.add_lease(CWD_SAMPLE, "sess-A", "skills/daily-tracking/")
        holder = ms.find_lease_holder(CWD_SAMPLE, "skills/daily-tracking/SKILL.md")
        self.assertIsNotNone(holder)
        self.assertEqual(holder["session_id"], "sess-A")

    def test_find_lease_holder_no_match(self):
        ms.register_session(CWD_SAMPLE, "sess-A")
        ms.add_lease(CWD_SAMPLE, "sess-A", "AGENTS.md")
        holder = ms.find_lease_holder(CWD_SAMPLE, "guidelines/other.md")
        self.assertIsNone(holder)

    def test_find_lease_holder_ignores_stale(self):
        ms.register_session(CWD_SAMPLE, "sess-stale")
        ms.add_lease(CWD_SAMPLE, "sess-stale", "AGENTS.md")
        # Backdate
        reg = ms.load_registry(CWD_SAMPLE)
        reg["active_sessions"][0]["last_heartbeat"] = "2020-01-01T00:00:00Z"
        ms.save_registry(CWD_SAMPLE, reg)
        holder = ms.find_lease_holder(CWD_SAMPLE, "AGENTS.md")
        self.assertIsNone(holder)


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

class TestCleanup(TempBaseTestCase):
    def _backdate(self, session_id: str, minutes_ago: int) -> None:
        ts = (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        reg = ms.load_registry(CWD_SAMPLE)
        for s in reg["active_sessions"]:
            if s["session_id"] == session_id:
                s["last_heartbeat"] = ts
        ms.save_registry(CWD_SAMPLE, reg)

    def test_cleanup_releases_stale_leases(self):
        ms.register_session(CWD_SAMPLE, "sess-stale")
        ms.add_lease(CWD_SAMPLE, "sess-stale", "AGENTS.md")
        self._backdate("sess-stale", 120)

        report = ms.invoke_cleanup(CWD_SAMPLE, self_session_id="sess-new")
        self.assertEqual(len(report["released_leases"]), 1)
        self.assertEqual(report["released_leases"][0]["path"], "AGENTS.md")
        self.assertIn("sess-stale", report["ended"])

    def test_cleanup_archives_when_solo(self):
        ms.register_session(CWD_SAMPLE, "sess-stale")
        self._backdate("sess-stale", 120)

        # self_session_id is "sess-new" — not in registry yet, so only stale exists
        report = ms.invoke_cleanup(CWD_SAMPLE, self_session_id="sess-new")
        # Solo (no fresh others) -> should archive
        self.assertIn("sess-stale", report["archived"])
        # Registry should now be empty of stale entry
        reg = ms.load_registry(CWD_SAMPLE)
        self.assertEqual(reg["active_sessions"], [])
        # Archive dir should contain the file
        adir = ms.archive_dir(CWD_SAMPLE)
        archived = list(adir.glob("sess-stale.json"))
        self.assertEqual(len(archived), 1)

    def test_cleanup_no_archive_when_others_active(self):
        ms.register_session(CWD_SAMPLE, "sess-stale")
        ms.register_session(CWD_SAMPLE, "sess-fresh")
        self._backdate("sess-stale", 120)

        report = ms.invoke_cleanup(CWD_SAMPLE, self_session_id="sess-new")
        self.assertIn("sess-stale", report["ended"])
        # Not solo (sess-fresh exists) -> should NOT archive
        self.assertEqual(report["archived"], [])
        # Stale entry still in registry (marked ended)
        reg = ms.load_registry(CWD_SAMPLE)
        ids = [s["session_id"] for s in reg["active_sessions"]]
        self.assertIn("sess-stale", ids)

    def test_cleanup_fresh_session_untouched(self):
        ms.register_session(CWD_SAMPLE, "sess-A")
        ms.add_lease(CWD_SAMPLE, "sess-A", "AGENTS.md")

        report = ms.invoke_cleanup(CWD_SAMPLE, self_session_id="sess-A")
        self.assertEqual(report["released_leases"], [])
        self.assertEqual(report["ended"], [])
        # Lease still held
        reg = ms.load_registry(CWD_SAMPLE)
        self.assertIn("AGENTS.md", reg["active_sessions"][0]["lease_paths"])


# ---------------------------------------------------------------------------
# Hook: SessionStart
# ---------------------------------------------------------------------------

class TestHookSessionStart(TempBaseTestCase):
    def test_solo_session_message(self):
        result = ms.hook_session_start({
            "cwd": CWD_SAMPLE,
            "session_id": "sess-A",
        })
        self.assertIn("hookSpecificOutput", result)
        self.assertEqual(result["hookSpecificOutput"]["hookEventName"], "SessionStart")
        self.assertIn("No other active", result["hookSpecificOutput"]["additionalContext"])

    def test_lists_other_active_sessions(self):
        # Pre-register a session
        ms.register_session(CWD_SAMPLE, "sess-other", status="active")
        ms.add_lease(CWD_SAMPLE, "sess-other", "AGENTS.md")
        # Set intent
        s = ms.load_session(CWD_SAMPLE, "sess-other")
        s["intent_summary"] = "add daily-tracking guideline"
        ms.save_session(CWD_SAMPLE, s)

        result = ms.hook_session_start({
            "cwd": CWD_SAMPLE,
            "session_id": "sess-A",
        })
        ctx = result["hookSpecificOutput"]["additionalContext"]
        self.assertIn("sess-oth", ctx)  # session_id[:8]
        self.assertIn("AGENTS.md", ctx)
        self.assertIn("add daily-tracking guideline", ctx)

    def test_registers_self_in_registry(self):
        ms.hook_session_start({
            "cwd": CWD_SAMPLE,
            "session_id": "sess-A",
        })
        reg = ms.load_registry(CWD_SAMPLE)
        ids = [s["session_id"] for s in reg["active_sessions"]]
        self.assertIn("sess-A", ids)

    def test_cleanup_message_when_archived(self):
        ms.register_session(CWD_SAMPLE, "sess-stale")
        reg = ms.load_registry(CWD_SAMPLE)
        for s in reg["active_sessions"]:
            if s["session_id"] == "sess-stale":
                s["last_heartbeat"] = "2020-01-01T00:00:00Z"
        ms.save_registry(CWD_SAMPLE, reg)

        result = ms.hook_session_start({
            "cwd": CWD_SAMPLE,
            "session_id": "sess-new",
        })
        ctx = result["hookSpecificOutput"]["additionalContext"]
        self.assertIn("[cleanup]", ctx)


# ---------------------------------------------------------------------------
# Dispatcher / CLI smoke
# ---------------------------------------------------------------------------

class TestDispatcher(TempBaseTestCase):
    def test_unknown_hook_returns_error(self):
        rc = ms.main(["multi_session.py", "nonexistent-hook"])
        # Returns 1 for unknown hook
        self.assertEqual(rc, 1)

    def test_hook_with_invalid_stdin_does_not_crash(self):
        # We can't easily inject stdin in a unit test of main(); just verify
        # read_payload tolerates empty input.
        # Use mock stdin via patching:
        import io
        orig = sys.stdin
        sys.stdin = io.StringIO("")
        try:
            payload = ms.read_payload()
            self.assertEqual(payload, {})
        finally:
            sys.stdin = orig


if __name__ == "__main__":
    unittest.main()
