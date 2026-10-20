"""Szenario: planare Graphen für die Baker-Technik (Delaunay-Karten, dünne Karten, Gitter) und die Wahl der Wurzel.

Ein Graph hat Knoten 0 bis n − 1, Lage in der Ebene und Nachbarmengen. Gitter und Karten stammen aus `planar-dual-demo` und `graph-zeichnen-demo`; Zufall nur aus `numpy.random.default_rng(seed)`."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

import bkr_constants as C


@dataclass(frozen=True)
class Graph:
    adj: tuple[frozenset[int], ...]
    pos: tuple[tuple[float, float], ...]
    name: str = ""

    @property
    def n(self) -> int:
        return len(self.adj)

    @property
    def m(self) -> int:
        return sum(len(a) for a in self.adj) // 2

    def edges(self) -> list[tuple[int, int]]:
        return [(u, v) for u in range(self.n) for v in sorted(self.adj[u]) if u < v]


def _from_edges(n: int, edges, pos, name: str) -> Graph:
    adj: list[set[int]] = [set() for _ in range(n)]
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    return Graph(tuple(frozenset(a) for a in adj), tuple((float(x), float(y)) for x, y in pos), name)


def grid_side(n: int) -> int:
    return max(2, round(math.sqrt(n)))


def make_delaunay(n: int, seed: int) -> Graph:
    """Zufällige Standorte im Einheitsquadrat und alle Kanten ihrer Delaunay-Triangulierung (scipy/Qhull)."""
    from scipy.spatial import Delaunay

    points = np.random.default_rng(seed).random((n, 2))
    found = set()
    for simplex in Delaunay(points).simplices:
        a, b, c = (int(x) for x in simplex)
        found.update({(min(a, b), max(a, b)), (min(b, c), max(b, c)), (min(a, c), max(a, c))})
    return _from_edges(n, sorted(found), points, f"Karte mit {n} Standorten")


def make_thin(n: int, seed: int, keep: float = C.THIN_KEEP) -> Graph:
    """Dieselbe Karte mit zufällig `keep` der Kanten (kann in Stücke zerfallen)."""
    base = make_delaunay(n, seed)
    edges = base.edges()
    rng = np.random.default_rng(seed + 7919)
    chosen = sorted(int(i) for i in rng.choice(len(edges), size=round(keep * len(edges)), replace=False))
    return _from_edges(n, [edges[i] for i in chosen], base.pos, f"Karte mit 80 % der Kanten, {n} Standorte")


def make_grid(n: int, diagonals: bool) -> Graph:
    """k × k Knoten (k = Wurzel aus n, gerundet, mindestens 2); mit einer Diagonale je Zelle oder ohne."""
    k = grid_side(n)
    edges = []
    for r in range(k):
        for c in range(k):
            i = r * k + c
            if c + 1 < k:
                edges.append((i, i + 1))
            if r + 1 < k:
                edges.append((i, i + k))
            if diagonals and r + 1 < k and c + 1 < k:
                edges.append((i, i + k + 1))
    pos = [(float(i % k), float(-(i // k))) for i in range(k * k)]
    return _from_edges(k * k, edges, pos, f"Gitter {k} × {k}" + (" mit Diagonalen" if diagonals else ""))


def make_graph(net: str, n: int, seed: int) -> Graph:
    """Deterministisch aus den Argumenten: gleiche Eingabe, gleicher Graph."""
    if net == "delaunay":
        return make_delaunay(n, seed)
    if net == "thin":
        return make_thin(n, seed)
    if net == "grid_diag":
        return make_grid(n, True)
    if net == "grid":
        return make_grid(n, False)
    raise ValueError(net)


def root_vertex(graph: Graph, kind: str) -> int:
    """Wurzel der Breitensuche: 'center' = Knoten nächst dem Schwerpunkt, 'edge' = linkester Knoten (bei Gleichstand der mit kleinerem y, dann der kleineren Nummer)."""
    xs = [p[0] for p in graph.pos]
    ys = [p[1] for p in graph.pos]
    if kind == "edge":
        return min(range(graph.n), key=lambda v: (xs[v], ys[v], v))
    if kind == "center":
        cx, cy = sum(xs) / graph.n, sum(ys) / graph.n
        return min(range(graph.n), key=lambda v: ((xs[v] - cx) ** 2 + (ys[v] - cy) ** 2, v))
    raise ValueError(kind)
