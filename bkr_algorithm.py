"""Kern: die Baker-Technik für die größte unabhängige Menge auf planaren Graphen.

Ein Graph ist eine Liste von Nachbarmengen `adj` (Knoten 0 bis n − 1, einfach, ungerichtet). **Schichten:** Breitensuche von einer Wurzel aus (weitere Komponenten beginnen beim kleinsten noch nicht
erreichten Knoten mit Schicht 0). **Verschiebung i** (0 bis k − 1): alle Schichten j mit j ≡ i (mod k) werden gelöscht; was bleibt, zerfällt in Reste aus höchstens k − 1 aufeinanderfolgenden Schichten,
die durch gelöschte Schichten voneinander getrennt sind. Jeder Rest wird **exakt** gelöst (Dynamische Programmierung über eine Min-Fill-Zerlegung, `bkr_exact`), die Lösungen der Reste zusammen sind
unabhängig. Die beste der k Verschiebungen gewinnt; im Mittel über die Verschiebungen verliert man höchstens ein k-tel einer größten Menge, die beste Verschiebung also höchstens das:
**Güte mindestens (1 − 1/k) · OPT**. Gleichstand entscheidet die kleinere Verschiebung. Kein Zufall im Kern."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass

import bkr_exact as X

# --- Schichten und Reste -----------------------------------------------------------------------------------------------------------------------


def bfs_layers(adj, root: int = 0) -> tuple[int, ...]:
    """Schicht jedes Knotens: Abstand zur Wurzel; weitere Komponenten starten beim kleinsten noch nicht erreichten Knoten mit Schicht 0."""
    n = len(adj)
    layer = [-1] * n
    starts = [root] + [v for v in range(n) if v != root]
    for s in starts:
        if layer[s] >= 0:
            continue
        layer[s] = 0
        queue = deque([s])
        while queue:
            x = queue.popleft()
            for y in sorted(adj[x]):
                if layer[y] < 0:
                    layer[y] = layer[x] + 1
                    queue.append(y)
    return tuple(layer)


def kept_vertices(layer, k: int, shift: int) -> frozenset[int]:
    """Knoten, die nach dem Löschen der Schichten j ≡ shift (mod k) bleiben."""
    return frozenset(v for v, j in enumerate(layer) if j % k != shift)


def components(adj, keep) -> list[list[int]]:
    """Zusammenhangskomponenten des von `keep` induzierten Teilgraphen, je aufsteigend sortiert, nach kleinstem Knoten geordnet."""
    seen: set[int] = set()
    out = []
    for s in sorted(keep):
        if s in seen:
            continue
        comp = [s]
        seen.add(s)
        queue = deque([s])
        while queue:
            x = queue.popleft()
            for y in adj[x]:
                if y in keep and y not in seen:
                    seen.add(y)
                    comp.append(y)
                    queue.append(y)
        out.append(sorted(comp))
    return out


@dataclass(frozen=True)
class Piece:
    chosen: tuple[int, ...]     # eine größte unabhängige Menge des Rests (Knoten des ganzen Graphen), bei Abbruch leer
    cells: int                  # berechnete Tabellenzellen
    predicted: int              # Summe 2^Beutel vor dem Rechnen
    max_bag: int                # größte Beutelgröße
    aborted: bool               # Zellbudget überschritten


def solve_piece(adj, comp, cell_budget: int | None = None) -> Piece:
    """Größte unabhängige Menge des Rests `comp` per DP über die Min-Fill-Zerlegung."""
    index = {v: i for i, v in enumerate(comp)}
    sub = tuple(frozenset(index[w] for w in adj[v] if w in index) for v in comp)
    order = X.min_fill_order(sub)
    res = X.max_weight_independent_set(sub, [1] * len(comp), order, cell_budget)
    if res.aborted:
        return Piece((), 0, res.predicted, res.max_bag, True)
    return Piece(tuple(comp[i] for i in res.chosen), res.cells, res.predicted, res.max_bag, False)


@dataclass(frozen=True)
class Shift:
    shift: int
    chosen: tuple[int, ...]     # vereinigte Lösung der Reste (leer bei Abbruch)
    pieces: int                 # Zahl der Reste
    cells: int
    max_bag: int
    aborted: bool

    @property
    def size(self) -> int | None:
        return None if self.aborted else len(self.chosen)


@dataclass(frozen=True)
class BakerResult:
    k: int
    root: int
    layers: tuple[int, ...]
    shifts: tuple[Shift, ...]
    best: Shift | None          # beste fertige Verschiebung (kleinste bei Gleichstand), None wenn alle abbrachen

    @property
    def size(self) -> int | None:
        return None if self.best is None else len(self.best.chosen)

    @property
    def cells(self) -> int:
        return sum(s.cells for s in self.shifts)

    @property
    def max_bag(self) -> int:
        return max(s.max_bag for s in self.shifts)

    @property
    def aborted(self) -> int:
        return sum(1 for s in self.shifts if s.aborted)

    @property
    def height(self) -> int:
        return max(self.layers) + 1 if self.layers else 0


def baker(adj, k: int, root: int = 0, cell_budget: int | None = None) -> BakerResult:
    """Baker-Technik: für jede Verschiebung die Schichten j ≡ i (mod k) löschen, die Reste exakt lösen, die Lösungen vereinen; die beste Verschiebung gewinnt.
    Überschreitet ein Rest das Zellbudget, gilt die ganze Verschiebung als abgebrochen (keine Aussage)."""
    layer = bfs_layers(adj, root)
    shifts = []
    for i in range(k):
        chosen: list[int] = []
        cells = max_bag = pieces = 0
        aborted = False
        for comp in components(adj, kept_vertices(layer, k, i)):
            piece = solve_piece(adj, comp, cell_budget)
            pieces += 1
            max_bag = max(max_bag, piece.max_bag)
            if piece.aborted:
                aborted = True
                break
            chosen += piece.chosen
            cells += piece.cells
        shifts.append(Shift(i, () if aborted else tuple(sorted(chosen)), pieces, cells, max_bag, aborted))
    done = [s for s in shifts if not s.aborted]
    best = max(done, key=lambda s: (len(s.chosen), -s.shift)) if done else None
    return BakerResult(k, root, layer, tuple(shifts), best)


# --- Gütegarantie und Gegenproben -----------------------------------------------------------------------------------------------------------------


def meets_guarantee(size: int, opt: int, k: int) -> bool:
    """Gilt size ≥ (1 − 1/k) · opt? Ganzzahlig gerechnet: size · k ≥ (k − 1) · opt."""
    return size * k >= (k - 1) * opt


def guarantee_ratio(k: int) -> float:
    return 1 - 1 / k


def width_bound(k: int) -> int:
    """Literaturwert (Außenplanarität r, Baumweite höchstens 3r − 1) für einen Rest aus k − 1 Schichten: 3 (k − 1) − 1. Nicht im Original geprüft."""
    return 3 * (k - 1) - 1


def is_independent(adj, vertices) -> bool:
    chosen = set(vertices)
    return all(not (set(adj[v]) & chosen) for v in chosen)


def triangle_rows(adj) -> list[list[int]]:
    """Cliquen-Bedingungen: jedes Dreieck (u < v < w) einmal, dazu alle Kanten, die in keinem Dreieck liegen."""
    n = len(adj)
    triangles = []
    covered = set()
    for u in range(n):
        for v in sorted(adj[u]):
            if v > u:
                for w in sorted(set(adj[u]) & set(adj[v])):
                    if w > v:
                        triangles.append([u, v, w])
                        covered.update({(u, v), (u, w), (v, w)})
    edges = [[u, v] for u in range(n) for v in sorted(adj[u]) if u < v and (u, v) not in covered]
    return triangles + edges


@dataclass(frozen=True)
class Optimum:
    value: int | None        # beste gefundene Größe (None: keine Lösung)
    proven: bool             # als optimal bewiesen
    seconds: float


def milp_optimum(adj, time_limit: float = 60.0) -> Optimum:
    """Größte unabhängige Menge exakt per `scipy.optimize.milp` mit Dreiecks-Cliquen als Bedingungen (auf Triangulierungen eng). Ohne Beweis binnen `time_limit` ist der Wert nur die beste gefundene Größe."""
    import numpy as np
    from scipy.optimize import Bounds, LinearConstraint, milp
    from scipy.sparse import lil_matrix

    n = len(adj)
    rows = triangle_rows(adj)
    t0 = time.perf_counter()
    if not rows:
        return Optimum(n, True, time.perf_counter() - t0)
    matrix = lil_matrix((len(rows), n))
    for i, row in enumerate(rows):
        for v in row:
            matrix[i, v] = 1
    res = milp(-np.ones(n), constraints=LinearConstraint(matrix.tocsr(), -np.inf, 1), integrality=np.ones(n), bounds=Bounds(0, 1), options={"time_limit": time_limit})
    value = None if res.x is None else int(round(-res.fun))
    return Optimum(value, res.status == 0, time.perf_counter() - t0)
