"""Abbildungen: Spuren der Karte (Schichtfarben, gelöschte Schicht, gewählte Knoten), Verschiebungen, Reihen; alle Achsen gesperrt."""

import bkr_algorithm as A
import bkr_constants as C
import bkr_evaluation as ev
import bkr_scenario as S
import bkr_visualization as V


def test_map_figure_traces_by_hand():
    g = S.make_grid(9, False)
    r = A.baker(g.adj, 2, 0)                                # beste Verschiebung 1: gelöscht werden die Schichten 1 und 3, gewählt 0, 2, 4, 6, 8
    fig = V.build_map(g, r.layers, 2, r.best, title="x")
    assert len(fig.data) == 4
    edges, nodes, deleted, chosen = fig.data
    assert edges.x.count(None) == 12 and len(nodes.x) == 9 and list(nodes.marker.color) == list(r.layers)
    assert sorted(zip(deleted.x, deleted.y)) == sorted(g.pos[v] for v in (1, 3, 5, 7)) and deleted.marker.symbol == "x"
    assert sorted(zip(chosen.x, chosen.y)) == sorted(g.pos[v] for v in (0, 2, 4, 6, 8)) and chosen.marker.color == C.COLOR_CHOSEN
    assert fig.layout.yaxis.scaleanchor == "x" and fig.layout.yaxis.constrain == "domain" and fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange


def test_map_figure_without_a_finished_shift_has_only_edges_and_layers():
    g = S.make_grid(9, False)
    r = A.baker(g.adj, 2, 0, cell_budget=1)
    assert len(V.build_map(g, r.layers, 2, r.best).data) == 2


def test_shifts_figure_by_hand():
    g = S.make_grid(9, False)
    r = A.baker(g.adj, 3, 0)
    fig = V.build_shifts(r.shifts, greedy=4, ils=5)
    bars = fig.data[0]
    assert list(bars.x) == ["0", "1", "2"] and list(bars.y) == [4, 4, 4] and bars.marker.color[0] == C.COLOR_CHOSEN and bars.marker.color[1] == C.COLOR_BAKER
    assert sorted(s.y0 for s in fig.layout.shapes) == [4, 5]
    full = V.build_shifts(r.shifts, 4, 5, opt=5, guarantee=2 / 3)
    assert sorted(round(s.y0, 3) for s in full.layout.shapes) == [3.333, 4, 5, 5]


def test_shifts_figure_leaves_aborted_shifts_empty():
    g = S.make_grid(9, False)
    r = A.baker(g.adj, 3, 0, cell_budget=1)
    assert list(V.build_shifts(r.shifts, 4, 5).data[0].y) == [None, None, None]


ROWS = [{"k": 2, "baker_quota": 0.775, "guarantee": 0.5, "greedy_quota": 0.907, "ils_quota": 0.992, "time": 0.0065, "bag": 3, "width_bound": 2},
        {"k": 3, "baker_quota": 0.841, "guarantee": 2 / 3, "greedy_quota": 0.907, "ils_quota": 0.992, "time": 0.025, "bag": 6, "width_bound": 5}]


def test_quality_time_and_width_figures_use_the_rows():
    q = V.build_quality(ROWS)
    by = {t.name: list(t.y) for t in q.data}
    assert by["Baker"] == [0.775, 0.841] and by["Greedy"] == [0.907, 0.907] and by["Lokalsuche"] == [0.992, 0.992] and by["Garantie 1 − 1/k"] == [0.5, 2 / 3]
    t = V.build_time(ROWS)
    assert list(t.data[0].y) == [6.5, 25.0] and list(t.data[0].text) == ["Beutel 3", "Beutel 6"] and t.layout.yaxis.type == "log"
    w = V.build_width(ROWS)
    by = {t.name: list(t.y) for t in w.data}
    assert by["Min-Fill (gemessen)"] == [2, 5] and by["3 (k − 1) − 1"] == [2, 5]


def test_sizes_special_and_dp_figures():
    rows = [{"n": 100, "baker_quota": 1.0, "greedy_quota": 0.84, "ils_quota": 1.0}, {"n": 800, "baker_quota": 0.94, "greedy_quota": 0.9, "ils_quota": 1.0}]
    s = V.build_sizes(rows)
    assert [t.name for t in s.data] == ["Baker", "Greedy", "Lokalsuche"] and list(s.data[0].x) == ["n = 100", "n = 800"] and list(s.data[0].y) == [1.0, 0.94]
    special = [{"net": "grid", "k": 2, "baker": 200, "greedy": 182, "ils": 200, "opt": 200}, {"net": "grid", "k": 3, "baker": 146, "greedy": 182, "ils": 200, "opt": 200},
               {"net": "thin", "k": 2, "baker": 115, "greedy": 142, "ils": 154, "opt": 155}]
    fig = V.build_special(special, "grid", C.NET_TYPES)
    assert list(fig.data[0].y) == [200, 146] and sorted(sh.y0 for sh in fig.layout.shapes) == [182, 200, 200]
    dp = V.build_dp([{"n": 50, "predicted": 8798, "bag": 10, "budget": 2_000_000}, {"n": 200, "predicted": 2.2e6, "bag": 19, "budget": 2_000_000}])
    assert list(dp.data[0].text) == ["Beutel 10", "Beutel 19"] and dp.layout.yaxis.type == "log" and dp.layout.shapes[0].y0 == 2_000_000
    assert V.num_bag(19) == "19" and V.num_bag(19.5) == "19,5"


def test_all_axes_are_locked():
    a = ev.analyse(ev.Settings("grid", 16, 3, "center", 1))
    figs = [V.build_quality(ROWS), V.build_time(ROWS), V.build_width(ROWS), V.build_shifts(a.baker.shifts, 1, 2), V.build_map(a.graph, a.baker.layers, 3, a.baker.best)]
    for fig in figs:
        assert fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange
