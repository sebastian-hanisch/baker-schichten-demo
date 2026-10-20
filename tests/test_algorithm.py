"""Einheiten des Kerns an handgerechneten Mini-Graphen (eine Regel = eine Funktion)."""

import pytest

import bkr_algorithm as A
from conftest import adj_from_edges


# --- Schichten und Reste -----------------------------------------------------------------------------------------------------------------------


def test_bfs_layers_by_hand(path7, star, grid3):
    assert A.bfs_layers(path7, 0) == (0, 1, 2, 3, 4, 5, 6)
    assert A.bfs_layers(path7, 3) == (3, 2, 1, 0, 1, 2, 3)
    assert A.bfs_layers(star, 0) == (0, 1, 1, 1, 1)
    assert A.bfs_layers(star, 1) == (1, 0, 2, 2, 2)
    assert A.bfs_layers(grid3, 0) == (0, 1, 2, 1, 2, 3, 2, 3, 4)


def test_bfs_layers_start_every_other_component_at_zero():
    adj = adj_from_edges(5, [(0, 1), (2, 3)])
    assert A.bfs_layers(adj, 0) == (0, 1, 0, 1, 0)
    assert A.bfs_layers(adj, 3) == (0, 1, 1, 0, 0)       # Wurzel 3: Komponente {2, 3}; danach {0, 1} ab Knoten 0, dann der einzelne Knoten 4


def test_kept_vertices_delete_every_kth_layer(path7):
    layer = A.bfs_layers(path7, 0)
    assert A.kept_vertices(layer, 3, 0) == frozenset({1, 2, 4, 5})
    assert A.kept_vertices(layer, 3, 1) == frozenset({0, 2, 3, 5, 6})
    assert A.kept_vertices(layer, 2, 1) == frozenset({0, 2, 4, 6})


def test_components_of_the_kept_set_by_hand(path7):
    assert A.components(path7, frozenset({1, 2, 4, 5})) == [[1, 2], [4, 5]]
    assert A.components(path7, frozenset({0, 2, 3, 5, 6})) == [[0], [2, 3], [5, 6]]
    assert A.components(path7, frozenset()) == []
    assert A.components(path7, frozenset(range(7))) == [list(range(7))]


def test_solve_piece_on_a_path_piece(path7):
    piece = A.solve_piece(path7, [2, 3, 4, 5])           # Weg mit 4 Knoten: größte unabhängige Menge hat 2 Knoten
    assert len(piece.chosen) == 2 and not piece.aborted and piece.max_bag >= 2
    assert A.is_independent(path7, piece.chosen) and set(piece.chosen) <= {2, 3, 4, 5}


def test_solve_piece_aborts_at_the_cell_budget(path7):
    piece = A.solve_piece(path7, list(range(7)), cell_budget=1)
    assert piece.aborted and piece.chosen == () and piece.cells == 0 and piece.predicted > 1


def test_solve_piece_relabels_to_the_original_vertices(grid3):
    piece = A.solve_piece(grid3, [4, 5, 7, 8])           # Quadrat 4 – 5 – 8 – 7: zwei gegenüberliegende Knoten
    assert sorted(piece.chosen) in ([4, 8], [5, 7])


# --- Baker -------------------------------------------------------------------------------------------------------------------------------------


def test_baker_on_the_path_by_hand(path7):
    r2 = A.baker(path7, 2, 0)
    assert [s.size for s in r2.shifts] == [3, 4]          # Verschiebung 0: Schichten 0, 2, 4, 6 gelöscht, 3 Einzelknoten; Verschiebung 1: 4 Einzelknoten
    assert r2.best.shift == 1 and r2.size == 4 and r2.best.chosen == (0, 2, 4, 6)
    r3 = A.baker(path7, 3, 0)
    assert [s.size for s in r3.shifts] == [2, 3, 3]
    assert r3.best.shift == 1                              # Gleichstand: die kleinere Verschiebung
    assert [s.pieces for s in r3.shifts] == [2, 3, 3]


def test_baker_on_the_star_by_hand(star):
    r = A.baker(star, 2, 0)
    assert [s.size for s in r.shifts] == [4, 1] and r.best.shift == 0 and r.best.chosen == (1, 2, 3, 4)


