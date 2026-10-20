"""Urteile sind reine Funktionen: jede Zahl im Text wird an handgesetzten Werten geprüft; Art (success/info/warning) und Schwellen ebenfalls."""

import bkr_algorithm as A
import bkr_constants as C
import bkr_evaluation as ev
import bkr_scenario as S
import bkr_search as Q


def fake(sizes, greedy, ils, k=5, aborted=(), baker_time=0.2, ils_time=0.04):
    """Eine Analyse mit handgesetzten Größen je Verschiebung (abgebrochene ohne Lösung), Greedy- und Lokalsuche-Größe und Zeiten."""
    shifts = tuple(A.Shift(i, () if i in aborted else tuple(range(s)), 2, 100, 5, i in aborted) for i, s in enumerate(sizes))
    done = [s for s in shifts if not s.aborted]
    best = max(done, key=lambda s: (len(s.chosen), -s.shift)) if done else None
    graph = S.make_grid(16, False)
    baker = A.BakerResult(k, 0, (0,) * graph.n, shifts, best)
    return ev.Analysis(ev.Settings("grid", 16, k), graph, 0, baker, baker_time, tuple(range(greedy)), Q.SearchResult((), ils, {}, 0, C.ILS_ITERATIONS, greedy), ils_time)


def test_num_percent_and_ms_text_use_german_format():
    assert ev.num(1234567) == "1.234.567" and ev.num(3.14159, 2) == "3,14" and ev.num(0) == "0"
    assert ev.percent(0.9134) == "91,3 %" and ev.percent(1) == "100,0 %"
    assert ev.ms_text(0.0021) == "2,1 ms" and ev.ms_text(1.5) == "1,50 s" and ev.ms_text(0.999) == "999,0 ms"
    assert ev.plural(1, "Phase", "Phasen") == "1 Phase" and ev.plural(0, "Phase", "Phasen") == "0 Phasen"


def test_baker_verdict_info_when_local_search_is_better():
    kind, text = ev.verdict_baker(fake([110, 116, 112, 109, 111], 109, 124))
    assert kind == "info"
    for part in ("k = 5", "beste Verschiebung 1", "**116**", "in 200,0 ms", "Greedy 109", "Lokalsuche 124 in 40,0 ms", "mindestens 80,0 % des Optimums", "Die Lokalsuche ist besser."):
        assert part in text, part


def test_baker_verdict_success_when_baker_beats_greedy_and_matches_local_search():
    kind, text = ev.verdict_baker(fake([110, 116, 112, 109, 111], 109, 116))
    assert kind == "success" and "Die Lokalsuche ist besser" not in text


def test_baker_verdict_warning_when_greedy_is_at_least_as_good():
    for greedy in (116, 120):
        kind, text = ev.verdict_baker(fake([110, 116, 112, 109, 111], greedy, 124))
        assert kind == "warning" and "Greedy ist mindestens so gut" in text


def test_baker_verdict_warning_when_every_shift_aborts():
    kind, text = ev.verdict_baker(fake([0, 0, 0], 100, 110, k=3, aborted=(0, 1, 2)))
    assert kind == "warning" and "Alle 3 Verschiebungen brechen ab" in text and "3.000.000 Tabellenzellen" in text and "größter Beutel 5" in text


def test_baker_verdict_mentions_a_partial_abort():
    kind, text = ev.verdict_baker(fake([110, 116, 112, 109, 111], 109, 124, aborted=(2,)))
    assert "1 Verschiebung brach beim Zellbudget ab." in text


def test_baker_verdict_with_the_optimum():
    kind, text = ev.verdict_baker(fake([110, 116, 112, 109, 111], 109, 124), A.Optimum(127, True, 3.0))
    assert "Optimum 127: Baker erreicht **91,3 %**, Greedy 85,8 %, Lokalsuche 97,6 %." in text and "nicht bewiesen" not in text
    kind, text = ev.verdict_baker(fake([110, 116, 112, 109, 111], 109, 124), A.Optimum(127, False, 60.0))
    assert "Optimum 127 (beste gefundene Größe, nicht bewiesen)" in text
    assert "Optimum" not in ev.verdict_baker(fake([110, 116, 112, 109, 111], 109, 124), A.Optimum(None, False, 60.0))[1].replace("des Optimums", "")


