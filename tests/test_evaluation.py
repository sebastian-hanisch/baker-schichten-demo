"""Auswertung: eine Analyse ist deterministisch (bis auf Zeiten), die Messreihen laufen über feste Pläne und liefern geordnete Mediane."""

import pytest

import bkr_algorithm as A
import bkr_constants as C
import bkr_evaluation as ev
import bkr_scenario as S


def test_default_settings_equal_the_default_constants():
    s = ev.Settings()
    assert (s.net, s.n, s.k, s.root, s.seed) == (C.DEFAULT_NET, C.DEFAULT_N, C.DEFAULT_K, C.DEFAULT_ROOT, C.DEFAULT_SEED)


def test_analyse_is_deterministic_in_everything_but_time():
    s = ev.Settings("delaunay", 120, 4, "center", 5)
    a, b = ev.analyse(s), ev.analyse(s)
    assert a.baker == b.baker and a.greedy == b.greedy and a.ils.size == b.ils.size and a.root == b.root
    assert a.graph == S.make_graph("delaunay", 120, 5) and a.baker_time > 0 and a.ils_time > 0


def test_analyse_uses_the_requested_root_and_k():
    a = ev.analyse(ev.Settings("grid", 9, 2, "center", 1))
    assert a.root == 4 and a.baker.k == 2 and a.baker.root == 4
    b = ev.analyse(ev.Settings("grid", 9, 2, "edge", 1))
    assert b.root == 6


def test_analysis_sizes_by_hand():
    a = ev.analyse(ev.Settings("grid", 9, 2, "edge", 1))                # Gitter 3 × 3, Wurzel unten links: Optimum 5
    assert a.baker_size == 5 and a.greedy_size >= 4 and a.ils_size == 5
    assert a.baker_size == a.baker.size and a.greedy_size == len(a.greedy) and a.ils_size == a.ils.size


def test_run_all_returns_all_methods():
    g = S.make_grid(9, False)
    baker, bt, greedy, ils, it = ev.run_all(g, 3, 0)
    assert baker.size == 4 and A.is_independent(g.adj, greedy) and ils.size == 5 and bt > 0 and it > 0


def test_cached_optimum_is_the_milp_value_and_is_cached():
    before = ev.cached_optimum.cache_info().hits
    first = ev.cached_optimum("grid", 16, 0)
    second = ev.cached_optimum("grid", 16, 0)
    assert first == second and first.value == 8 and first.proven
    assert ev.cached_optimum.cache_info().hits >= before + 1
    assert ev.optimum_for(ev.Settings("grid", 16, 3, "center", 0)) == first


def test_quality_series_rows():
    rows = ev.quality_series(n=40, ks=(2, 3, 4), seeds=C.SWEEP_SEEDS[:3])
    assert [r["k"] for r in rows] == [2, 3, 4] and all(r["plans"] == 3 and r["n"] == 40 for r in rows)
    assert all(r["meets"] == r["finished"] == 3 and r["opt_proven"] == 3 and r["aborted"] == 0 for r in rows)
    assert all(r["baker"] <= r["opt"] and r["greedy"] <= r["opt"] and r["ils"] <= r["opt"] for r in rows)
    assert all(0 < r["baker_quota"] <= 1 and r["guarantee"] <= r["baker_quota"] for r in rows)
    assert [r["guarantee"] for r in rows] == pytest.approx([0.5, 2 / 3, 0.75]) and [r["width_bound"] for r in rows] == [2, 5, 8]
    assert rows[0]["bag"] <= rows[1]["bag"] <= rows[2]["bag"]


def test_size_series_rows_and_the_optimum_limit():
    rows = ev.size_series(sizes=(60, C.OPT_MAX_N + 100), k=3, seeds=C.SWEEP_SEEDS[:1])
    assert [r["n"] for r in rows] == [60, C.OPT_MAX_N + 100] and rows[0]["opt"] is not None and rows[1]["opt"] is None
    assert rows[1]["known"] >= rows[1]["ils"] and rows[1]["baker_quota"] <= 1 and rows[0]["ils_quota"] <= 1


def test_special_series_rows():
    rows = ev.special_series(side=8, ks=(2, 3))
    assert [(r["net"], r["k"]) for r in rows] == [("grid_diag", 2), ("grid_diag", 3), ("grid", 2), ("grid", 3), ("thin", 2), ("thin", 3)]
    assert all(r["meets"] and r["n"] == 64 for r in rows)
    grid = [r for r in rows if r["net"] == "grid"]
    assert grid[0]["opt"] == 32 and grid[0]["baker"] == 32                      # k = 2 trifft die Parität des bipartiten Gitters


def test_dp_series_rows():
    rows = ev.dp_series(sizes=(30, 200), seeds=C.SWEEP_SEEDS[:2], budget=1_000_000)
    assert [r["n"] for r in rows] == [30, 200] and rows[0]["aborted"] == 0 and rows[1]["aborted"] == 2
    assert rows[1]["bag"] > rows[0]["bag"] and rows[1]["predicted"] > rows[0]["predicted"] and rows[0]["budget"] == 1_000_000
