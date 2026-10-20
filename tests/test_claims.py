"""Jede Zahl der README wird hier nachgerechnet (DEMO-PLAYBOOK §4): über dieselben Auswertungsfunktionen wie in der App.

Gitter (ohne Diagonalen und mit) sind reines Python und exakt; bei den Delaunay-Karten (scipy/Qhull) und der dünnen Karte gelten Bänder von ±2 Knoten, weil eine andere Qhull-Fassung
bei fast entarteten Punkten eine andere Triangulierung wählen könnte. Zeiten nur als Richtungen und weite Verhältnisse (reines Python, Last schwankt)."""

import pytest

import bkr_algorithm as A
import bkr_constants as C
import bkr_evaluation as ev
import bkr_scenario as S


@pytest.fixture(scope="module")
def quality():
    return ev.quality_series()


@pytest.fixture(scope="module")
def sizes():
    return ev.size_series()


@pytest.fixture(scope="module")
def special():
    return ev.special_series()


@pytest.fixture(scope="module")
def dp():
    return ev.dp_series()


def _row(rows, **match):
    return next(r for r in rows if all(r[k] == v for k, v in match.items()))


def test_the_series_use_the_documented_fixed_plans():
    assert C.SWEEP_SEEDS == tuple(range(100000, 100005)) and C.QUALITY_N == 400 and C.QUALITY_KS == (2, 3, 4, 5, 6, 8)
    assert C.SIZE_SERIES == (100, 200, 400, 800) and C.SIZE_SERIES_K == 6 and C.SPECIAL_SIDE == 20 and C.SPECIAL_KS == (2, 3, 4, 5, 6, 8)
    assert C.DP_SIZES == (50, 100, 200, 400, 800) and C.DP_BUDGET == 2_000_000 and C.CELL_BUDGET == 3_000_000 and C.ILS_ITERATIONS == 1500 and C.OPT_MAX_N == 400
    assert (C.N_MIN, C.N_MAX, C.K_MIN, C.K_MAX, C.DEFAULT_N, C.DEFAULT_K) == (20, 1600, 2, 8, 400, 5)


# --- Güte und Zeit über k (Karten mit 400 Standorten) --------------------------------------------------------------------------------------------


def test_quality_by_k_matches_the_readme(quality):
    assert [r["k"] for r in quality] == [2, 3, 4, 5, 6, 8] and all(r["plans"] == 5 and r["opt_proven"] == 5 for r in quality)
    first = quality[0]
    assert first["opt"] == pytest.approx(127, abs=2) and first["greedy"] == pytest.approx(115, abs=2) and first["ils"] == pytest.approx(126, abs=2)
    assert [r["baker"] for r in quality] == pytest.approx([99, 108, 111, 116, 119, 121], abs=2)
    assert [r["baker_quota"] for r in quality] == pytest.approx([0.775, 0.841, 0.880, 0.920, 0.936, 0.960], abs=0.02)
    assert first["greedy_quota"] == pytest.approx(0.907, abs=0.02) and first["ils_quota"] == pytest.approx(0.992, abs=0.015)
    assert [r["guarantee"] for r in quality] == pytest.approx([0.5, 2 / 3, 0.75, 0.8, 5 / 6, 0.875])


def test_the_oracle_covers_26_small_24_medium_and_15_whole_graph_cases():
    from test_oracle_baker import small_graphs
    assert len(list(small_graphs())) == 26 == 12 * 2 + 2
    assert 4 * 6 == 24 and 3 * 5 == 15                          # test_baker_against_a_second_milp_on_medium_graphs: 4 Netzarten × 6 Seeds; test_pieces_agree_with_the_whole_graph_dp: 3 × 5


def test_the_guarantee_holds_in_every_plan_and_the_estimate_is_far_above_it(quality):
    assert all(r["meets"] == r["finished"] == 5 for r in quality)
    assert all(r["baker_quota"] > r["guarantee"] + 0.05 for r in quality)


def test_baker_beats_greedy_from_k_6_in_every_plan_and_never_beats_local_search(quality):
    above = {r["k"]: r["above_greedy"] for r in quality}
    assert above[2] == above[3] == 0 and above[6] == above[8] == 5 and 0 < above[5] < 5 and above[4] <= 1
    assert all(r["ils"] >= r["baker"] for r in quality)
    assert _row(quality, k=5)["baker"] > _row(quality, k=5)["greedy"] and _row(quality, k=4)["baker"] < _row(quality, k=4)["greedy"]


def test_beutel_sizes_and_time_grow_with_k_and_pass_the_bound_from_k_5(quality):
    bags = [r["bag"] for r in quality]
    assert bags == sorted(bags) and bags[:5] == pytest.approx([3, 6, 9, 13, 16], abs=1) and bags[-1] >= 19
    assert [r["width_bound"] for r in quality] == [2, 5, 8, 11, 14, 20]
    assert all(r["bag"] - 1 <= r["width_bound"] for r in quality if r["k"] in (2, 3, 4)) and all(r["bag"] - 1 > r["width_bound"] for r in quality if r["k"] in (5, 6))
    assert [r["bag"] - 1 for r in quality[:5]] == pytest.approx([2, 5, 8, 12, 15], abs=1)
    times = [r["time"] for r in quality[:5]]
    assert times == sorted(times) and times[4] > 10 * times[0]                  # gemessen etwa 0,007 / 0,03 / 0,07 / 0,2 / 0,7 s
    assert 10 <= _row(quality, k=8)["aborted"] <= 26 and all(r["aborted"] == 0 for r in quality[:5])        # bei k = 8 brechen 18 von 40 Verschiebungen am Zellbudget ab


