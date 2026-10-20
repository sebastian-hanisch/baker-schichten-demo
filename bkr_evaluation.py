"""Auswertung: eine Karte mit Baker, Greedy und Lokalsuche, Urteile (reine Funktionen) und die Messreihen der App.

Die Reihen (`quality_series`, `size_series`, `special_series`, `dp_series`) laufen über feste Pläne (`C.SWEEP_SEEDS`), nie über einen einzelnen Seed. Größen und Zellen sind exakt,
Zeiten hängen von Maschine und Umsetzung ab (reines Python)."""

from __future__ import annotations

import statistics
import time
from functools import lru_cache
from dataclasses import dataclass

import bkr_algorithm as A
import bkr_constants as C
import bkr_exact as X
import bkr_scenario as S
import bkr_search as Q


def num(x: float, digits: int = 0) -> str:
    """Zahl im deutschen Format: Tausenderpunkt, Dezimalkomma."""
    return f"{x:,.{digits}f}".translate(str.maketrans({",": ".", ".": ","}))


def plural(count: int, singular: str, plural_form: str) -> str:
    return f"{count} {singular if count == 1 else plural_form}"


def ms_text(seconds: float) -> str:
    """Zeit in Millisekunden, bei einer Sekunde und mehr in Sekunden."""
    return f"{num(seconds, 2)} s" if seconds >= 1 else f"{num(seconds * 1000, 1)} ms"


def aborted_text(count: int) -> str:
    """„1 Verschiebung brach“ bzw. „3 Verschiebungen brachen“ (mit „beim Zellbudget ab“ davor oder dahinter zu verwenden)."""
    return f"{plural(count, 'Verschiebung', 'Verschiebungen')} {'brach' if count == 1 else 'brachen'}"


def percent(x: float) -> str:
    return f"{num(100 * x, 1)} %"


@dataclass(frozen=True)
class Settings:
    net: str = C.DEFAULT_NET
    n: int = C.DEFAULT_N
    k: int = C.DEFAULT_K
    root: str = C.DEFAULT_ROOT
    seed: int = C.DEFAULT_SEED


@dataclass(frozen=True)
class Analysis:
    settings: Settings
    graph: S.Graph
    root: int
    baker: A.BakerResult
    baker_time: float
    greedy: tuple[int, ...]
    ils: Q.SearchResult
    ils_time: float

    @property
    def baker_size(self) -> int | None:
        return self.baker.size

    @property
    def greedy_size(self) -> int:
        return len(self.greedy)

    @property
    def ils_size(self) -> int:
        return self.ils.size


def run_all(graph: S.Graph, k: int, root: int, ils_seed: int = 1) -> tuple[A.BakerResult, float, tuple[int, ...], Q.SearchResult, float]:
    """Baker, Greedy und Lokalsuche auf demselben Graphen; Zeiten der zwei teuren Verfahren."""
    t0 = time.perf_counter()
    baker = A.baker(graph.adj, k, root, C.CELL_BUDGET)
    baker_time = time.perf_counter() - t0
    greedy = Q.greedy_min_degree(graph.adj)
    t0 = time.perf_counter()
    ils = Q.iterated_local_search(graph.adj, C.ILS_ITERATIONS, seed=ils_seed)
    return baker, baker_time, greedy, ils, time.perf_counter() - t0


def analyse(settings: Settings) -> Analysis:
    graph = S.make_graph(settings.net, settings.n, settings.seed)
    root = S.root_vertex(graph, settings.root)
    baker, bt, greedy, ils, it = run_all(graph, settings.k, root)
    return Analysis(settings, graph, root, baker, bt, greedy, ils, it)


@lru_cache(maxsize=256)
def cached_optimum(net: str, n: int, seed: int) -> A.Optimum:
    """Das Optimum einer festen Karte (zwischengespeichert: dieselbe Karte kommt in mehreren Reihen vor)."""
    return A.milp_optimum(S.make_graph(net, n, seed).adj, C.OPT_TIME_LIMIT)


def optimum_for(settings: Settings) -> A.Optimum:
    return cached_optimum(settings.net, settings.n, settings.seed)


# --- Messreihen --------------------------------------------------------------------------------------------------------------------------------


def _quota(size, reference):
    return None if size is None or not reference else size / reference


def _median(values):
    values = [v for v in values if v is not None]
    return statistics.median(values) if values else None


