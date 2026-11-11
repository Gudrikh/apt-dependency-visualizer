"""CLI первого этапа. Читает и печатает конфигурацию."""

import argparse
import json
import sys
from pathlib import Path

from src.config import FIELDS, load_config


def main(argv: list[str] | None = None) -> int:
    """Вернуть код завершения после обработки файла JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="путь к файлу JSON")
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        for name in FIELDS:
            value = getattr(config, name)
            if isinstance(value, Path):
                value = str(value)
            print(f"{name} = {json.dumps(value, ensure_ascii=False)}")
    except (OSError, ValueError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
