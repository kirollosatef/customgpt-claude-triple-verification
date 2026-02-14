"""
Config Loader
Python equivalent of test-config.mjs
Run: python3 -m unittest tests/test_config.py -v
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "python"))
from quadruple_verification import _deep_merge, _load_json_file


class TestDeepMerge(unittest.TestCase):
    def test_should_merge_flat_objects(self):
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = _deep_merge(base, override)
        self.assertEqual(result, {"a": 1, "b": 3, "c": 4})

    def test_should_deep_merge_nested_objects(self):
        base = {"a": {"x": 1, "y": 2}, "b": 3}
        override = {"a": {"y": 5, "z": 6}}
        result = _deep_merge(base, override)
        self.assertEqual(result, {"a": {"x": 1, "y": 5, "z": 6}, "b": 3})

    def test_should_replace_arrays_not_concatenate(self):
        base = {"rules": ["a", "b", "c"]}
        override = {"rules": ["x", "y"]}
        result = _deep_merge(base, override)
        self.assertEqual(result, {"rules": ["x", "y"]})

    def test_should_handle_null_override(self):
        base = {"a": 1}
        result = _deep_merge(base, None)
        self.assertEqual(result, {"a": 1})

    def test_should_handle_null_base(self):
        override = {"a": 1}
        result = _deep_merge(None, override)
        self.assertEqual(result, {"a": 1})

    def test_should_not_mutate_original_objects(self):
        base = {"a": {"x": 1}}
        override = {"a": {"y": 2}}
        _deep_merge(base, override)
        self.assertEqual(base, {"a": {"x": 1}})


class TestLoadJSONFile(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="config-test-"))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_should_load_valid_json_file(self):
        file_path = self.temp_dir / "test.json"
        file_path.write_text(json.dumps({"key": "value"}), encoding="utf-8")
        result = _load_json_file(file_path)
        self.assertEqual(result, {"key": "value"})

    def test_should_return_empty_object_for_non_existent_file(self):
        result = _load_json_file(self.temp_dir / "missing.json")
        self.assertEqual(result, {})

    def test_should_return_empty_object_for_invalid_json(self):
        file_path = self.temp_dir / "invalid.json"
        file_path.write_text("not valid json{{{", encoding="utf-8")
        result = _load_json_file(file_path)
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