def quality_series(n: int = C.QUALITY_N, ks=C.QUALITY_KS, seeds=C.SWEEP_SEEDS, net: str = "delaunay") -> list[dict]:
    """Baker für jedes k auf festen Karten, gegen das Optimum (`milp`), Greedy und Lokalsuche; eine Zeile je k, Mediane über die Pläne."""
    plans = []
    for seed in seeds:
        graph = S.make_graph(net, n, seed)
        root = S.root_vertex(graph, C.DEFAULT_ROOT)
        opt = cached_optimum(net, n, seed)
        greedy = len(Q.greedy_min_degree(graph.adj))
        ils = Q.iterated_local_search(graph.adj, C.ILS_ITERATIONS, seed=1).size
        plans.append((graph, root, opt, greedy, ils))
    rows = []
    for k in ks:
        per_plan = []
        for graph, root, opt, greedy, ils in plans:
            t0 = time.perf_counter()
            result = A.baker(graph.adj, k, root, C.CELL_BUDGET)
            per_plan.append((result, time.perf_counter() - t0))
        sizes = [r.size for r, _ in per_plan]
        opts = [p[2].value for p in plans]
        rows.append({
            "k": k, "n": n, "plans": len(plans), "opt": _median(opts), "opt_proven": sum(1 for p in plans if p[2].proven),
            "greedy": _median([p[3] for p in plans]), "ils": _median([p[4] for p in plans]), "baker": _median(sizes),
            "baker_quota": _median([_quota(s, o) for s, o in zip(sizes, opts)]),
            "greedy_quota": _median([p[3] / p[2].value for p in plans]), "ils_quota": _median([p[4] / p[2].value for p in plans]),
            "guarantee": A.guarantee_ratio(k),
            "meets": sum(1 for s, o in zip(sizes, opts) if s is not None and A.meets_guarantee(s, o, k)), "finished": sum(1 for s in sizes if s is not None),
            "time": statistics.median(t for _, t in per_plan), "bag": max(r.max_bag for r, _ in per_plan), "width_bound": A.width_bound(k),
            "aborted": sum(r.aborted for r, _ in per_plan),
            "above_greedy": sum(1 for s, p in zip(sizes, plans) if s is not None and s > p[3]),
        })
    return rows


def size_series(sizes=C.SIZE_SERIES, k: int = C.SIZE_SERIES_K, seeds=C.SWEEP_SEEDS) -> list[dict]:
    """Baker (festes k) gegen Greedy und Lokalsuche über die Größe der Karte; das Optimum nur bis `C.OPT_MAX_N`, sonst bezieht sich die Quote auf die beste bekannte Größe."""
    rows = []
    for n in sizes:
        per_plan = []
        for seed in seeds:
            graph = S.make_graph("delaunay", n, seed)
            root = S.root_vertex(graph, C.DEFAULT_ROOT)
            baker, bt, greedy, ils, it = run_all(graph, k, root)
            opt = cached_optimum("delaunay", n, seed).value if n <= C.OPT_MAX_N else None
            known = max(x for x in (opt, ils.size, len(greedy), baker.size) if x is not None)
            per_plan.append((baker, bt, len(greedy), ils.size, it, opt, known))
        rows.append({
            "n": n, "k": k, "plans": len(per_plan), "baker": _median([p[0].size for p in per_plan]), "greedy": _median([p[2] for p in per_plan]), "ils": _median([p[3] for p in per_plan]),
            "opt": _median([p[5] for p in per_plan]), "known": _median([p[6] for p in per_plan]),
            "baker_quota": _median([_quota(p[0].size, p[6]) for p in per_plan]), "greedy_quota": _median([p[2] / p[6] for p in per_plan]), "ils_quota": _median([p[3] / p[6] for p in per_plan]),
            "baker_time": statistics.median(p[1] for p in per_plan), "ils_time": statistics.median(p[4] for p in per_plan), "aborted": sum(p[0].aborted for p in per_plan),
        })
    return rows


def special_series(side: int = C.SPECIAL_SIDE, ks=C.SPECIAL_KS, seed: int = C.SWEEP_SEEDS[0]) -> list[dict]:
    """Gitter mit Diagonalen, Gitter und dünne Karte (je ein fester Graph), Baker für jedes k gegen das Optimum, Greedy und Lokalsuche."""
    rows = []
    for net in ("grid_diag", "grid", "thin"):
        graph = S.make_graph(net, side * side, seed)
        root = S.root_vertex(graph, C.DEFAULT_ROOT)
        opt = cached_optimum(net, side * side, seed).value
        greedy = len(Q.greedy_min_degree(graph.adj))
        ils = Q.iterated_local_search(graph.adj, C.ILS_ITERATIONS, seed=1).size
        for k in ks:
            result = A.baker(graph.adj, k, root, C.CELL_BUDGET)
            rows.append({"net": net, "k": k, "n": graph.n, "opt": opt, "greedy": greedy, "ils": ils, "baker": result.size,
                         "baker_quota": _quota(result.size, opt), "guarantee": A.guarantee_ratio(k),
                         "meets": result.size is not None and A.meets_guarantee(result.size, opt, k)})
    return rows


