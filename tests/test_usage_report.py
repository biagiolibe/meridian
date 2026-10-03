"""Regression tests for private local session-usage reporting."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import meridian  # noqa: E402


class UsageReportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.home = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_jsonl(self, path: Path, rows: list[object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(json.dumps(row) if isinstance(row, dict) else str(row) for row in rows) + "\n", encoding="utf-8")

    def test_reports_codex_counters_without_message_content(self) -> None:
        path = self.home / ".codex/sessions/2026/10/03/rollout-sample.jsonl"
        self.write_jsonl(path, [
            {"timestamp": "2026-10-03T10:00:00Z", "type": "session_meta", "payload": {"timestamp": "2026-10-03T10:00:00Z", "cwd": "/private/projects/meridian", "model": "gpt-test", "instructions": "PRIVATE CODEX MESSAGE"}},
            {"type": "event_msg", "payload": {"type": "token_count", "info": {"last_token_usage": {"input_tokens": 18000, "cached_input_tokens": 0, "output_tokens": 20}}}},
            {"type": "event_msg", "payload": {"type": "token_count", "info": {"last_token_usage": {"input_tokens": 65000, "cached_input_tokens": 62000, "output_tokens": 30}}}},
            "{truncated",
        ])
        report = meridian.usage_report("codex", Path("/any/meridian"), "2026-10-03", True, self.home)
        self.assertEqual(report["status"], "ok")
        session = report["sessions"][0]
        self.assertEqual(session["project"], "meridian")
        self.assertEqual(session["calls"], 2)
        self.assertEqual(session["first_call_input"], 18000)
        self.assertEqual(session["cumulative_input"], 83000)
        self.assertEqual(session["cached_input"], 62000)
        self.assertEqual(session["breakdown"]["largest_input_growth"], {"call": 2, "tokens": 47000})
        rendered = meridian.format_usage_report(report)
        self.assertNotIn("PRIVATE CODEX MESSAGE", rendered)
        self.assertNotIn("/private/projects", rendered)

    def test_reports_claude_counters_and_sorts_sessions(self) -> None:
        project = self.home / ".claude/projects/-Users-example-meridian"
        self.write_jsonl(project / "later.jsonl", [
            {"type": "assistant", "timestamp": "2026-10-03T11:00:00Z", "cwd": "/Users/example/meridian", "message": {"model": "claude-test", "text": "PRIVATE CLAUDE MESSAGE", "usage": {"input_tokens": 38000, "cache_read_input_tokens": 0, "output_tokens": 10}}},
        ])
        self.write_jsonl(project / "earlier.jsonl", [
            {"type": "assistant", "timestamp": "2026-10-03T09:00:00Z", "cwd": "/Users/example/meridian", "message": {"usage": {"input_tokens": 65000, "cache_read_input_tokens": 64000, "output_tokens": 12}}},
        ])
        report = meridian.usage_report("claude", Path("/work/meridian"), None, False, self.home)
        self.assertEqual([session["start"] for session in report["sessions"]], ["2026-10-03T09:00:00Z", "2026-10-03T11:00:00Z"])
        self.assertEqual(report["sessions"][0]["cached_input"], 64000)
        self.assertNotIn("PRIVATE CLAUDE MESSAGE", meridian.format_usage_report(report))

    def test_unknown_or_missing_format_is_explicitly_unsupported(self) -> None:
        path = self.home / ".codex/sessions/2026/10/03/rollout-unknown.jsonl"
        self.write_jsonl(path, [{"type": "event_msg", "payload": {"text": "PRIVATE UNKNOWN MESSAGE"}}])
        report = meridian.usage_report("codex", None, None, False, self.home)
        self.assertEqual(report["status"], "unsupported")
        self.assertEqual(report["adapters"][0]["status"], "unsupported")
        rendered = meridian.format_usage_report(report)
        self.assertIn("unsupported", rendered)
        self.assertNotIn("PRIVATE UNKNOWN MESSAGE", rendered)

    def test_since_rejects_invalid_dates(self) -> None:
        with self.assertRaisesRegex(meridian.MeridianError, "ISO date"):
            meridian.usage_report("codex", None, "not-a-date", False, self.home)