def test_baker_verdict_boundaries_between_greedy_and_local_search():
    assert ev.verdict_baker(fake([116], 115, 116, k=1))[0] == "success"          # genau gleich der Lokalsuche zählt als nicht schlechter
    assert ev.verdict_baker(fake([116], 116, 116, k=1))[0] == "warning"          # gleich Greedy ist nicht darüber
    assert ev.verdict_baker(fake([116], 115, 117, k=1))[0] == "info"


def test_shifts_verdict_by_hand():
    kind, text = ev.verdict_shifts(fake([110, 116, 112, 109, 111], 109, 124))
    assert kind == "info"
    for part in ("5 fertigen Verschiebungen", "**109 bis 116**", "beste ist Verschiebung 1 (116)", "schlechteste Verschiebung 3 (109)"):
        assert part in text, part
    assert "4 fertigen Verschiebungen" in ev.verdict_shifts(fake([110, 116, 112, 109, 111], 109, 124, aborted=(0,)))[1]
    assert ev.verdict_shifts(fake([0, 0], 5, 5, k=2, aborted=(0, 1))) == ("warning", "Keine Verschiebung wurde fertig.")


def test_shifts_verdict_takes_the_smaller_shift_on_ties():
    text = ev.verdict_shifts(fake([100, 100, 100], 90, 100, k=3))[1]
    assert "liefern alle **100** Knoten" in text and "beste ist Verschiebung 0 (100) (bei Gleichstand die kleinste)." in text and "schlechteste" not in text
    two = ev.verdict_shifts(fake([100, 100, 90], 90, 100, k=3))[1]
    assert "**90 bis 100**" in two and "beste ist Verschiebung 0 (100), die schlechteste Verschiebung 2 (90)." in two


def quality_row(k, baker, quota, guarantee, **kw):
    base = {"k": k, "n": 400, "plans": 5, "baker": baker, "greedy": 115, "ils": 126, "baker_quota": quota, "greedy_quota": 0.907, "ils_quota": 0.992, "guarantee": guarantee,
            "meets": 5, "finished": 5, "aborted": 0}
    base.update(kw)
    return base


def quality_rows():
    return [quality_row(2, 99, 0.775, 0.5), quality_row(3, 108, 0.841, 2 / 3), quality_row(4, 111, 0.88, 0.75), quality_row(5, 116, 0.92, 0.8)]


def test_quality_verdict_by_hand():
    kind, text = ev.verdict_quality(quality_rows())
    assert kind == "success"
    for part in ("n = 400, 5 Pläne (Mediane)", "**77,5 %** des Optimums bei k = 2", "**92,0 %** bei k = 5", "Garantie 50,0 % und 80,0 %", "Greedy 90,7 %", "Lokalsuche 99,2 %",
                 "Baker liegt ab k = 5 über Greedy", "die Lokalsuche ist in allen Zeilen mindestens so gut", "Die Garantie hält in jedem fertigen Plan."):
        assert part in text, part


def test_quality_verdict_variants():
    rows = quality_rows()
    for r in rows:
        r["baker"] = 110
    kind, text = ev.verdict_quality(rows)
    assert kind == "info" and "Baker liegt in keiner Zeile über Greedy" in text
    rows = quality_rows()
    rows[1]["ils"] = 100
    assert "die Lokalsuche liegt nicht in allen Zeilen vorn" in ev.verdict_quality(rows)[1]
    rows = quality_rows()
    rows[2]["meets"] = 4
    kind, text = ev.verdict_quality(rows)
    assert kind == "info" and "Die Garantie wurde in mindestens einem Plan verfehlt." in text
    rows = quality_rows()
    rows[3]["aborted"], rows[2]["aborted"] = 2, 1
    assert "3 Verschiebungen brachen beim Zellbudget ab (die Garantie gilt nur, wenn alle k Verschiebungen fertig werden)." in ev.verdict_quality(rows)[1]
    rows[2]["aborted"], rows[3]["aborted"] = 1, 0
    assert "1 Verschiebung brach beim Zellbudget ab" in ev.verdict_quality(rows)[1]


