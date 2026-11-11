"""CLI четвёртого этапа. Показывает прямой или обратный граф."""

import argparse
import sys
from pathlib import Path

from src.config import load_config
from src.graph import dependency_graph, reverse_edges
from src.repository import load_repository


def main(argv: list[str] | None = None) -> int:
    """Вернуть код завершения после обработки файла JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="путь к файлу JSON")
    parser.add_argument(
        "--reverse", action="store_true", help="показать обратные зависимости",
    )
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        repository = load_repository(config)
        if args.reverse:
            repository = reverse_edges(repository)
        graph = dependency_graph(
            repository, config.package, config.max_depth,
            config.exclude_substring,
        )
        arrow = "<-" if args.reverse else "->"
        for name in sorted(graph):
            children = ", ".join(graph[name]) or "-"
            print(f"{name} {arrow} {children}")
    except (OSError, ValueError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