def dp_series(sizes=C.DP_SIZES, seeds=C.SWEEP_SEEDS, budget: int = C.DP_BUDGET) -> list[dict]:
    """Der ganze Graph per DP statt Schichten: größter Beutel (Min-Fill) und vorhergesagte Zellen je Größe der Karte, Abbruch beim Zellbudget."""
    rows = []
    for n in sizes:
        bags, predicted, aborted = [], [], 0
        for seed in seeds:
            graph = S.make_graph("delaunay", n, seed)
            order = X.min_fill_order(graph.adj)
            res = X.max_weight_independent_set(graph.adj, [1] * graph.n, order, budget)
            bags.append(res.max_bag)
            predicted.append(res.predicted)
            aborted += int(res.aborted)
        rows.append({"n": n, "plans": len(seeds), "bag": statistics.median(bags), "predicted": statistics.median(predicted), "aborted": aborted, "budget": budget})
    return rows


# --- Urteile (rein) ----------------------------------------------------------------------------------------------------------------------------


def verdict_baker(a: Analysis, opt: A.Optimum | None = None) -> tuple[str, str]:
    """Urteil über eine Karte als (Art, Text): Baker gegen Greedy und Lokalsuche, Garantie, Optimum auf Klick; die App ruft st.<Art>(Text), der Test prüft jede Zahl an handgesetzten Werten."""
    k = a.settings.k
    if a.baker_size is None:
        return "warning", (f"Alle {k} Verschiebungen brechen ab: ein Rest braucht mehr als {num(C.CELL_BUDGET)} Tabellenzellen (größter Beutel {a.baker.max_bag}). "
                           "Kleineres k oder eine kleinere Karte wählen.")
    best = a.baker.best
    head = f"Baker (k = {k}, beste Verschiebung {best.shift}) findet **{num(a.baker_size)}** unabhängige Knoten in {ms_text(a.baker_time)}; Greedy {num(a.greedy_size)}, Lokalsuche {num(a.ils_size)} in {ms_text(a.ils_time)}."
    parts = [head, f"Garantie: mindestens {percent(A.guarantee_ratio(k))} des Optimums."]
    if a.baker.aborted:
        parts.append(f"{aborted_text(a.baker.aborted)} beim Zellbudget ab.")
    if opt is not None and opt.value is not None:
        quota = a.baker_size / opt.value
        proof = "" if opt.proven else " (beste gefundene Größe, nicht bewiesen)"
        parts.append(f"Optimum {num(opt.value)}{proof}: Baker erreicht **{percent(quota)}**, Greedy {percent(a.greedy_size / opt.value)}, Lokalsuche {percent(a.ils_size / opt.value)}.")
    if a.baker_size > a.greedy_size and a.baker_size >= a.ils_size:
        return "success", " ".join(parts)
    if a.baker_size > a.greedy_size:
        parts.append("Die Lokalsuche ist besser.")
        return "info", " ".join(parts)
    parts.append("Greedy ist mindestens so gut: die Garantie ist ein Satz über den schlechtesten Fall, nicht über diese Karte.")
    return "warning", " ".join(parts)


def verdict_shifts(a: Analysis) -> tuple[str, str]:
    """Urteil über die k Verschiebungen: Spanne der Lösungsgrößen und die beste."""
    done = [s for s in a.baker.shifts if not s.aborted]
    if not done:
        return "warning", "Keine Verschiebung wurde fertig."
    sizes = [len(s.chosen) for s in done]
    best = a.baker.best
    worst = min(done, key=lambda s: (len(s.chosen), s.shift))
    spread = f"**{min(sizes)} bis {max(sizes)}**" if min(sizes) != max(sizes) else f"alle **{min(sizes)}**"
    text = (f"Die {plural(len(done), 'fertige Verschiebung', 'fertigen Verschiebungen')} liefern {spread} Knoten; die beste ist Verschiebung {best.shift} ({len(best.chosen)})"
            + (f", die schlechteste Verschiebung {worst.shift} ({len(worst.chosen)})." if min(sizes) != max(sizes) else " (bei Gleichstand die kleinste).")
            + " Das Mittel über alle k Verschiebungen verliert höchstens ein k-tel einer größten Menge; die beste Verschiebung liegt mindestens darüber.")
    return "info", text


