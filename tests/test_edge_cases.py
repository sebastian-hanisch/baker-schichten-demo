"""Randfälle: kleinste Graphen, k größer als die Zahl der Schichten, isolierte Knoten, vollständiger Graph, jede Netzart und jedes k an den Reglergrenzen."""

import pytest

import bkr_algorithm as A
import bkr_constants as C
import bkr_evaluation as ev
from conftest import adj_from_edges


def test_single_vertex():
    adj = adj_from_edges(1, [])
    r = A.baker(adj, 2, 0)
    assert [s.size for s in r.shifts] == [0, 1] and r.size == 1 and r.best.shift == 1


def test_isolated_vertices_are_one_layer_each_component():
    adj = adj_from_edges(5, [])
    assert A.bfs_layers(adj, 0) == (0,) * 5
    r = A.baker(adj, 2, 0)
    assert [s.size for s in r.shifts] == [0, 5] and r.size == 5


def test_complete_graph_has_one_independent_vertex():
    adj = adj_from_edges(4, [(i, j) for i in range(4) for j in range(i + 1, 4)])
    r = A.baker(adj, 2, 0)
    assert [s.size for s in r.shifts] == [1, 1] and r.size == 1 and r.best.shift == 0


def test_k_larger_than_the_height_solves_the_graph_exactly(path7, grid3):
    for adj, opt in ((path7, 4), (grid3, 5)):
        height = max(A.bfs_layers(adj, 0)) + 1
        r = A.baker(adj, height + 1, 0)
        assert r.size == opt and r.shifts[height].pieces == 1 and r.shifts[height].size == opt     # die Verschiebung ohne gelöschte Schicht ist ein einziger Rest


def test_a_disconnected_graph_is_covered_component_by_component():
    adj = adj_from_edges(6, [(0, 1), (1, 2), (3, 4)])
    r = A.baker(adj, 3, 0)
    assert A.is_independent(adj, r.best.chosen) and r.size >= 3
    assert A.meets_guarantee(r.size, 4, 3)                # größte Menge: {0, 2, 3, 5}


@pytest.mark.parametrize("net", list(C.NET_TYPES))
@pytest.mark.parametrize("root", list(C.ROOTS))
@pytest.mark.parametrize("k", [C.K_MIN, C.K_MAX])
@pytest.mark.parametrize("seed", [0, C.SEED_MAX])
def test_smallest_graphs_at_the_regler_bounds_meet_the_guarantee(net, root, k, seed):
    a = ev.analyse(ev.Settings(net, C.N_MIN, k, root, seed))
    opt = A.milp_optimum(a.graph.adj).value
    assert a.baker.aborted == 0 and A.is_independent(a.graph.adj, a.baker.best.chosen)
    assert A.meets_guarantee(a.baker_size, opt, k) and a.baker_size <= opt and a.greedy_size <= opt


def test_n_not_a_square_is_rounded_to_the_nearest_grid():
    assert ev.analyse(ev.Settings("grid", 17, 3, "center", 1)).graph.n == 16
    assert ev.analyse(ev.Settings("grid", 24, 3, "center", 1)).graph.n == 25


def test_the_largest_graph_with_a_small_k_runs_within_the_budget():
    a = ev.analyse(ev.Settings("delaunay", C.N_MAX, 3, "center", 1))
    assert a.graph.n == C.N_MAX and a.baker.aborted == 0 and A.is_independent(a.graph.adj, a.baker.best.chosen)


def test_a_graph_with_few_layers_and_a_large_k_does_not_break():
    a = ev.analyse(ev.Settings("grid_diag", 25, C.K_MAX, "center", 1))    
    height = a.baker.height
    assert height == 5 and a.baker.aborted == 0           # die Diagonalen laufen nur in einer Richtung: die Ecken sind 4 Schritte von der Mitte entfernt
    assert [s.pieces for s in a.baker.shifts][height:] == [1] * (C.K_MAX - height)
