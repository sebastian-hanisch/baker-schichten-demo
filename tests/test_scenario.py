"""Szenario: Gitter, Karten, dünne Karten, Wurzelwahl; die Graphen sind planar (Euler-Schranke) und deterministisch."""

import pytest

import bkr_constants as C
import bkr_scenario as S


def test_grid_side_is_the_rounded_square_root_with_a_minimum_of_two():
    assert [S.grid_side(n) for n in (1, 4, 9, 10, 15, 16, 400)] == [2, 2, 3, 3, 4, 4, 20]


def test_grid_by_hand_for_three_by_three():
    g = S.make_grid(9, False)
    assert (g.n, g.m) == (9, 12) and g.name == "Gitter 3 × 3"
    assert g.edges()[:4] == [(0, 1), (0, 3), (1, 2), (1, 4)]
    assert g.pos[0] == (0.0, 0.0) and g.pos[2] == (2.0, 0.0) and g.pos[6] == (0.0, -2.0)
    d = S.make_grid(9, True)
    assert d.m == 16 and (0, 4) in d.edges() and d.name == "Gitter 3 × 3 mit Diagonalen"


def test_grid_edge_counts():
    for k in (2, 3, 7, 20):
        assert S.make_grid(k * k, False).m == 2 * k * (k - 1)
        assert S.make_grid(k * k, True).m == 2 * k * (k - 1) + (k - 1) ** 2


def test_delaunay_is_deterministic_planar_and_triangulated():
    a, b = S.make_delaunay(80, 3), S.make_delaunay(80, 3)
    assert a == b and a != S.make_delaunay(80, 4)
    assert a.n == 80 and a.m <= 3 * a.n - 6 and a.m >= 2 * a.n - 5              # Triangulierung: zwischen 2n − 3 − h und 3n − 3 − h Kanten
    assert all(u < v for u, v in a.edges()) and all(len(x) >= 2 for x in a.adj)
    assert a.name == "Karte mit 80 Standorten"


def test_thin_keeps_80_percent_of_the_edges_of_the_same_map():
    base, thin = S.make_delaunay(100, 5), S.make_thin(100, 5)
    assert thin.pos == base.pos and thin.m == round(0.8 * base.m)
    assert set(thin.edges()) <= set(base.edges())
    assert S.make_thin(100, 5) == thin and S.make_thin(100, 6) != thin


def test_make_graph_dispatches_and_rejects_unknown():
    assert S.make_graph("delaunay", 30, 1) == S.make_delaunay(30, 1)
    assert S.make_graph("thin", 30, 1) == S.make_thin(30, 1)
    assert S.make_graph("grid", 16, 1) == S.make_grid(16, False)
    assert S.make_graph("grid_diag", 16, 1) == S.make_grid(16, True)
    with pytest.raises(ValueError):
        S.make_graph("ring", 16, 1)


def test_grid_ignores_the_seed():
    assert S.make_graph("grid", 25, 1) == S.make_graph("grid", 25, 2)


def test_root_vertex_by_hand():
    g = S.make_grid(9, False)
    assert S.root_vertex(g, "center") == 4              # Mitte des 3 × 3-Gitters
    assert S.root_vertex(g, "edge") == 6                # linke Spalte, bei Gleichstand das kleinere y (unterste Zeile)
    with pytest.raises(ValueError):
        S.root_vertex(g, "oben")


def test_root_vertex_center_is_nearest_to_the_centroid_and_edge_is_leftmost():
    g = S.make_delaunay(120, 7)
    xs, ys = [p[0] for p in g.pos], [p[1] for p in g.pos]
    cx, cy = sum(xs) / g.n, sum(ys) / g.n
    c = S.root_vertex(g, "center")
    assert all((xs[c] - cx) ** 2 + (ys[c] - cy) ** 2 <= (xs[v] - cx) ** 2 + (ys[v] - cy) ** 2 for v in range(g.n))
    assert xs[S.root_vertex(g, "edge")] == min(xs)


def test_constants_roots_and_nets_match_the_scenario():
    assert set(C.NET_TYPES) == {"delaunay", "thin", "grid_diag", "grid"} and set(C.ROOTS) == {"center", "edge"}
    for net in C.NET_TYPES:
        S.make_graph(net, C.N_MIN, 1)
