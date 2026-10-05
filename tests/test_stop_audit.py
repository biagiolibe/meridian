"""Tests for the Stop-hook audit of unbacked BLOCKED reports (task 173)."""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import meridian  # noqa: E402
import stop_audit  # noqa: E402

NOW = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)


class StopAuditTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name).resolve()
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.project)], check=True)
        (self.project / "PROJECT_WORKFLOW.md").write_text("workflow\n", encoding="utf-8")
        self.journal = self.project / ".git" / meridian.JOURNAL_NAME

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def seed(self, *lines: dict) -> None:
        self.journal.write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")

    def blocked(self, code: str, task: str | None = None, ts: str = "2026-10-05T11:00:00Z") -> dict:
        return {"version": 1, "ts": ts, "command": "worktree check", "task": task, "result": "blocked", "stop_code": code, "exit": 2}

    def run_audit(self, message: str, **extra: object) -> list[dict]:
        payload = {"cwd": str(self.project), "last_assistant_message": message, **extra}
        return stop_audit.audit(payload, NOW)

    def test_backed_code_is_not_recorded(self) -> None:
        self.seed(self.blocked("WRONG_WORKTREE"))
        self.assertEqual(self.run_audit("BLOCKED WRONG_WORKTREE: mismatch"), [])
        self.assertEqual(len(self.journal.read_text().splitlines()), 1)

    def test_unbacked_tool_code_is_recorded_with_code_only(self) -> None:
        self.seed(self.blocked("PRIMARY_DIRTY"))
        written = self.run_audit("Stopping.\nBLOCKED WRONG_WORKTREE: my own reading of the text")
        self.assertEqual([(line["result"], line["stop_code"]) for line in written], [("unbacked_block", "WRONG_WORKTREE")])
        stored = self.journal.read_text()
        self.assertNotIn("my own reading", stored)
        self.assertEqual(json.loads(stored.splitlines()[-1])["result"], "unbacked_block")

    def test_code_older_than_the_session_window_is_unbacked(self) -> None:
        self.seed(self.blocked("WRONG_WORKTREE", ts="2026-10-01T00:00:00Z"))
        self.assertEqual(self.run_audit("BLOCKED WRONG_WORKTREE")[0]["result"], "unbacked_block")

    def test_active_task_scopes_the_backing_line(self) -> None:
        self.seed(self.blocked("WRONG_WORKTREE", task="172"))
        with mock.patch.object(stop_audit, "active_task", return_value="173"):
            written = self.run_audit("BLOCKED WRONG_WORKTREE")
        self.assertEqual([(line["result"], line["task"]) for line in written], [("unbacked_block", "173")])
        self.seed(self.blocked("WRONG_WORKTREE", task="173"))
        with mock.patch.object(stop_audit, "active_task", return_value="173"):
            self.assertEqual(self.run_audit("BLOCKED WRONG_WORKTREE"), [])

    def test_judgment_code_is_declared(self) -> None:
        self.seed(self.blocked("PRIMARY_DIRTY"))
        written = self.run_audit("BLOCKED ACCEPTANCE_UNMET: criterion 3")
        self.assertEqual([line["result"] for line in written], ["declared_block"])

    def test_no_code_writes_nothing(self) -> None:
        self.seed(self.blocked("PRIMARY_DIRTY"))
        self.assertEqual(self.run_audit("All done. This was not BLOCKED by anything."), [])
        self.assertEqual(len(self.journal.read_text().splitlines()), 1)

    def test_non_meridian_directory_and_missing_journal_do_nothing(self) -> None:
        self.assertEqual(self.run_audit("BLOCKED WRONG_WORKTREE"), [])
        self.assertFalse(self.journal.exists())
        with tempfile.TemporaryDirectory() as other:
            self.assertEqual(stop_audit.audit({"cwd": other, "last_assistant_message": "BLOCKED WRONG_WORKTREE"}, NOW), [])

    def test_malformed_input_exits_zero(self) -> None:
        for raw in ("not json", "[]", '{"cwd": 3}', ""):
            with mock.patch("sys.stdin", io.StringIO(raw)):
                self.assertEqual(stop_audit.main(), 0)

    def test_final_message_falls_back_to_the_transcript(self) -> None:
        transcript = self.project / "t.jsonl"
        entries = [
            {"type": "assistant", "timestamp": "2026-10-05T10:00:00.123Z", "message": {"content": [{"type": "text", "text": "BLOCKED PRIMARY_DIRTY"}]}},
            {"type": "assistant", "timestamp": "2026-10-05T10:05:00.000Z", "message": {"content": [{"type": "tool_use", "name": "Bash"}, {"type": "text", "text": "BLOCKED WRONG_WORKTREE"}]}},
        ]
        transcript.write_text("".join(json.dumps(e) + "\n" for e in entries), encoding="utf-8")
        self.seed(self.blocked("WRONG_WORKTREE", ts="2026-10-05T09:00:00Z"))
        written = stop_audit.audit({"cwd": str(self.project), "transcript_path": str(transcript)}, NOW)
        self.assertEqual([line["stop_code"] for line in written], ["WRONG_WORKTREE"])
        self.assertEqual(written[0]["result"], "unbacked_block")

    def test_flow_report_counts_unbacked_without_inventing_a_task(self) -> None:
        self.seed(self.blocked("PRIMARY_DIRTY"))
        self.run_audit("BLOCKED WRONG_WORKTREE")
        report = meridian.flow_report(self.project, None, NOW)
        self.assertEqual(report["unbacked_blocks"], 1)
        self.assertEqual(report["totals"]["stops"], 1)
        self.assertEqual(report["totals"]["tasks"], 0)


if __name__ == "__main__":
    unittest.main()
