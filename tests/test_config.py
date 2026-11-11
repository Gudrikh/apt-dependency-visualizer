"""Проверки успешной загрузки и ошибок по каждому параметру."""

import json
import tempfile
import unittest
from pathlib import Path

from src.config import load_config


class ConfigTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "config.json"
        (self.path.parent / "repository.json").write_text("{}", "utf-8")
        self.values = {
            "package": "A",
            "repository": "repository.json",
            "test_mode": True,
            "output": "out/graph.svg",
            "ascii_tree": False,
            "max_depth": 3,
            "exclude_substring": "",
        }

    def load(self, **changes):
        self.path.write_text(json.dumps(self.values | changes), "utf-8")
        return load_config(self.path)

    def test_relative_paths(self):
        config = self.load()
        self.assertEqual(Path(config.repository).parent, self.path.parent)
        self.assertEqual(config.output, self.path.parent / "out/graph.svg")

    def test_invalid_parameter_values(self):
        for field, value in (
            ("package", "a"),
            ("repository", "missing.json"),
            ("test_mode", "true"),
            ("output", "graph.png"),
            ("ascii_tree", 1),
            ("max_depth", -1),
            ("max_depth", False),
            ("exclude_substring", ["B"]),
        ):
            with self.subTest(field=field, value=value):
                with self.assertRaisesRegex(ValueError, field):
                    self.load(**{field: value})

    def test_invalid_apt_url(self):
        with self.assertRaisesRegex(ValueError, "repository"):
            self.load(package="hello", test_mode=False, repository="ftp://a")

    def test_missing_and_unknown_keys(self):
        del self.values["package"]
        with self.assertRaisesRegex(ValueError, "package.*typo"):
            self.load(typo="A")

    def test_duplicate_json_key(self):
        self.path.write_text('{"package": "A", "package": "B"}', "utf-8")
        with self.assertRaisesRegex(ValueError, "package"):
            load_config(self.path)
