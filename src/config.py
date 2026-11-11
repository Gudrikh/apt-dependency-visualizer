"""Загрузка и проверка семи параметров конфигурации."""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


APT_NAME = re.compile(r"[a-z0-9][a-z0-9+.-]+")
TEST_NAME = re.compile(r"[A-Z]+")
MIN_DEPTH = 0
FIELDS = (
    "package", "repository", "test_mode", "output", "ascii_tree",
    "max_depth", "exclude_substring",
)


@dataclass(frozen=True)
class Config:
    """Проверенные параметры с путями относительно файла JSON."""

    package: str
    repository: str
    test_mode: bool
    output: Path
    ascii_tree: bool
    max_depth: int
    exclude_substring: str


def check_keys(values: dict) -> None:
    """Проверить наличие всех полей и выявить лишние."""
    missing = set(FIELDS) - values.keys()
    extra = values.keys() - set(FIELDS)
    if missing or extra:
        details = []
        if missing:
            details.append("отсутствуют " + ", ".join(sorted(missing)))
        if extra:
            details.append("неизвестны " + ", ".join(sorted(extra)))
        raise ValueError("Поля конфигурации: " + "; ".join(details))


def validate_fields(values: object) -> dict:
    """Проверить набор полей и их типы."""
    if not isinstance(values, dict):
        raise ValueError("Конфигурация должна быть объектом JSON")
    check_keys(values)
    for name in ("test_mode", "ascii_tree"):
        if type(values[name]) is not bool:
            raise ValueError(f"{name}: ожидается true или false")
    for name in ("package", "repository", "output", "exclude_substring"):
        if not isinstance(values[name], str):
            raise ValueError(f"{name}: ожидается строка")
    depth = values["max_depth"]
    if type(depth) is not int or depth < MIN_DEPTH:
        raise ValueError("max_depth: ожидается целое число от 0")
    return values


def unique_keys(pairs: list[tuple]) -> dict:
    """Отклонить дубли ключей при чтении JSON."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Ключ JSON указан дважды: {key}")
        result[key] = value
    return result


def http_url(value: str) -> str:
    """Проверить абсолютный HTTP(S)-адрес индекса."""
    try:
        url = urlsplit(value)
        _ = url.port
    except ValueError as error:
        raise ValueError(f"repository: неверный URL ({error})") from error
    if not url.hostname or url.scheme not in {"http", "https"}:
        raise ValueError("repository: нужен URL с http:// или https://")
    if any(char.isspace() or not char.isprintable() for char in value):
        raise ValueError("repository: URL содержит пробел или спецсимвол")
    if url.username is not None or url.fragment:
        raise ValueError("repository: URL должен быть без логина и фрагмента")
    return value


def local_path(folder: Path, value: str, field: str) -> Path:
    """Получить путь относительно каталога конфигурации."""
    if not value.strip() or not value.isprintable():
        raise ValueError(f"{field}: нужен непустой путь к файлу")
    return (folder / value).resolve()


def output_path(folder: Path, value: str) -> Path:
    """Проверить расширение и родительский каталог файла графа."""
    path = local_path(folder, value, "output")
    if path.suffix.lower() != ".svg" or path.is_dir():
        raise ValueError("output: укажите имя файла с расширением .svg")
    for parent in path.parents:
        if parent.is_file():
            raise ValueError(f"output: {parent} является файлом")
    return path


def load_config(path: Path) -> Config:
    """Прочитать конфигурацию и проверить значения полей."""
    with path.open(encoding="utf-8-sig") as source:
        values = json.load(source, object_pairs_hook=unique_keys)
    values = validate_fields(values)
    folder = path.resolve().parent
    test_mode = values["test_mode"]
    name_pattern = TEST_NAME if test_mode else APT_NAME
    if not name_pattern.fullmatch(values["package"]):
        description = "заглавными латинскими буквами" if test_mode else "APT"
        raise ValueError(f"package: ожидается имя пакета {description}")
    repository = values["repository"]
    if test_mode:
        local = local_path(folder, repository, "repository")
        if not local.is_file():
            raise ValueError(f"repository: тестовый файл не найден ({local})")
        repository = str(local)
    else:
        repository = http_url(repository)
    values["repository"] = repository
    values["output"] = output_path(folder, values["output"])
    return Config(**values)
