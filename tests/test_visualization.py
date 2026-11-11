"""Проверки вывода PlantUML, ASCII и обработки ошибок рендера."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.main import check_output
from src.visualization import ascii_tree, plantuml, render_svg, save_diagram


class VisualizationTests(unittest.TestCase):
    def test_plantuml_includes_cycle_and_isolated_vertex(self):
        graph = {"C": (), "B": ("A",), "A": ("B",)}
        source = plantuml(graph, "A")
        self.assertIn('rectangle "A" as p0 #D8EEFC', source)
        self.assertIn('rectangle "C" as p2', source)
        self.assertIn("p0 --> p1\np1 --> p0", source)
        self.assertTrue(source.endswith("@enduml\n"))

    def test_ascii_marks_cycles_and_repeated_subtrees(self):
        graph = {"A": ("B", "C"), "B": ("D",), "C": ("D",), "D": ("A",)}
        tree = ascii_tree(graph, "A", 4)
        self.assertIn("|       \\-- A [cycle]", tree)
        self.assertTrue(tree.endswith("    \\-- D [shown]"))
        self.assertTrue(tree.isascii())

    def test_ascii_respects_depth_on_each_path(self):
        graph = {"A": ("B", "C"), "B": ("C",), "C": ("D",), "D": ()}
        expected = "A\n+-- B\n|   \\-- C\n\\-- C\n    \\-- D"
        self.assertEqual(ascii_tree(graph, "A", 2), expected)

    def test_save_creates_two_files(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "out/test.svg"
            svg = b'<svg xmlns="http://www.w3.org/2000/svg"/>'
            with patch("src.visualization.render_svg", return_value=svg):
                source = plantuml({"A": ()}, "A")
                puml = save_diagram(output, source)
            self.assertEqual(puml.read_text("utf-8"), source)
            self.assertEqual(output.read_bytes(), svg)

    def test_missing_jar(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict(os.environ, PLANTUML_JAR=f"{folder}/missing.jar"):
                with self.assertRaisesRegex(ValueError, "PlantUML JAR"):
                    render_svg(plantuml({"A": ()}, "A"))

    def test_reject_overwriting_a_test_repository(self):
        output = Path("example.svg")
        with self.assertRaisesRegex(ValueError, "output"):
            check_output(Path("config.json"), output.resolve(),
                         output.with_suffix(".puml"))
