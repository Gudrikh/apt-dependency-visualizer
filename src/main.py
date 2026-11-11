"""Построение и визуализация графа зависимостей пакета Ubuntu."""

import argparse
import sys
from pathlib import Path

from src.config import load_config
from src.graph import dependency_graph
from src.repository import load_repository
from src.visualization import ascii_tree, plantuml, save_diagram


def check_output(config_file: Path, output: Path, repository: Path) -> None:
    """Проверить, что визуализация не перезапишет входные файлы."""
    targets = {output, output.with_suffix(".puml").resolve()}
    if targets.intersection({config_file.resolve(), repository.resolve()}):
        raise ValueError("output: файлы диаграммы совпадают со входными")


def main(argv: list[str] | None = None) -> int:
    """Вернуть код завершения после обработки файла JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="путь к файлу JSON")
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        input_file = (
            Path(config.repository) if config.test_mode else args.config
        )
        check_output(args.config, config.output, input_file)
        repository = load_repository(config)
        graph = dependency_graph(
            repository, config.package, config.max_depth,
            config.exclude_substring,
        )
        source = plantuml(graph, config.package)
        puml = save_diagram(config.output, source)
        print(f"PlantUML: {puml}")
        print(f"SVG: {config.output}")
        if config.ascii_tree:
            print(ascii_tree(graph, config.package, config.max_depth))
    except (OSError, ValueError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
