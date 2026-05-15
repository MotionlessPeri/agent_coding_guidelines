"""Scenario C — Crashed session's lease is auto-recovered.

Models design doc Appendix scenario C. Verifies that when a session goes
stale (VSCode crash, network drop, etc.), the next SessionStart auto-releases
its lease and archives the entry — letting the new session claim the path
without manual intervention.

Run from skill root:
    python tests/scenario_c_crash_recovery.py
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))
import multi_session as ms

PROJECT = "/tmp/fake_project_C"


def _force_stale(cwd: str, session_id: str, minutes_back: int = 120) -> None:
    """Helper to simulate a session that hasn't heartbeated in N minutes."""
    past = datetime.now(timezone.utc) - timedelta(minutes=minutes_back)
    ts = past.strftime("%Y-%m-%dT%H:%M:%SZ")
    reg = ms.load_registry(cwd)
    for s in reg["active_sessions"]:
        if s["session_id"] == session_id:
            s["last_heartbeat"] = ts
    ms.save_registry(cwd, reg)
    sess = ms.load_session(cwd, session_id)
    if sess:
        sess["last_heartbeat"] = ts
        ms.save_session(cwd, sess)


class ScenarioCCrashRecovery(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["MULTI_SESSION_BASE"] = self.tmp.name

    def tearDown(self):
        os.environ.pop("MULTI_SESSION_BASE", None)
        self.tmp.cleanup()

    def test_scenario_c(self):
        # ---- T0: A starts, claims AGENTS.md, begins editing ----
        ms.hook_session_start({"cwd": PROJECT, "session_id": "sess-A"})
        ms.register_session(PROJECT, "sess-A", status="active")
        ms.add_lease(PROJECT, "sess-A", "AGENTS.md")
        ms.hook_post_tool_edit({
            "cwd": PROJECT,
            "session_id": "sess-A",
            "tool_input": {"file_path": "AGENTS.md"},
        })

        # ---- T1: A's VSCode crashes — no heartbeats for 2 hours ----
        # (Stop hook never fires because the process died.)
        _force_stale(PROJECT, "sess-A", minutes_back=120)

        # Sanity: at this point find_lease_holder ignores the stale lease
        # (per our stale filtering in active_sessions).
        self.assertIsNone(ms.find_lease_holder(PROJECT, "AGENTS.md"))

        # ---- T2: User opens new tab — session C starts ----
        out_c = ms.hook_session_start({"cwd": PROJECT, "session_id": "sess-C"})
        ctx = out_c["hookSpecificOutput"]["additionalContext"]

        # SessionStart cleanup should have:
        # (a) Released A's lease (set to []) and marked A=ended
        # (b) Since C is the only fresh session, archived A
        # (c) Context message mentions archive / cleanup
        self.assertIn("Archived", ctx)
        self.assertIn("No other active", ctx)

        # ---- T3: Verify state files ----
        # A should NO LONGER be in active_sessions list
        reg = ms.load_registry(PROJECT)
        ids = [s["session_id"] for s in reg["active_sessions"]]
        self.assertNotIn("sess-A", ids)
        self.assertIn("sess-C", ids)

        # A's session file should be archived
        archive_root = ms.project_root(PROJECT) / "archive"
        archived = list(archive_root.rglob("sess-A.json"))
        self.assertEqual(len(archived), 1, f"expected exactly one archived A file, got {archived}")
        # Archive still contains touched_files for post-mortem
        import json
        with archived[0].open("r", encoding="utf-8") as f:
            archived_data = json.load(f)
        self.assertIn("AGENTS.md", archived_data["touched_files"])
        self.assertEqual(archived_data["status"], "ended")

        # ---- T4: C can claim AGENTS.md freely ----
        ms.register_session(PROJECT, "sess-C", status="active")
        ms.add_lease(PROJECT, "sess-C", "AGENTS.md")
        pre = ms.hook_pre_tool_edit({
            "cwd": PROJECT,
            "session_id": "sess-C",
            "tool_input": {"file_path": "AGENTS.md"},
        })
        self.assertIsNone(pre)  # C's own lease, allowed

        holder = ms.find_lease_holder(PROJECT, "AGENTS.md")
        self.assertEqual(holder["session_id"], "sess-C")


if __name__ == "__main__":
    unittest.main()
