# Variable-graph helpers with no Qt dependency.
from __future__ import annotations

from collections import deque
from typing import Any, Dict, Iterable, List, Tuple


def graph_has_cycle(node_definitions: Dict[Any, str]) -> bool:
    """True if definition nodes form a cycle through $var dependencies."""
    calc_nodes = list(node_definitions)
    if not calc_nodes:
        return False
    var_to_def = {v: k for k, v in node_definitions.items()}
    in_degree = {node: 0 for node in calc_nodes}
    graph = {node: set() for node in calc_nodes}
    for node in calc_nodes:
        for var in getattr(node, "dependencies", ()) or ():
            source = var_to_def.get(f"${var}")
            if source and source in graph and source is not node:
                graph[source].add(node)
                in_degree[node] += 1
    queue = deque([n for n, d in in_degree.items() if d == 0])
    seen = 0
    while queue:
        node = queue.popleft()
        seen += 1
        for dep in graph[node]:
            in_degree[dep] -= 1
            if in_degree[dep] == 0:
                queue.append(dep)
    return seen != len(calc_nodes)


def definition_edges(node_definitions: Dict[Any, str], dependencies: Dict[str, Iterable]) -> List[Tuple[Any, Any]]:
    var_to_def = {v: k for k, v in node_definitions.items()}
    edges = []
    for var_name, dependents in dependencies.items():
        source = var_to_def.get(var_name)
        if source is None:
            continue
        for dep in dependents:
            if dep is not source:
                edges.append((source, dep))
    return edges