def test_baker_on_the_three_by_three_grid_by_hand(grid3):
    r2 = A.baker(grid3, 2, 0)
    assert [s.size for s in r2.shifts] == [4, 5] and r2.best.chosen == (0, 2, 4, 6, 8)
    r3 = A.baker(grid3, 3, 0)
    assert [s.size for s in r3.shifts] == [4, 4, 4] and r3.best.shift == 0
    assert [s.pieces for s in r3.shifts] == [2, 2, 2]
    assert r3.height == 5


def test_baker_result_properties(grid3):
    r = A.baker(grid3, 3, 0)
    assert r.k == 3 and r.root == 0 and r.layers == (0, 1, 2, 1, 2, 3, 2, 3, 4)
    assert r.size == 4 and r.aborted == 0 and r.cells == sum(s.cells for s in r.shifts) > 0
    assert r.max_bag == max(s.max_bag for s in r.shifts)


def test_baker_k_one_deletes_everything(path7):
    r = A.baker(path7, 1, 0)
    assert r.size == 0 and r.best.chosen == () and r.best.pieces == 0


def test_baker_aborts_shifts_at_the_cell_budget(path7):
    r = A.baker(path7, 3, 0, cell_budget=1)
    assert r.best is None and r.size is None and r.aborted == 3 and all(s.chosen == () and s.size is None for s in r.shifts)


def test_baker_with_a_partial_abort_keeps_the_finished_shifts():
    # zwei Wege (2 und 7 Knoten), k = 8: nur Verschiebung 7 (keine Schicht gelöscht) hat den ganzen 7er-Weg als Rest; das Zellbudget unter seiner Vorhersage bricht genau diese Verschiebung ab
    adj = adj_from_edges(9, [(0, 1)] + [(i, i + 1) for i in range(2, 8)])
    budget = A.solve_piece(adj, list(range(2, 9))).predicted - 1
    full, tight = A.baker(adj, 8, 0), A.baker(adj, 8, 0, cell_budget=budget)
    assert full.aborted == 0 and tight.aborted == 1 and tight.shifts[7].aborted and tight.shifts[7].size is None
    assert tight.best is not None and tight.best.shift != 7 and tight.size == full.size == 5


def test_baker_is_deterministic(grid3):
    assert A.baker(grid3, 3, 4) == A.baker(grid3, 3, 4)


# --- Güte, Schranke, Hilfen ------------------------------------------------------------------------------------------------------------------


def test_guarantee_by_hand():
    assert A.guarantee_ratio(2) == 0.5 and A.guarantee_ratio(4) == 0.75
    assert A.meets_guarantee(2, 4, 2) and not A.meets_guarantee(1, 4, 2)         # 2 ≥ ½ · 4, 1 < 2
    assert A.meets_guarantee(3, 4, 3) and not A.meets_guarantee(2, 4, 3)         # 3 ≥ 8/3, 2 < 8/3
    assert A.meets_guarantee(0, 0, 5)


def test_width_bound_is_three_k_minus_one_minus_one():
    assert [A.width_bound(k) for k in (2, 3, 4, 5, 6, 8)] == [2, 5, 8, 11, 14, 20]


def test_is_independent_by_hand(grid3):
    assert A.is_independent(grid3, [0, 2, 4, 6, 8]) and A.is_independent(grid3, [])
    assert not A.is_independent(grid3, [0, 1]) and not A.is_independent(grid3, [4, 7])


def test_triangle_rows_by_hand():
    adj = adj_from_edges(4, [(0, 1), (0, 2), (1, 2), (2, 3)])
    assert A.triangle_rows(adj) == [[0, 1, 2], [2, 3]]
    assert A.triangle_rows(adj_from_edges(3, [])) == []
    assert A.triangle_rows(adj_from_edges(3, [(0, 1), (1, 2)])) == [[0, 1], [1, 2]]


def test_milp_optimum_by_hand(path7, star, grid3):
    assert A.milp_optimum(path7).value == 4 and A.milp_optimum(path7).proven
    assert A.milp_optimum(star).value == 4
    assert A.milp_optimum(grid3).value == 5
    empty = A.milp_optimum(adj_from_edges(3, []))
    assert empty.value == 3 and empty.proven
    triangle = A.milp_optimum(adj_from_edges(3, [(0, 1), (0, 2), (1, 2)]))
    assert triangle.value == 1


@pytest.mark.parametrize("k", [2, 3, 4])
def test_baker_meets_its_guarantee_on_the_small_graphs(path7, star, grid3, k):
    for adj, opt in ((path7, 4), (star, 4), (grid3, 5)):
        assert A.meets_guarantee(A.baker(adj, k, 0).size, opt, k)