def test_quality_verdict_over_greedy_threshold_is_strict():
    rows = quality_rows()
    rows[3]["baker"] = 115
    assert "keiner Zeile über Greedy" in ev.verdict_quality(rows)[1]
    rows[3]["baker"] = 116
    assert "ab k = 5 über Greedy" in ev.verdict_quality(rows)[1]


def test_width_verdict_by_hand():
    rows = [{"k": 3, "bag": 6, "width_bound": 5}, {"k": 4, "bag": 9, "width_bound": 8}, {"k": 5, "bag": 13, "width_bound": 11}]
    kind, text = ev.verdict_width(rows)
    assert kind == "info"
    assert "k = 3: Breite 5 gegen 5, k = 4: Breite 8 gegen 8, k = 5: Breite 12 gegen 11." in text
    assert "Ab k = 5 liegt die Heuristik über der Schranke" in text
    rows[2]["bag"] = 12
    assert "Die Heuristik bleibt in allen Zeilen unter der Schranke." in ev.verdict_width(rows)[1]


def test_sizes_verdict_by_hand():
    rows = [{"n": 100, "k": 6, "plans": 5, "baker": 32, "ils": 32, "greedy": 27, "baker_time": 0.05, "ils_time": 0.04},
            {"n": 800, "k": 6, "plans": 5, "baker": 235, "ils": 249, "greedy": 224, "baker_time": 1.78, "ils_time": 0.044}]
    kind, text = ev.verdict_sizes(rows)
    assert kind == "info"
    for part in ("k = 6, n = 100 bis 800 (5 Pläne, Mediane)", "bei n = 800 findet Baker 235 Knoten in 1,78 s", "die Lokalsuche 249 in 44,0 ms", "Greedy 224", "Die Lokalsuche ist in jeder Größe besser."):
        assert part in text, part
    rows[0]["ils"] = 30
    assert "nicht in jeder Größe besser" in ev.verdict_sizes(rows)[1]


def special_rows():
    return [{"net": "grid_diag", "k": 2, "baker": 105, "greedy": 102, "meets": True}, {"net": "grid_diag", "k": 3, "baker": 98, "greedy": 102, "meets": True},
            {"net": "grid", "k": 3, "baker": 146, "greedy": 182, "meets": True}]


def test_special_verdict_by_hand():
    kind, text = ev.verdict_special(special_rows())
    assert kind == "warning"
    assert "Gitter mit Diagonalen, k = 3 (98 gegen Greedy 102); Gitter (bipartit), k = 3 (146 gegen Greedy 182)" in text and "Die Garantie hält in jeder Zeile." in text
    rows = special_rows()[:1]
    kind, text = ev.verdict_special(rows)
    assert kind == "info" and "in keiner Zeile unter Greedy" in text
    rows[0]["meets"] = False
    assert "mindestens einer Zeile verfehlt" in ev.verdict_special(rows)[1]
    assert ev.aborted_text(1) == "1 Verschiebung brach" and ev.aborted_text(2) == "2 Verschiebungen brachen" and ev.aborted_text(0) == "0 Verschiebungen brachen"


def test_dp_verdict_by_hand():
    rows = [{"n": 100, "bag": 14, "aborted": 0, "budget": 2_000_000}, {"n": 200, "bag": 19, "aborted": 3, "budget": 2_000_000}, {"n": 400, "bag": 28, "aborted": 5, "budget": 2_000_000}]
    kind, text = ev.verdict_dp(rows)
    assert kind == "info"
    assert "n = 100: größter Beutel 14, n = 200: größter Beutel 19, n = 400: größter Beutel 28." in text and "Ab n = 200 übersteigt" in text and "2.000.000" in text
    assert "Alle Größen blieben unter dem Zellbudget." in ev.verdict_dp([rows[0]])[1]