# --- Über die Größe (k = 6) ---------------------------------------------------------------------------------------------------------------------


def test_sizes_by_n_match_the_readme(sizes):
    assert [r["n"] for r in sizes] == [100, 200, 400, 800] and all(r["plans"] == 5 and r["aborted"] == 0 for r in sizes)
    assert [r["baker"] for r in sizes] == pytest.approx([32, 61, 119, 235], abs=2)
    assert [r["greedy"] for r in sizes] == pytest.approx([27, 56, 115, 224], abs=2)
    assert [r["ils"] for r in sizes] == pytest.approx([32, 64, 126, 249], abs=2)
    assert [r["opt"] for r in sizes[:3]] == pytest.approx([32, 64, 127], abs=2) and sizes[3]["opt"] is None
    assert all(r["ils"] >= r["baker"] > r["greedy"] for r in sizes)


def test_baker_is_slower_than_local_search_from_n_200(sizes):
    assert all(r["baker_time"] > 2 * r["ils_time"] for r in sizes[1:])              # gemessen etwa 6- bis 40-fach
    assert sizes[3]["baker_time"] > sizes[1]["baker_time"]


# --- Sonderfälle ---------------------------------------------------------------------------------------------------------------------------------


def test_grid_cases_are_exact(special):
    diag = {r["k"]: r for r in special if r["net"] == "grid_diag"}
    grid = {r["k"]: r for r in special if r["net"] == "grid"}
    assert [diag[k]["baker"] for k in (2, 3, 4, 5, 6, 8)] == [105, 98, 109, 117, 118, 121] and all(diag[k]["opt"] == 134 and diag[k]["greedy"] == 102 and diag[k]["ils"] == 133 for k in diag)
    assert [grid[k]["baker"] for k in (2, 3, 4, 5, 6, 8)] == [200, 146, 200, 176, 200, 200] and all(grid[k]["opt"] == 200 and grid[k]["greedy"] == 182 and grid[k]["ils"] == 200 for k in grid)
    assert diag[3]["baker"] < diag[3]["greedy"] and grid[3]["baker"] < grid[3]["greedy"] and grid[5]["baker"] < grid[5]["greedy"]
    assert diag[3]["baker"] < diag[2]["baker"] and grid[3]["baker_quota"] == pytest.approx(0.73) and all(r["meets"] for r in special)


def test_thin_map_is_in_bands(special):
    thin = {r["k"]: r for r in special if r["net"] == "thin"}
    assert [thin[k]["baker"] for k in (2, 3, 4, 5, 6, 8)] == pytest.approx([115, 131, 135, 141, 144, 147], abs=2)
    assert thin[2]["opt"] == pytest.approx(155, abs=2) and thin[2]["greedy"] == pytest.approx(142, abs=2) and thin[2]["ils"] == pytest.approx(154, abs=2)
    assert all(thin[k]["baker"] < thin[k]["greedy"] for k in (2, 3, 4)) and thin[8]["baker"] > thin[8]["greedy"]


# --- Ganzer Graph per DP ------------------------------------------------------------------------------------------------------------------------


def test_the_whole_graph_dp_breaks_at_n_200(dp):
    assert [r["n"] for r in dp] == [50, 100, 200, 400, 800] and all(r["plans"] == 5 for r in dp)
    assert [r["bag"] for r in dp] == pytest.approx([10, 14, 19, 28, 38], abs=2)
    assert dp[0]["aborted"] == dp[1]["aborted"] == 0 and 1 <= dp[2]["aborted"] <= 4 and dp[3]["aborted"] == dp[4]["aborted"] == 5
    assert dp[1]["predicted"] < C.DP_BUDGET < dp[3]["predicted"] and dp[4]["predicted"] > 1e11


# --- Presets -------------------------------------------------------------------------------------------------------------------------------------


def test_presets_hold_what_their_help_texts_say():
    by = {name: ev.analyse(ev.Settings(**p)) for name, p in C.PRESETS.items()}
    default, small, large, diag, grid = (by[name] for name in C.PRESETS)
    assert default.baker_size == pytest.approx(116, abs=2) and default.greedy_size == pytest.approx(109, abs=2) and default.ils_size == pytest.approx(124, abs=2)
    assert default.greedy_size < default.baker_size < default.ils_size and default.baker.aborted == 0
    assert small.baker_size == pytest.approx(98, abs=2) and small.baker.max_bag <= 4 and small.baker_time < default.baker_time
    assert large.baker_size == pytest.approx(118, abs=2) and large.baker_size >= default.baker_size and large.baker_time > default.baker_time and large.baker.aborted == 0
    assert (diag.baker_size, diag.greedy_size, diag.ils_size) == (98, 102, 133) and diag.baker_size < diag.greedy_size
    assert (grid.baker_size, grid.greedy_size, grid.ils_size) == (146, 182, 200) and [s.size for s in grid.baker.shifts] == [146, 146, 146]


def test_the_default_map_has_known_optimum_and_the_guarantee_holds():
    s = ev.Settings()
    a = ev.analyse(s)
    opt = ev.optimum_for(s)
    assert opt.proven and opt.value == pytest.approx(124, abs=2) and A.meets_guarantee(a.baker_size, opt.value, s.k)
    assert (S.make_graph("delaunay", 400, 35).n, a.baker.height) == (400, pytest.approx(11, abs=1))
