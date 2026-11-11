"""Построение ограниченного графа итеративным обходом в глубину."""


Graph = dict[str, tuple[str, ...]]


def dependency_graph(
    repository: Graph,
    root: str,
    max_depth: int,
    exclude_substring: str,
) -> Graph:
    """Собрать рёбра на глубине до max_depth, сохраняя циклы."""
    if root not in repository:
        raise ValueError(f"Пакет {root} отсутствует в репозитории")
    if exclude_substring and exclude_substring in root:
        raise ValueError(f"exclude_substring: скрывает исходный пакет {root}")
    graph = {}
    depths = {}
    stack = [(root, 0)]
    beyond_limit = max_depth + 1
    while stack:
        package, depth = stack.pop()
        if depth >= depths.get(package, beyond_limit):
            continue
        depths[package] = depth
        children = ()
        if depth < max_depth:
            children = allowed_packages(
                repository.get(package, ()), exclude_substring
            )
        graph[package] = children
        stack.extend((child, depth + 1) for child in reversed(children))
    return graph


def allowed_packages(
    packages: tuple[str, ...], exclude_substring: str,
) -> tuple[str, ...]:
    """Исключить имена, содержащие подстроку с учётом регистра."""
    if not exclude_substring:
        return packages
    return tuple(name for name in packages if exclude_substring not in name)


def reverse_edges(repository: Graph) -> Graph:
    """Развернуть рёбра, сохранив изолированные и виртуальные вершины."""
    incoming = {name: [] for name in repository}
    for name, dependencies in repository.items():
        for child in dependencies:
            incoming.setdefault(child, []).append(name)
    return {name: tuple(sorted(parents)) for name, parents in incoming.items()}
