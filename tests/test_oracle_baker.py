"""Orakel-Test baker-schichten-demo / baker: die Baker-Lösung gegen drei andere Rechenwege.

Orakel (ORACLE-PLAYBOOK, Verfahrenstyp „Näherungsverfahren mit Garantie“):
1. **Brute Force** über alle Teilmengen auf Graphen bis 18 Knoten (Optimum), dazu die Garantie size · k ≥ (k − 1) · OPT und size ≤ OPT;
2. ein **zweites ganzzahliges Programm** (`scipy.milp` mit nur Kantenbedingungen, ohne die Dreiecks-Cliquen des Kerns) auf Karten und Gittern mit 60 Knoten;
3. die **Dynamische Programmierung über den ganzen Graphen** (gleiches Verfahren wie je Rest, aber ohne Schichten) auf Graphen mit 40 Knoten;
dazu die Bauteile: jede Verschiebung liefert eine unabhängige Menge ohne Knoten der gelöschten Schichten; zwischen verschiedenen Resten liegt keine Kante; benachbarte Knoten haben Schichten, die sich um höchstens 1 unterscheiden;
das Dreiecks-Programm des Kerns gleich dem Kanten-Programm."""

import numpy as np
import pytest

import bkr_algorithm as A
import bkr_exact as X
import bkr_scenario as S
from conftest import brute_force_mis

NETS = ("delaunay", "thin", "grid_diag", "grid")


def edge_milp(adj) -> int:
    """Zweites Orakel: nur Kantenbedingungen x_u + x_v ≤ 1."""
    from scipy.optimize import Bounds, LinearConstraint, milp
    from scipy.sparse import lil_matrix

    n = len(adj)
    edges = [(u, v) for u in range(n) for v in adj[u] if u < v]
    if not edges:
        return n
    matrix = lil_matrix((len(edges), n))
    for i, (u, v) in enumerate(edges):
        matrix[i, u] = matrix[i, v] = 1
    res = milp(-np.ones(n), constraints=LinearConstraint(matrix.tocsr(), -np.inf, 1), integrality=np.ones(n), bounds=Bounds(0, 1))
    return int(round(-res.fun))


def small_graphs():
    for seed in range(12):
        yield pytest.param(S.make_delaunay(18, seed), f"delaunay-{seed}")
        yield pytest.param(S.make_thin(18, seed), f"thin-{seed}")
    yield pytest.param(S.make_grid(16, False), "grid-4")
    yield pytest.param(S.make_grid(16, True), "grid_diag-4")


@pytest.mark.parametrize("graph,name", list(small_graphs()))
def test_baker_is_independent_below_the_optimum_and_meets_the_guarantee_on_small_graphs(graph, name):
    opt = brute_force_mis(graph.adj)
    assert A.milp_optimum(graph.adj).value == opt
    for k in (2, 3, 4, 5):
        for root in (0, graph.n // 2):
            r = A.baker(graph.adj, k, root)
            assert r.aborted == 0
            assert A.is_independent(graph.adj, r.best.chosen)
            assert A.meets_guarantee(r.size, opt, k) and r.size <= opt, (name, k, root, r.size, opt)


@pytest.mark.parametrize("net", NETS)
@pytest.mark.parametrize("seed", range(6))
def test_baker_against_a_second_milp_on_medium_graphs(net, seed):
    graph = S.make_graph(net, 60, seed)
    opt = edge_milp(graph.adj)
    assert A.milp_optimum(graph.adj).value == opt                     # Dreiecks-Programm des Kerns gleich dem Kanten-Programm
    for k in (2, 3, 4, 6):
        r = A.baker(graph.adj, k, S.root_vertex(graph, "center"))
        assert A.meets_guarantee(r.size, opt, k) and r.size <= opt


@pytest.mark.parametrize("net", ("delaunay", "thin", "grid_diag"))
@pytest.mark.parametrize("seed", range(5))
def test_pieces_agree_with_the_whole_graph_dp(net, seed):
    graph = S.make_graph(net, 40, seed)
    order = X.min_fill_order(graph.adj)
    whole = X.max_weight_independent_set(graph.adj, [1] * graph.n, order)
    assert not whole.aborted and A.is_independent(graph.adj, whole.chosen)
    assert whole.value == A.milp_optimum(graph.adj).value
    r = A.baker(graph.adj, 5, 0)
    assert r.size <= whole.value and A.meets_guarantee(r.size, whole.value, 5)


@pytest.mark.parametrize("net", NETS)
def test_every_shift_is_independent_avoids_the_deleted_layers_and_pieces_are_separated(net):
    graph = S.make_graph(net, 100, 4)
    root = S.root_vertex(graph, "center")
    k = 4
    r = A.baker(graph.adj, k, root)
    layer = r.layers
    for u in range(graph.n):                                            # BFS-Schichten: benachbarte Knoten unterscheiden sich um höchstens 1
        for v in graph.adj[u]:
            assert abs(layer[u] - layer[v]) <= 1
    for s in r.shifts:
        assert A.is_independent(graph.adj, s.chosen)
        assert all(layer[v] % k != s.shift for v in s.chosen)
        pieces = A.components(graph.adj, A.kept_vertices(layer, k, s.shift))
        assert len(pieces) == s.pieces
        owner = {v: i for i, comp in enumerate(pieces) for v in comp}
        for u in owner:
            for v in graph.adj[u]:
                if v in owner:
                    assert owner[u] == owner[v]                          # keine Kante zwischen verschiedenen Resten
        assert all(max(layer[v] for v in comp) - min(layer[v] for v in comp) <= k - 2 for comp in pieces)    # höchstens k − 1 aufeinanderfolgende Schichten


@pytest.mark.parametrize("net", NETS)
def test_the_average_over_the_shifts_of_an_optimal_solution_loses_at_most_one_kth(net):
    # Kern des Beweises: die gelöschten Klassen zerlegen jede unabhängige Menge I; ein i verliert höchstens |I| / k
    graph = S.make_graph(net, 50, 2)
    layer = A.bfs_layers(graph.adj, S.root_vertex(graph, "center"))
    order = X.min_fill_order(graph.adj)
    opt_set = X.max_weight_independent_set(graph.adj, [1] * graph.n, order, 6_000_000)
    assert not opt_set.aborted
    for k in (2, 3, 5):
        lost = [sum(1 for v in opt_set.chosen if layer[v] % k == i) for i in range(k)]
        assert sum(lost) == len(opt_set.chosen) and min(lost) * k <= len(opt_set.chosen)


def test_brute_force_oracle_by_hand(path7, star, grid3):
    assert brute_force_mis(path7) == 4 and brute_force_mis(star) == 4 and brute_force_mis(grid3) == 5
    assert edge_milp(path7) == 4 and edge_milp(grid3) == 5
