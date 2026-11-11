# Визуализатор зависимостей Ubuntu APT

Практическая работа №2 по конфигурационному управлению. Группа ИКБО-62-25,
вариант 7.

Исходный код и история этапов доступны на [GitHub][repository].

Программа читает индекс пакетов Ubuntu по HTTP(S), строит граф прямых и
транзитивных зависимостей и сохраняет его в PlantUML и SVG. Можно
ограничить глубину, исключить пакеты по имени и вывести ASCII-дерево.
Тестовый режим работает с локальным JSON без сети.

## Запуск

Для анализа нужен Python 3.10 или новее. Для рендера установите Java,
доступную как `java` в PATH. PlantUML рисует граф через встроенный Smetana.
Установка пакетов Python и Graphviz для запуска программы не требуется.

В PowerShell из корня проекта скачайте проверенную версию PlantUML и
запустите пример.

```powershell
New-Item -ItemType Directory -Force tools | Out-Null
$base = "https://repo.maven.apache.org/maven2/net/sourceforge/plantuml"
$version = "1.2025.4"
curl.exe -fL "$base/plantuml/$version/plantuml-$version.jar" -o tools/plantuml.jar
.\run.bat examples/ubuntu-hello.json
python -m unittest discover -v
```

Переменная среды `PLANTUML_JAR` позволяет указать путь к уже скачанному
JAR. Для запуска на Linux используйте команду ниже.

```bash
python3 -m src.main examples/ubuntu-hello.json
```

Отдельная сборка проекта не требуется. Тесты запускаются без Java и без
подключения к интернету.

## Конфигурация JSON

Все семь полей обязательны. Относительные пути считаются от каталога
конфигурационного файла. Примеры лежат в `examples/`.

| Ключ | Значение |
| --- | --- |
| `package` | Имя пакета APT или имя заглавными латинскими буквами в тестовом режиме. |
| `repository` | URL индекса `Packages`, `Packages.gz`, `Packages.xz` или путь к тестовому JSON. Для URL с `/` в конце подставляется `Packages.gz`. |
| `test_mode` | `true` для тестового JSON, `false` для Ubuntu. |
| `output` | Путь к файлу `.svg`. Рядом сохраняется файл `.puml` с тем же именем. |
| `ascii_tree` | `true` включает печать ASCII-дерева. При `false` выводятся пути к файлам. |
| `max_depth` | Неотрицательное целое. Глубина корня равна 0. |
| `exclude_substring` | Пакеты с этой подстрокой исключаются с учётом регистра. Пустая строка отключает фильтр. |

Ошибки конфигурации, загрузки индекса и рендера дают сообщение и код
завершения 1. Если фильтр совпадает с именем корневого пакета, запуск
завершается ошибкой. У отсутствующего в индексе корня также будет ошибка.

## Этапы

Теги `stage-1` … `stage-5` указывают на пять отдельных коммитов.
Для демонстрации раннего этапа выполните `git switch --detach stage-1`,
подставив нужный тег. Возврат к итоговой версии — `git switch main`.

| Тег | Что показать |
| --- | --- |
| [`stage-1`][stage-1] | `run.bat examples/local.json` печатает семь настроек. Тест `test_invalid_parameter_values` проверяет ошибку для каждого поля. |
| [`stage-2`][stage-2] | `run.bat examples/ubuntu-hello.json` показывает прямую зависимость `libc6` из индекса Ubuntu. |
| [`stage-3`][stage-3] | Три тестовых сценария ниже показывают циклы, глубину и фильтр. |
| [`stage-4`][stage-4] | Те же сценарии с `--reverse` показывают обратные зависимости. |
| [`stage-5`][stage-5] | Визуализация трёх пакетов в PlantUML, SVG и ASCII. [Изменения в коммите][stage-5-commit]. |

### Тестовый граф и обратные зависимости

```powershell
.\run.bat examples/local.json
.\run.bat examples/local-limited.json
.\run.bat examples/local-isolated.json
```

В `examples/repository.json` каждому пакету сопоставлен массив имён.
Например, `{"A":["B"],"B":[]}` задаёт ребро A → B. Каждый пакет должен
присутствовать среди ключей, включая пакеты без зависимостей.

- `local.json` содержит циклы C → D → C и A → C → E → A.
- `local-limited.json` исключает D, а E находится на предельной глубине 2.
- `local-isolated.json` выводит только Z на глубине 0.

На этапе 4 добавьте `--reverse` к каждой из трёх команд. В полном
сценарии цепочка G → F → E → A даёт обратные зависимости F и G.
В ограниченном сценарии G отсекается глубиной, а у Z входящих рёбер нет.

### Алгоритм

