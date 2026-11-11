"""Проверки глубины, циклов, фильтра и загрузки тестовых графов."""

import tempfile
import unittest
from pathlib import Path

from src.graph import dependency_graph
from src.repository import load_test_repository


class GraphTests(unittest.TestCase):
    def test_expand_again_at_a_shallower_depth(self):
        repository = {"A": ("B", "C"), "B": ("C",), "C": ("D",), "D": ()}
        self.assertEqual(dependency_graph(repository, "A", 2, ""), repository)

    def test_cycle_preserves_back_edge_and_self_loop(self):
        repository = {"A": ("A", "B"), "B": ("A",)}
        self.assertEqual(dependency_graph(repository, "A", 9, ""), repository)

    def test_filter_and_depth(self):
        repository = {"A": ("B", "C"), "B": ("E",), "C": ("D",), "D": ("E",)}
        graph = dependency_graph(repository, "A", 2, "B")
        self.assertEqual(graph, {"A": ("C",), "C": ("D",), "D": ()})

    def test_zero_depth_and_unknown_root(self):
        repository = {"A": ("B",), "B": ()}
        self.assertEqual(dependency_graph(repository, "A", 0, ""), {"A": ()})
        with self.assertRaisesRegex(ValueError, "Z"):
            dependency_graph(repository, "Z", 2, "")
        with self.assertRaisesRegex(ValueError, "exclude_substring"):
            dependency_graph(repository, "A", 2, "A")

    def test_unavailable_dependency_is_a_leaf(self):
        repository = {"app": ("virtual-name",)}
        graph = dependency_graph(repository, "app", 2, "")
        self.assertEqual(graph, repository | {"virtual-name": ()})

    def test_chain_longer_than_recursion_limit(self):
        length = 1500
        repository = {str(i): (str(i + 1),) for i in range(length)}
        graph = dependency_graph(repository, "0", length, "")
        self.assertEqual(len(graph), length + 1)
        self.assertEqual(graph[str(length)], ())

    def test_invalid_test_repository(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "invalid.json"
            for data in ('{"a": []}', '{"A": ["B"]}', '{"A": "A"}', '[]'):
                with self.subTest(data=data):
                    path.write_text(data, "utf-8")
                    with self.assertRaises(ValueError):
                        load_test_repository(path)
