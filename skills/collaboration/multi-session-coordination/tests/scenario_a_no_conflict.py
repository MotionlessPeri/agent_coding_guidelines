"""Scenario A — Two sessions, non-overlapping work.

Models design doc Appendix scenario A. Verifies that two sessions can work
concurrently on different paths, see each other in the registry, commit
independently, and end cleanly.

Run from skill root:
    python tests/scenario_a_no_conflict.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))
import multi_session as ms

PROJECT = "/tmp/fake_project_A"


class ScenarioANoConflict(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["MULTI_SESSION_BASE"] = self.tmp.name

    def tearDown(self):
        os.environ.pop("MULTI_SESSION_BASE", None)
        self.tmp.cleanup()

    def test_scenario_a(self):
        # ---- T0: A starts ----
        out_a = ms.hook_session_start({"cwd": PROJECT, "session_id": "sess-A"})
        ctx_a = out_a["hookSpecificOutput"]["additionalContext"]
        self.assertIn("No other active", ctx_a)

        # ---- T1: A transitions discussion → active, claims AGENTS.md ----
        ms.register_session(PROJECT, "sess-A", status="active")
        ms.add_lease(PROJECT, "sess-A", "AGENTS.md")

        # ---- T2: A makes an edit (simulated PostToolUse) ----
        ms.hook_post_tool_edit({
            "cwd": PROJECT,
            "session_id": "sess-A",
            "tool_input": {"file_path": "AGENTS.md"},
        })
        s = ms.load_session(PROJECT, "sess-A")
        self.assertIn("AGENTS.md", s["touched_files"])

        # ---- T3: B starts ----
        out_b = ms.hook_session_start({"cwd": PROJECT, "session_id": "sess-B"})
        ctx_b = out_b["hookSpecificOutput"]["additionalContext"]
        self.assertIn("sess-A"[:8], ctx_b)
        self.assertIn("AGENTS.md", ctx_b)

        # ---- T4: B claims a non-overlapping path ----
        ms.register_session(PROJECT, "sess-B", status="active")
        ms.add_lease(PROJECT, "sess-B", "guidelines/ue/foo.md")

        # ---- T5: PreToolUse from B on guidelines/ue/foo.md should pass ----
        pre = ms.hook_pre_tool_edit({
            "cwd": PROJECT,
            "session_id": "sess-B",
            "tool_input": {"file_path": "guidelines/ue/foo.md"},
        })
        self.assertIsNone(pre)  # no conflict

        # ---- T6: PreToolUse from B on AGENTS.md should be DENIED ----
        pre = ms.hook_pre_tool_edit({
            "cwd": PROJECT,
            "session_id": "sess-B",
            "tool_input": {"file_path": "AGENTS.md"},
        })
        self.assertIsNotNone(pre)
        self.assertEqual(pre["hookSpecificOutput"]["permissionDecision"], "deny")

        # ---- T7: B touches its own file (legal) ----
        ms.hook_post_tool_edit({
            "cwd": PROJECT,
            "session_id": "sess-B",
            "tool_input": {"file_path": "guidelines/ue/foo.md"},
        })

        # ---- T8: A stops (commit + release would have happened agent-side) ----
        ms.remove_lease(PROJECT, "sess-A", "AGENTS.md")
        ms.hook_stop({"cwd": PROJECT, "session_id": "sess-A"})
        sa = ms.load_session(PROJECT, "sess-A")
        self.assertEqual(sa["status"], "ended")

        # ---- T9: B can now claim AGENTS.md if it wants ----
        self.assertIsNone(ms.find_lease_holder(PROJECT, "AGENTS.md"))

        # ---- T10: B stops ----
        ms.hook_stop({"cwd": PROJECT, "session_id": "sess-B"})

        # ---- T11: New session C starts (solo) → archive of ended sessions ----
        out_c = ms.hook_session_start({"cwd": PROJECT, "session_id": "sess-C"})
        ctx_c = out_c["hookSpecificOutput"]["additionalContext"]
        # Should announce no other active + cleanup info
        self.assertIn("No other active", ctx_c)

        archive_root = ms.project_root(PROJECT) / "archive"
        self.assertTrue(archive_root.is_dir())
        archived_a = list(archive_root.rglob("sess-A.json"))
        archived_b = list(archive_root.rglob("sess-B.json"))
        # On a solo SessionStart the cleanup pass archives ended sessions
        self.assertEqual(len(archived_a), 1)
        self.assertEqual(len(archived_b), 1)


if __name__ == "__main__":
    unittest.main()
