"""Scenario B — Two sessions contend for AGENTS.md; resolve via inbox.

Models design doc Appendix scenario B. Verifies the full negotiation flow:
B sees A's lease, writes release_request to A's inbox, A's next turn sees the
request and releases, B's next turn proceeds.

Run from skill root:
    python tests/scenario_b_lease_conflict.py
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))
import multi_session as ms

PROJECT = "/tmp/fake_project_B"


class ScenarioBLeaseConflict(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["MULTI_SESSION_BASE"] = self.tmp.name

    def tearDown(self):
        os.environ.pop("MULTI_SESSION_BASE", None)
        self.tmp.cleanup()

    def test_scenario_b(self):
        # ---- T0: A starts, claims AGENTS.md ----
        ms.hook_session_start({"cwd": PROJECT, "session_id": "sess-A"})
        ms.register_session(PROJECT, "sess-A", status="active")
        ms.add_lease(PROJECT, "sess-A", "AGENTS.md")
        s = ms.load_session(PROJECT, "sess-A")
        s["intent_summary"] = "add daily-tracking guideline"
        ms.save_session(PROJECT, s)

        # ---- T1: B starts, sees A's lease in SessionStart context ----
        out_b = ms.hook_session_start({"cwd": PROJECT, "session_id": "sess-B"})
        ctx = out_b["hookSpecificOutput"]["additionalContext"]
        self.assertIn("AGENTS.md", ctx)
        self.assertIn("daily-tracking", ctx)

        # ---- T2: B tries to edit AGENTS.md → DENIED ----
        pre = ms.hook_pre_tool_edit({
            "cwd": PROJECT,
            "session_id": "sess-B",
            "tool_input": {"file_path": "AGENTS.md"},
        })
        self.assertIsNotNone(pre)
        self.assertEqual(pre["hookSpecificOutput"]["permissionDecision"], "deny")
        # The reason names the holder (per skill heuristics)
        self.assertIn("sess-A"[:8], pre["hookSpecificOutput"]["permissionDecisionReason"])

        # ---- T3: B writes a release_request to A's inbox (skill policy) ----
        # This is the agent-side step the skill teaches.
        a_session = ms.load_session(PROJECT, "sess-A")
        a_session.setdefault("inbox", []).append({
            "from": "sess-B",
            "ts": ms.now_iso(),
            "type": "release_request",
            "path": "AGENTS.md",
            "reason": "want to add pattern-recognition import line",
            "resolved": False,
        })
        ms.save_session(PROJECT, a_session)

        # ---- T4: A's next turn → UserPromptSubmit surfaces the request ----
        out_a = ms.hook_user_prompt_submit({"cwd": PROJECT, "session_id": "sess-A"})
        self.assertIsNotNone(out_a)
        ctx = out_a["hookSpecificOutput"]["additionalContext"]
        self.assertIn("release_request", ctx)
        self.assertIn("AGENTS.md", ctx)
        self.assertIn("pattern-recognition", ctx)

        # ---- T5: A decides to comply: commits + releases + marks resolved ----
        # (Agent-side, commit step is simulated — we don't actually run git here.)
        ms.remove_lease(PROJECT, "sess-A", "AGENTS.md")
        a_session = ms.load_session(PROJECT, "sess-A")
        for m in a_session.get("inbox", []):
            if m.get("type") == "release_request" and m.get("path") == "AGENTS.md":
                m["resolved"] = True
        # Also writes a release_notice to B
        b_session = ms.load_session(PROJECT, "sess-B")
        b_session.setdefault("inbox", []).append({
            "from": "sess-A",
            "ts": ms.now_iso(),
            "type": "release_notice",
            "path": "AGENTS.md",
            "reason": "released after committing daily-tracking changes",
            "resolved": False,
        })
        ms.save_session(PROJECT, a_session)
        ms.save_session(PROJECT, b_session)

        # ---- T6: A's next UserPromptSubmit no longer surfaces the resolved msg ----
        out_a2 = ms.hook_user_prompt_submit({"cwd": PROJECT, "session_id": "sess-A"})
        # The only inbox msg was resolved; should be None or not include release_request
        if out_a2 is not None:
            self.assertNotIn("release_request", out_a2["hookSpecificOutput"]["additionalContext"])

        # ---- T7: B's next UserPromptSubmit sees the release_notice ----
        out_b = ms.hook_user_prompt_submit({"cwd": PROJECT, "session_id": "sess-B"})
        self.assertIsNotNone(out_b)
        self.assertIn("release_notice", out_b["hookSpecificOutput"]["additionalContext"])

        # ---- T8: B can now claim AGENTS.md and edit ----
        ms.add_lease(PROJECT, "sess-B", "AGENTS.md")
        pre = ms.hook_pre_tool_edit({
            "cwd": PROJECT,
            "session_id": "sess-B",
            "tool_input": {"file_path": "AGENTS.md"},
        })
        self.assertIsNone(pre)  # B's own lease, allowed

        # And the lease holder lookup confirms ownership
        holder = ms.find_lease_holder(PROJECT, "AGENTS.md")
        self.assertEqual(holder["session_id"], "sess-B")


if __name__ == "__main__":
    unittest.main()
