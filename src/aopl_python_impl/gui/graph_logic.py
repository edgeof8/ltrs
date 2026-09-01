# Variable-graph helpers with no Qt dependency.
from __future__ import annotations

from collections import deque
from math import atan2, cos, pi, sin
from typing import Any, Dict, Iterable, List, Optional, Tuple


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


def point_on_rect_toward(
    cx: float,
    cy: float,
    width: float,
    height: float,
    tx: float,
    ty: float,
) -> Tuple[float, float]:
    """Hit the border of a rect centered at (cx, cy) on the way toward (tx, ty)."""
    dx = tx - cx
    dy = ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    hw = max(width, 1.0) / 2.0
    hh = max(height, 1.0) / 2.0
    sx = hw / abs(dx) if dx else float("inf")
    sy = hh / abs(dy) if dy else float("inf")
    t = min(sx, sy)
    return cx + dx * t, cy + dy * t


def arrow_head_points(
    x1: float, y1: float, x2: float, y2: float, size: float = 11.0
) -> Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]:
    angle = atan2(y2 - y1, x2 - x1)
    left = (x2 - size * cos(angle - pi / 6), y2 - size * sin(angle - pi / 6))
    right = (x2 - size * cos(angle + pi / 6), y2 - size * sin(angle + pi / 6))
    return (x2, y2), left, right


def pair_display_lines(
    num: str, aop: Optional[str], primary_mode: str
) -> Tuple[str, Optional[str]]:
    """Primary result plus optional fingerprint. Identical strings stay one line."""
    if not aop or aop == num:
        if primary_mode == "aop" and aop:
            return aop, None
        return num, None
    if primary_mode == "aop":
        return aop, num
    return num, aop
