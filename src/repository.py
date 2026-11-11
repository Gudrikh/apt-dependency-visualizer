"""Выбор реального или тестового источника зависимостей."""

import json
from pathlib import Path

from src.apt import load_apt_repository
from src.config import Config, TEST_NAME, unique_keys
from src.graph import Graph


def load_repository(config: Config) -> Graph:
    """Загрузить списки смежности из указанного источника."""
    if config.test_mode:
        return load_test_repository(Path(config.repository))
    return load_apt_repository(config.repository)


def load_test_repository(path: Path) -> Graph:
    """Прочитать словарь из имён пакетов и списков их зависимостей."""
    with path.open(encoding="utf-8-sig") as source:
        data = json.load(source, object_pairs_hook=unique_keys)
    if not isinstance(data, dict) or not data:
        raise ValueError("repository: нужен непустой объект JSON")
    graph = {}
    for name, dependencies in data.items():
        if not TEST_NAME.fullmatch(name):
            raise ValueError(f"repository: неверное имя пакета {name!r}")
        if not isinstance(dependencies, list):
            raise ValueError(f"repository: {name} должен содержать список")
        for child in dependencies:
            if not isinstance(child, str) or child not in data:
                raise ValueError(
                    f"repository: зависимость {child!r} пакета {name} "
                    "отсутствует среди ключей"
                )
        graph[name] = tuple(sorted(set(dependencies)))
    return graph
