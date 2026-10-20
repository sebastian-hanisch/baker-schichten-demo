"""Gemeinsame Fixtures: die Mini-Graphen, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import itertools
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def adj_from_edges(n, edges):
    adj = [set() for _ in range(n)]
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    return tuple(frozenset(a) for a in adj)


@pytest.fixture
def path7():
    """Weg 0 – 1 – … – 6: BFS von 0 gibt die Schichten 0 bis 6, die größte unabhängige Menge hat 4 Knoten (0, 2, 4, 6)."""
    return adj_from_edges(7, [(i, i + 1) for i in range(6)])


@pytest.fixture
def star():
    """Stern mit Mitte 0 und vier Blättern: größte unabhängige Menge sind die 4 Blätter."""
    return adj_from_edges(5, [(0, i) for i in range(1, 5)])


@pytest.fixture
def grid3():
    """3 × 3-Gitter (Knoten zeilenweise 0 bis 8): BFS von 0 gibt die Schichten (0,1,2,1,2,3,2,3,4), die größte unabhängige Menge hat 5 Knoten (0, 2, 4, 6, 8)."""
    edges = [(i, i + 1) for i in range(9) if i % 3 < 2] + [(i, i + 3) for i in range(6)]
    return adj_from_edges(9, edges)


def brute_force_mis(adj) -> int:
    """Größe einer größten unabhängigen Menge durch Aufzählen aller Teilmengen (nur für wenige Knoten)."""
    n = len(adj)
    best = 0
    for r in range(n, 0, -1):
        if r <= best:
            break
        for subset in itertools.combinations(range(n), r):
            chosen = set(subset)
            if all(not (set(adj[v]) & chosen) for v in subset):
                return r
    return best
