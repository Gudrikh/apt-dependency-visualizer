"""Чтение индекса Packages напрямую по HTTP(S)."""

import gzip
import lzma
import re
from collections.abc import Iterator
from http.client import HTTPException
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import urlopen

from src.config import APT_NAME


TIMEOUT_SECONDS = 30
GZIP_SIGNATURE = b"\x1f\x8b"
XZ_SIGNATURE = b"\xfd7zXZ\x00"
RELATION_FIELDS = ("Pre-Depends", "Depends")
INDEX_FIELDS = {"Package", *RELATION_FIELDS}
RELATION = re.compile(
    rf"({APT_NAME.pattern})(?::[a-z0-9-]+)?(?:\s*\([^()]+\))?"
)


def index_url(repository: str) -> str:
    """Для URL каталога выбрать стандартное имя сжатого индекса."""
    url = urlsplit(repository)
    if url.path.endswith("/"):
        return url._replace(path=url.path + "Packages.gz").geturl()
    return repository


def load_apt_repository(repository: str) -> dict[str, tuple[str, ...]]:
    """Скачать и прочитать индекс Packages, Packages.gz или Packages.xz."""
    url = index_url(repository)
    try:
        with urlopen(url, timeout=TIMEOUT_SECONDS) as response:
            data = response.read()
    except (OSError, HTTPException) as error:
        if isinstance(error, HTTPError):
            error.close()
        raise ValueError(
            f"repository: не удалось скачать {url} ({error})"
        ) from error
    try:
        if data.startswith(GZIP_SIGNATURE):
            data = gzip.decompress(data)
        elif data.startswith(XZ_SIGNATURE):
            data = lzma.decompress(data)
        return parse_packages(data.decode("utf-8"))
    except (OSError, EOFError, lzma.LZMAError, ValueError) as error:
        raise ValueError(
            f"repository: неверный индекс {url} ({error})"
        ) from error


def package_fields(text: str) -> Iterator[dict[str, str]]:
    """Выделить нужные поля отдельных записей Debian control."""
    fields = {}
    current = ""
    for line in text.splitlines():
        if not line.strip():
            if fields:
                yield fields
            fields = {}
            current = ""
        elif line.startswith((" ", "\t")):
            if current in fields:
                fields[current] += " " + line.strip()
        else:
            current, separator, value = line.partition(":")
            if separator and current in INDEX_FIELDS:
                fields[current] = value.strip()
    if fields:
        yield fields


def dependency_names(relation: str) -> set[str]:
    """Извлечь все имена, включая альтернативы из группы через |."""
    names = set()
    for item in re.split(r"[,|]", relation) if relation else ():
        match = RELATION.fullmatch(item.strip())
        if match is None:
            raise ValueError(f"неверная запись зависимости: {item!r}")
        names.add(match.group(1))
    return names


def parse_packages(text: str) -> dict[str, tuple[str, ...]]:
    """Построить списки прямых зависимостей из текстового индекса."""
    packages = {}
    for fields in package_fields(text):
        name = fields.get("Package", "")
        if not APT_NAME.fullmatch(name):
            raise ValueError(f"неверное поле Package: {name!r}")
        if name not in packages:
            dependencies = set()
            for field in RELATION_FIELDS:
                dependencies.update(dependency_names(fields.get(field, "")))
            packages[name] = tuple(sorted(dependencies))
    if not packages:
        raise ValueError("нет ни одной записи Package")
    return packages
