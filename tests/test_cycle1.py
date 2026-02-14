"""
Cycle 1 — Code Quality Rules
Python equivalent of test-cycle1.mjs
Run: python3 -m unittest tests/test_cycle1.py -v
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "python"))
from quadruple_verification import _run_cycle1


class TestNoTodo(unittest.TestCase):
    def test_blocks_todo_comments(self):
        v = _run_cycle1("// TODO: fix this later", ".js", "file-write", set())
        self.assertTrue(len(v) > 0)
        self.assertEqual(v[0]["rule_id"], "no-todo")

    def test_blocks_fixme_comments(self):
        v = _run_cycle1("# FIXME: broken logic", ".py", "file-write", set())
        self.assertTrue(len(v) > 0)
        self.assertEqual(v[0]["rule_id"], "no-todo")

    def test_blocks_hack_comments(self):
        v = _run_cycle1("// HACK: temporary workaround", ".js", "file-write", set())
        self.assertTrue(len(v) > 0)

    def test_blocks_xxx_comments(self):
        v = _run_cycle1("# XXX: needs review", ".py", "file-write", set())
        self.assertTrue(len(v) > 0)

    def test_does_not_block_normal_code(self):
        v = _run_cycle1("const total = items.reduce((a, b) => a + b, 0);", ".js", "file-write", set())
        todo_v = [x for x in v if x["rule_id"] == "no-todo"]
        self.assertEqual(len(todo_v), 0)


class TestNoEmptyPass(unittest.TestCase):
    def test_blocks_bare_pass_in_python(self):
        v = _run_cycle1("def foo():\n    pass\n", ".py", "file-write", set())
        self.assertTrue(any(x["rule_id"] == "no-empty-pass" for x in v))

    def test_not_triggered_for_js_files(self):
        v = _run_cycle1("pass\n", ".js", "file-write", set())
        self.assertFalse(any(x["rule_id"] == "no-empty-pass" for x in v))


class TestNoNotImplemented(unittest.TestCase):
    def test_blocks_not_implemented_error(self):
        v = _run_cycle1('raise NotImplementedError("coming soon")', ".py", "file-write", set())
        self.assertTrue(any(x["rule_id"] == "no-not-implemented" for x in v))


class TestNoEllipsis(unittest.TestCase):
    def test_blocks_ellipsis_placeholder(self):
        v = _run_cycle1("def foo():\n    ...\n", ".py", "file-write", set())
        self.assertTrue(any(x["rule_id"] == "no-ellipsis" for x in v))

    def test_not_triggered_for_non_python_files(self):
        v = _run_cycle1("...\n", ".js", "file-write", set())
        self.assertFalse(any(x["rule_id"] == "no-ellipsis" for x in v))


class TestNoPlaceholderText(unittest.TestCase):
    def test_blocks_placeholder_text(self):
        v = _run_cycle1("// This is a placeholder implementation", ".js", "file-write", set())
        self.assertTrue(any(x["rule_id"] == "no-placeholder-text" for x in v))

    def test_blocks_stub_text(self):
        v = _run_cycle1("# stub function", ".py", "file-write", set())
        self.assertTrue(any(x["rule_id"] == "no-placeholder-text" for x in v))

    def test_blocks_implement_this_text(self):
        v = _run_cycle1("// implement this later", ".js", "file-write", set())
        self.assertTrue(any(x["rule_id"] == "no-placeholder-text" for x in v))


class TestNoThrowNotImpl(unittest.TestCase):
    def test_blocks_throw_not_implemented_in_js(self):
        v = _run_cycle1('throw new Error("not implemented yet")', ".js", "file-write", set())
        self.assertTrue(any(x["rule_id"] == "no-throw-not-impl" for x in v))

    def test_blocks_throw_not_implemented_in_ts(self):
        v = _run_cycle1("throw new Error(`not implemented`)", ".ts", "file-write", set())
        self.assertTrue(any(x["rule_id"] == "no-throw-not-impl" for x in v))

    def test_not_triggered_for_python_files(self):
        v = _run_cycle1('throw new Error("not implemented")', ".py", "file-write", set())
        self.assertFalse(any(x["rule_id"] == "no-throw-not-impl" for x in v))


class TestContextFiltering(unittest.TestCase):
    def test_does_not_run_file_write_rules_in_bash_context(self):
        v = _run_cycle1("TODO: fix this", ".sh", "bash", set())
        self.assertEqual(len(v), 0)


class TestDisabledRules(unittest.TestCase):
    def test_should_skip_disabled_rules(self):
        v = _run_cycle1("// TODO: fix", ".js", "file-write", {"no-todo"})
        self.assertFalse(any(x["rule_id"] == "no-todo" for x in v))


class TestCleanCodePasses(unittest.TestCase):
    def test_should_approve_clean_typescript_code(self):
        clean_code = """
interface User {
  id: string;
  name: string;
}

function validateEmail(email: string): boolean {
  const pattern = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
  return pattern.test(email);
}
"""
        v = _run_cycle1(clean_code, ".ts", "file-write", set())
        self.assertEqual(len(v), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
