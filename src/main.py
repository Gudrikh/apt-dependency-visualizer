"""CLI второго этапа. Показывает прямые зависимости пакета Ubuntu."""

import argparse
import sys
from pathlib import Path

from src.apt import load_apt_repository
from src.config import load_config


def main(argv: list[str] | None = None) -> int:
    """Вернуть код завершения после обработки файла JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="путь к файлу JSON")
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if config.test_mode:
            raise ValueError("test_mode: тестовый граф появится на этапе 3")
        packages = load_apt_repository(config.repository)
        if config.package not in packages:
            raise ValueError(f"Пакет {config.package} отсутствует в индексе")
        print(f"Прямые зависимости пакета {config.package}:")
        print("\n".join(packages[config.package]) or "(нет)")
    except (OSError, ValueError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