DFS использует явный стек и запоминает наименьшую глубину обработки
вершины. Если вершина достигнута позже по более короткому пути, DFS
повторно раскрывает её зависимости. На предельной глубине вершина видна
без дальнейшего обхода. Обратные рёбра обрабатываются тем же DFS после
разворота графа репозитория.

В ASCII-дереве метка `[cycle]` обозначает возвращение к предку текущей
ветви, а `[shown]` — повтор узла, уже показанного на той же или меньшей
глубине. Диаграмма сохраняет рёбра циклов.

## Этап 5. Визуализация

```powershell
.\run.bat examples/ubuntu-hello.json
.\run.bat examples/ubuntu-jq.json
.\run.bat examples/ubuntu-curl.json
```

Откройте `output/hello.svg`, `output/jq.svg` и `output/curl.svg` в
браузере. Голубым выделен исходный пакет. Стрелка направлена от пакета к
его зависимости. В тех же каталогах лежат исходники `.puml`.

```text
hello
\-- libc6
    \-- libgcc-s1
```

## Сравнение с apt-cache dotty

Для проверки использован APT 2.8.3 на Ubuntu 24.04, архитектура amd64,
с тем же индексом `noble/main` и пустым списком установленных пакетов.
У всех трёх конфигураций глубина 2, фильтр отключён.

| Пакет | Вершин в SVG | Рёбер в SVG | Рёбер зависимостей в DOT | Зелёных рёбер в DOT |
| --- | ---: | ---: | ---: | ---: |
| `hello` | 3 | 2 | 4 | 20 |
| `jq` | 5 | 5 | 8 | 18 |
| `curl` | 15 | 17 | 81 | 54 |

Рёбра `Depends` и `Pre-Depends` в пределах глубины 2 совпали для всех
трёх пакетов. `apt-cache dotty` продолжает обход за этой границей.
Например, DOT содержит ребро `libgcc-s1 → gcc-14-base`, которое лежит
на третьем шаге от `hello`. Зелёным DOT обозначает отрицательные
отношения, например конфликт `hello → hello-traditional`.
В SVG входят только `Depends` и `Pre-Depends`.

Для повторения сравнения в Linux можно собрать временный кэш APT из
того же индекса.

```bash
tmp=$(mktemp -d)
base=https://archive.ubuntu.com/ubuntu
index=dists/noble/main/binary-amd64/Packages.gz
list=archive.ubuntu.com_ubuntu_dists_noble_main_binary-amd64_Packages
mkdir "$tmp/lists"
printf 'deb %s noble main\n' "$base" > "$tmp/sources.list"
curl -fsSL "$base/$index" | gzip -dc > "$tmp/lists/$list"
for pkg in hello jq curl; do
  apt-cache -o Dir::Etc::sourcelist="$tmp/sources.list" \
    -o Dir::Etc::sourceparts=- -o Dir::State::lists="$tmp/lists" \
    -o Dir::State::status=/dev/null -o Dir::Cache::pkgcache="" \
    -o Dir::Cache::srcpkgcache="" dotty "$pkg" > "$pkg.dot"
done
```

Программа включает имена всех заявленных альтернатив, убирает условия
версий и уточнения архитектуры. Если записей пакета несколько, берётся
первая запись из индекса. Зависимость без собственной записи остаётся
листом. Подбор версий и провайдеров виртуальных пакетов в анализ не входит.
APT используется только в контрольном сравнении.

[Документация apt-cache](https://manpages.ubuntu.com/manpages/noble/man8/apt-cache.8.html) ·
[Формат зависимостей Debian](https://www.debian.org/doc/debian-policy/ch-relationships.html) ·
[Командная строка PlantUML](https://plantuml.com/command-line)

## Файлы проекта

- `src/config.py` проверяет параметры, а `src/apt.py` читает индекс.
- `src/repository.py` выбирает источник, а `src/graph.py` строит граф.
- `src/visualization.py` отвечает за три формата вывода, `src/main.py` за CLI.
- `examples/` содержит конфигурации, `tests/` — автоматические проверки.
- `run.bat` запускает CLI из PowerShell или cmd.

[repository]: https://github.com/Gudrikh/apt-dependency-visualizer
[stage-1]: https://github.com/Gudrikh/apt-dependency-visualizer/tree/stage-1
[stage-2]: https://github.com/Gudrikh/apt-dependency-visualizer/tree/stage-2
[stage-3]: https://github.com/Gudrikh/apt-dependency-visualizer/tree/stage-3
[stage-4]: https://github.com/Gudrikh/apt-dependency-visualizer/tree/stage-4
[stage-5]: https://github.com/Gudrikh/apt-dependency-visualizer#этап-5-визуализация
[stage-5-commit]: https://github.com/Gudrikh/apt-dependency-visualizer/commit/655bee64780daede83dda9d750d544101445b11f