def verdict_quality(rows: list[dict]) -> tuple[str, str]:
    first, last = rows[0], rows[-1]
    over = next((r["k"] for r in rows if r["baker"] is not None and r["baker"] > r["greedy"]), None)
    ils_better = all(r["ils"] >= r["baker"] for r in rows if r["baker"] is not None)
    holds = all(r["meets"] == r["finished"] for r in rows)
    greedy = f"Baker liegt ab k = {over} über Greedy" if over is not None else "Baker liegt in keiner Zeile über Greedy"
    ils = "die Lokalsuche ist in allen Zeilen mindestens so gut" if ils_better else "die Lokalsuche liegt nicht in allen Zeilen vorn"
    guarantee = "Die Garantie hält in jedem fertigen Plan." if holds else "Die Garantie wurde in mindestens einem Plan verfehlt."
    aborted = sum(r["aborted"] for r in rows)
    if aborted:
        guarantee += f" {aborted_text(aborted)} beim Zellbudget ab (die Garantie gilt nur, wenn alle k Verschiebungen fertig werden)."
    text = (f"n = {first['n']}, {first['plans']} Pläne (Mediane): Baker erreicht **{percent(first['baker_quota'])}** des Optimums bei k = {first['k']} und **{percent(last['baker_quota'])}** bei k = {last['k']} "
            f"(Garantie {percent(first['guarantee'])} und {percent(last['guarantee'])}); Greedy {percent(first['greedy_quota'])}, Lokalsuche {percent(first['ils_quota'])}. {greedy}; {ils}. {guarantee}")
    return ("success" if holds and over is not None else "info"), text


def verdict_width(rows: list[dict]) -> tuple[str, str]:
    above = [r for r in rows if r["bag"] - 1 > r["width_bound"]]
    text = ("Größter Beutel der Min-Fill-Zerlegungen gegen die Schranke 3 (k − 1) − 1 für Reste aus k − 1 Schichten (Literaturwert, nicht im Original geprüft): "
            + ", ".join(f"k = {r['k']}: Breite {r['bag'] - 1} gegen {r['width_bound']}" for r in rows) + ". ")
    if above:
        text += f"Ab k = {above[0]['k']} liegt die Heuristik über der Schranke: die Schranke gilt für die beste Zerlegung, Min-Fill findet sie nicht."
    else:
        text += "Die Heuristik bleibt in allen Zeilen unter der Schranke."
    return "info", text


def verdict_sizes(rows: list[dict]) -> tuple[str, str]:
    last = rows[-1]
    lagging = all(r["ils"] >= r["baker"] for r in rows if r["baker"] is not None)
    text = (f"k = {last['k']}, n = {rows[0]['n']} bis {last['n']} ({last['plans']} Pläne, Mediane): bei n = {last['n']} findet Baker {num(last['baker'])} Knoten in {ms_text(last['baker_time'])}, "
            f"die Lokalsuche {num(last['ils'])} in {ms_text(last['ils_time'])}, Greedy {num(last['greedy'])}. ")
    text += "Die Lokalsuche ist in jeder Größe besser." if lagging else "Die Lokalsuche ist nicht in jeder Größe besser."
    return "info", text


def verdict_special(rows: list[dict]) -> tuple[str, str]:
    below = [r for r in rows if r["baker"] is not None and r["baker"] < r["greedy"]]
    broken = [r for r in rows if r["baker"] is not None and not r["meets"]]
    pieces = [f"{C.NET_TYPES[r['net']]}, k = {r['k']} ({r['baker']} gegen Greedy {r['greedy']})" for r in below]
    text = "Baker liegt unter Greedy bei: " + "; ".join(pieces) + ". " if pieces else "Baker liegt in keiner Zeile unter Greedy. "
    text += "Die Garantie hält in jeder Zeile." if not broken else "Die Garantie wurde in mindestens einer Zeile verfehlt."
    return ("warning" if below else "info"), text


def verdict_dp(rows: list[dict]) -> tuple[str, str]:
    aborted = next((r for r in rows if r["aborted"] > 0), None)
    text = ", ".join(f"n = {r['n']}: größter Beutel {num(r['bag'])}" for r in rows) + ". "
    if aborted is not None:
        text += f"Ab n = {aborted['n']} übersteigt die vorhergesagte Zellenzahl das Budget von {num(aborted['budget'])}: der ganze Graph ist per DP nicht zu rechnen, die Schichten schon."
    else:
        text += "Alle Größen blieben unter dem Zellbudget."
    return "info", text
