"""Представления одного графа в PlantUML, SVG и ASCII."""

import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree import ElementTree

from src.graph import Graph


DEFAULT_JAR = Path(__file__).resolve().parents[1] / "tools/plantuml.jar"
RENDER_TIMEOUT = 60
SVG_TAG = "{http://www.w3.org/2000/svg}svg"
LAST_BRANCH = "\\-- "
BRANCH = "+-- "


def plantuml(graph: Graph, root: str) -> str:
    """Сформировать ориентированную диаграмму со стабильными псевдонимами."""
    names = sorted(graph)
    aliases = {name: f"p{index}" for index, name in enumerate(names)}
    lines = [
        "@startuml",
        "!pragma layout smetana",
        "left to right direction",
        "skinparam shadowing false",
        "skinparam ArrowColor #536878",
        "skinparam RectangleBorderColor #536878",
        "skinparam RectangleBackgroundColor #F5F8FA",
    ]
    for name in names:
        color = " #D8EEFC" if name == root else ""
        lines.append(f'rectangle "{name}" as {aliases[name]}{color}')
    for name in names:
        for child in graph[name]:
            lines.append(f"{aliases[name]} --> {aliases[child]}")
    return "\n".join([*lines, "@enduml", ""])


def ascii_tree(graph: Graph, root: str, max_depth: int) -> str:
    """Показать дерево путей до предела глубины с отметками повторов."""
    lines = []
    shown_at = {}
    stack = [(root, "", "", ())]
    while stack:
        name, indent, branch, ancestors = stack.pop()
        line = indent + branch + name
        depth = len(ancestors)
        if name in ancestors:
            lines.append(line + " [cycle]")
            continue
        if depth >= shown_at.get(name, max_depth + 1):
            lines.append(line + " [shown]")
            continue
        lines.append(line)
        shown_at[name] = depth
        if depth == max_depth:
            continue
        if branch:
            indent += "    " if branch == LAST_BRANCH else "|   "
        children = graph[name]
        child_ancestors = (*ancestors, name)
        for index, child in enumerate(reversed(children)):
            connector = BRANCH if index else LAST_BRANCH
            stack.append((child, indent, connector, child_ancestors))
    return "\n".join(lines)


def render_svg(source: str) -> bytes:
    """Передать PlantUML в локальный Java-процесс и проверить ответ."""
    jar = Path(os.environ.get("PLANTUML_JAR", DEFAULT_JAR))
    if not jar.is_file():
        raise ValueError(
            "PlantUML JAR не найден. Поместите его в tools/plantuml.jar "
            "или задайте PLANTUML_JAR. См. инструкцию в README.md."
        )
    try:
        result = subprocess.run(
            ["java", "-jar", str(jar), "-charset", "UTF-8", "-tsvg", "-pipe"],
            input=source.encode("utf-8"),
            capture_output=True,
            timeout=RENDER_TIMEOUT,
            check=False,
        )
    except FileNotFoundError as error:
        raise ValueError("Команда java не найдена в PATH") from error
    except subprocess.TimeoutExpired as error:
        raise ValueError("PlantUML превысил время ожидания") from error
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"Ошибка PlantUML ({result.returncode}): {detail}")
    try:
        tag = ElementTree.fromstring(result.stdout).tag
    except ElementTree.ParseError as error:
        raise ValueError("PlantUML вернул некорректный SVG") from error
    if tag != SVG_TAG:
        raise ValueError("Ответ PlantUML не содержит SVG")
    return result.stdout


def save_diagram(output: Path, source: str) -> Path:
    """Сохранить диаграмму и её исходный текст рядом."""
    puml = output.with_suffix(".puml")
    if puml.is_dir():
        raise ValueError(f"output: {puml} является каталогом")
    svg = render_svg(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output.parent) as folder:
        temp_svg = Path(folder) / "graph.svg"
        temp_puml = Path(folder) / "graph.puml"
        temp_svg.write_bytes(svg)
        temp_puml.write_text(source, encoding="utf-8")
        temp_svg.replace(output)
        temp_puml.replace(puml)
    return puml
