"""
Audit Logger
Python equivalent of test-audit.mjs
Run: python3 -m unittest tests/test_audit.py -v
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "python"))
from quadruple_verification import _log_entry, _log_pre_tool, _log_post_tool, _log_stop


class TestAuditLogger(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="quadruple-verify-test-"))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _config(self):
        return {"audit": {"enabled": True, "logDir": str(self.temp_dir)}}

    def test_should_create_log_file_and_write_jsonl_entry(self):
        _log_entry(
            "pre-tool", "Write", "approve", [],
            {"filePath": "/test.js"}, self._config()
        )

        files = list(self.temp_dir.iterdir())
        self.assertGreater(len(files), 0, "Should create at least one log file")

        lines = files[0].read_text(encoding="utf-8").strip().split("\n")
        self.assertEqual(len(lines), 1)

        entry = json.loads(lines[0])
        self.assertEqual(entry["event"], "pre-tool")
        self.assertEqual(entry["tool"], "Write")
        self.assertEqual(entry["decision"], "approve")
        self.assertIn("timestamp", entry)
        self.assertIn("sessionId", entry)

    def test_should_append_multiple_entries_to_same_session_file(self):
        cfg = self._config()
        _log_pre_tool("Write", "approve", [], {"filePath": "/a.js"}, cfg)
        _log_pre_tool("Edit", "block", [{"rule_id": "no-todo", "message": "blocked"}], {}, cfg)
        _log_post_tool("Bash", {"command": "npm test"}, cfg)

        files = list(self.temp_dir.iterdir())
        lines = files[0].read_text(encoding="utf-8").strip().split("\n")
        self.assertEqual(len(lines), 3)

    def test_should_include_violations_in_log_entry(self):
        violations = [
            {"rule_id": "no-eval", "cycle": 2, "message": "eval is bad"},
            {"rule_id": "no-todo", "cycle": 1, "message": "no TODOs"},
        ]
        _log_pre_tool("Write", "block", violations, {}, self._config())

        files = list(self.temp_dir.iterdir())
        entry = json.loads(files[0].read_text(encoding="utf-8").strip())
        self.assertEqual(len(entry["violations"]), 2)
        self.assertEqual(entry["violations"][0]["rule_id"], "no-eval")

    def test_should_not_throw_on_log_failure(self):
        bad_config = {"audit": {"enabled": True, "logDir": "/nonexistent/impossible/path/that/will/fail"}}
        # Should not raise — audit logging must never block
        try:
            _log_entry("test", "test", "approve", [], {}, bad_config)
        except Exception as e:
            self.fail(f"Audit logger raised unexpectedly: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
