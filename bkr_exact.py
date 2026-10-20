"""Exakte Lösung über die Baumzerlegung: gekürzte, unveränderte Kopie aus `tree-decomposition-dp-demo` (Stück 6 der Härte-und-Struktur-Reihe) und `treewidth-demo` (Stück 5).

Hier übernommen, damit diese Demo ohne die anderen läuft: Eliminieren mit Auffüllen, Min-Grad und Min-Fill, Beutel und Elternbeutel aus einer Eliminationsordnung und die Dynamische Programmierung für die
gewichtete größte unabhängige Menge mit Zellbudget (ungewichtet: alle Gewichte 1). Eine Zelle ist ein Tabelleneintrag; die Zahl aller Zellen ist die Summe über alle Beutel von 2^Beutelgröße."""

import heapq
from dataclasses import dataclass


@dataclass(frozen=True)
class Elimination:
    order: tuple          # Eliminationsordnung
    width: int            # größte Beutelgröße minus 1
    fill: int             # Zahl ergänzter Kanten
    bags: tuple           # je Knoten (Index = Knotennummer): seine Beutel-Nachbarn beim Eliminieren, sortiert
    added: tuple          # je Schritt (Index = Position in der Ordnung): die dabei ergänzten Kanten (u, v), u < v
    sizes: tuple          # je Schritt: Beutelgröße (1 + Zahl der Nachbarn)


def eliminate(adj, order):
    """Eliminiert die Knoten in der Reihenfolge `order` und füllt auf. Gibt Breite, Zahl der Sehnen, Beutel je Knoten und die Sehnen je Schritt zurück."""
    n = len(adj)
    if sorted(order) != list(range(n)):
        raise ValueError("die Ordnung muss jeden Knoten genau einmal enthalten")
    h = [set(a) for a in adj]
    bags = [()] * n
    added, sizes = [], []
    fill = 0
    for v in order:
        nb = sorted(h[v])
        bags[v] = tuple(nb)
        sizes.append(len(nb) + 1)
        step_added = []
        for i in range(len(nb)):
            for j in range(i + 1, len(nb)):
                if nb[j] not in h[nb[i]]:
                    h[nb[i]].add(nb[j])
                    h[nb[j]].add(nb[i])
                    step_added.append((nb[i], nb[j]))
        fill += len(step_added)
        added.append(tuple(step_added))
        for w in nb:
            h[w].discard(v)
        h[v] = set()
    width = max(sizes) - 1 if sizes else 0
    return Elimination(tuple(order), width, fill, tuple(bags), tuple(added), tuple(sizes))


def fill_count(h, v):
    """Zahl der Kanten, die beim Eliminieren von v fehlen: Paare seiner Nachbarn, die nicht verbunden sind (alle Paare minus die vorhandenen Kanten unter den Nachbarn)."""
    nb = h[v]
    d = len(nb)
    present = sum(len(h[w] & nb) for w in nb) // 2
    return d * (d - 1) // 2 - present


def _simulate_pick(adj, score, affected_of):
    """Gemeinsamer Rahmen der beiden Heuristiken: immer den Knoten mit dem kleinsten Wert (Gleichstand: kleinster Index) eliminieren; nach dem Eliminieren werden die Werte der betroffenen Knoten neu bestimmt."""
    n = len(adj)
    h = [set(a) for a in adj]
    value = [score(h, v) for v in range(n)]
    heap = [(value[v], v) for v in range(n)]
    heapq.heapify(heap)
    alive = set(range(n))
    order = []
    while alive:
        s, v = heapq.heappop(heap)
        if v not in alive or s != value[v]:
            continue
        nb = sorted(h[v])
        for i in range(len(nb)):
            for j in range(i + 1, len(nb)):
                if nb[j] not in h[nb[i]]:
                    h[nb[i]].add(nb[j])
                    h[nb[j]].add(nb[i])
        for w in nb:
            h[w].discard(v)
        h[v] = set()
        alive.discard(v)
        order.append(v)
        for w in affected_of(h, nb):
            if w in alive:
                value[w] = score(h, w)
                heapq.heappush(heap, (value[w], w))
    return tuple(order)


def min_degree_order(adj):
    """Min-Grad: immer den Knoten mit den wenigsten noch nicht eliminierten Nachbarn eliminieren (Gleichstand: kleinster Index)."""
    return _simulate_pick(adj, lambda h, v: len(h[v]), lambda h, nb: nb)


def min_fill_order(adj):
    """Min-Fill: immer den Knoten eliminieren, dessen Nachbarn die wenigsten fehlenden Kanten haben (Gleichstand: kleinster Index). Betroffen sind die Nachbarn und deren Nachbarn."""
    def affected(h, nb):
        out = set(nb)
        for w in nb:
            out |= h[w]
        return out
    return _simulate_pick(adj, fill_count, affected)


NEG = -(1 << 60)          # Eintrag ungültig: die gewählte Teilmenge des Beutels ist nicht unabhängig oder passt nicht zu einem Kind


@dataclass(frozen=True)
class Rooted:
    order: tuple          # Eliminationsordnung = Verarbeitungsreihenfolge (Kinder vor Eltern)
    bags: tuple           # je Knoten v: der Beutel (sortiertes Tupel: v und seine Beutel-Nachbarn)
    parent: tuple         # je Knoten: Elternknoten oder None (Wurzel einer Komponente)
    children: tuple       # je Knoten: Tupel seiner Kinder
    width: int            # größte Beutelgröße minus 1


def rooted_decomposition(adj, order):
    """Beutel, Eltern und Kinder aus der Eliminationsordnung: Beutel(v) = {v} plus seine Beutel-Nachbarn, Elternknoten = der früheste spätere Nachbar. Hat der Graph mehrere Komponenten,
    gibt es mehrere Wurzeln (die Werte der Komponenten werden einfach addiert)."""
    el = eliminate(adj, order)
    n = len(adj)
    pos = {v: i for i, v in enumerate(order)}
    bags, parent = [None] * n, [None] * n
    kids = [[] for _ in range(n)]
    for v in range(n):
        later = el.bags[v]
        bags[v] = tuple(sorted((v,) + later))
        if later:
            parent[v] = min(later, key=lambda w: pos[w])
            kids[parent[v]].append(v)
    return Rooted(tuple(order), tuple(bags), tuple(parent), tuple(tuple(sorted(k)) for k in kids), el.width)


def predicted_cells(rooted, base=2):
    """Zahl aller Zellen vor dem Rechnen: Summe über alle Beutel von base^|Beutel| (base = 2 für Teilmengen, k für Färbungen)."""
    return sum(base ** len(b) for b in rooted.bags)


def bag_masks(adj, bag, weights):
    """Für jede Teilmenge des Beutels (Bitmaske über die Positionen im sortierten Beutel): ihr Gewicht und ob sie unabhängig ist. Gibt (Gewichte, unabhängig) zurück."""
    idx = {x: i for i, x in enumerate(bag)}
    adjm = [sum(1 << idx[w] for w in adj[x] if w in idx) for x in bag]
    size = 1 << len(bag)
    wsum = [0] * size
    ok = [True] * size
    for s in range(1, size):
        low = s & -s
        i = low.bit_length() - 1
        rest = s ^ low
        wsum[s] = wsum[rest] + weights[bag[i]]
        ok[s] = ok[rest] and (adjm[i] & s) == 0
    return wsum, ok


def project_child(child_bag, child_values, parent_bag, weights):
    """Kindtabelle auf den Trenner (die Knoten, die Kind- und Elternbeutel gemeinsam haben) projizieren. Der Schlüssel ist die Bitmaske der Teilmenge in den Positionen des ELTERNbeutels,
    der Wert der beste Wert des Kindes mit dieser Teilmenge auf dem Trenner, MINUS dem Gewicht dieser Teilmenge (sie zählt später im Elternbeutel). Gibt (Wert je Schlüssel,
    beste Kindmaske je Schlüssel, Trenner-Maske im Elternbeutel) zurück."""
    pidx = {x: i for i, x in enumerate(parent_bag)}
    cidx = {x: i for i, x in enumerate(child_bag)}
    pairs = [(cidx[x], pidx[x], weights[x]) for x in child_bag if x in pidx]
    best, arg = {}, {}
    for sc, val in enumerate(child_values):
        if val <= NEG // 2:
            continue
        key = wsep = 0
        for ci, pi, w in pairs:
            if sc >> ci & 1:
                key |= 1 << pi
                wsep += w
        val -= wsep
        if val > best.get(key, NEG):
            best[key] = val
            arg[key] = sc
    return best, arg, sum(1 << pi for _, pi, _ in pairs)


def table_for_bag(wsum, ok, projections):
    """Die Tabelle eines Beutels: für jede unabhängige Teilmenge S ihr Gewicht plus die besten Werte aller Kinder, die zu S auf dem Trenner passen; ungültig (NEG), wenn S nicht unabhängig ist
    oder ein Kind keinen passenden Eintrag hat. `projections`: Liste von (Wert je Schlüssel, _, Trenner-Maske). Gibt die Wertliste zurück (Länge = Zahl der Teilmengen)."""
    size = len(wsum)
    values = [NEG] * size
    for s in range(size):
        if not ok[s]:
            continue
        total = wsum[s]
        for best, _, sepmask in projections:
            got = best.get(s & sepmask)
            if got is None:
                total = NEG
                break
            total += got
        values[s] = total
    return values


@dataclass(frozen=True)
class DPResult:
    value: int            # Gewicht der besten unabhängigen Menge (bei Abbruch 0)
    chosen: tuple         # ihre Knoten (sortiert)
    cells: int            # tatsächlich berechnete Zellen
    predicted: int        # Summe 2^|Beutel| vor dem Rechnen
    peak: int             # größte Zahl gleichzeitig gehaltener Tabelleneinträge (Spitzenspeicher)
    max_bag: int          # größte Beutelgröße
    aborted: bool         # Zellbudget überschritten: nicht gerechnet
    tables: object = None  # {Knoten: (Beutel, Werte)} bei keep_tables, sonst None


def max_weight_independent_set(adj, weights, order, cell_budget=None, keep_tables=False):
    """Gewichtete größte unabhängige Menge über die Zerlegung der Ordnung `order`. Übersteigt die Vorhersage (Summe 2^Beutel) das `cell_budget`, wird nicht gerechnet (`aborted`).
    Die Tabellen der Kinder werden nach dem Verknüpfen verworfen (Spitzenspeicher), außer bei `keep_tables`. Gewichte ganzzahlig, beliebig (auch 0 oder negativ sind erlaubt,
    ein Knoten mit negativem Gewicht wird nie gewählt)."""
    rd = rooted_decomposition(adj, order)
    n = len(adj)
    pred = predicted_cells(rd)
    max_bag = max((len(b) for b in rd.bags), default=0)
    if cell_budget is not None and pred > cell_budget:
        return DPResult(0, (), 0, pred, 0, max_bag, True, None)
    values, kept, links = {}, {}, {}
    cells = live = peak = 0
    for v in rd.order:
        bag = rd.bags[v]
        wsum, ok = bag_masks(adj, bag, weights)
        projections = []
        for c in rd.children[v]:
            best, arg, sepmask = project_child(rd.bags[c], values[c], bag, weights)
            projections.append((best, arg, sepmask))
            if keep_tables:
                kept[c] = (rd.bags[c], values[c])
            live -= len(values[c])
            del values[c]
        links[v] = projections
        values[v] = table_for_bag(wsum, ok, projections)
        cells += len(values[v])
        live += len(values[v])
        peak = max(peak, live)
    total, chosen = 0, set()
    stack = []
    for r in (v for v in range(n) if rd.parent[v] is None):
        tab = values[r]
        s = max(range(len(tab)), key=lambda m: (tab[m], -m))
        total += tab[s]
        if keep_tables:
            kept[r] = (rd.bags[r], tab)
        stack.append((r, s))
    while stack:
        v, s = stack.pop()
        bag = rd.bags[v]
        chosen.update(bag[i] for i in range(len(bag)) if s >> i & 1)
        for c, (_, arg, sepmask) in zip(rd.children[v], links[v]):
            stack.append((c, arg[s & sepmask]))
    return DPResult(total, tuple(sorted(chosen)), cells, pred, peak, max_bag, False, kept if keep_tables else None)


def is_independent_set(adj, vertices):
    vs = list(vertices)
    return all(vs[j] not in adj[vs[i]] for i in range(len(vs)) for j in range(i + 1, len(vs)))


def brute_force_mwis(adj, weights, limit=20):
    """Gewichtete größte unabhängige Menge durch Aufzählen aller Teilmengen (nur n <= limit). Gibt (Gewicht, Menge) zurück."""
    n = len(adj)
    if n > limit:
        raise ValueError(f"Brute Force nur bis n = {limit}")
    adjm = [sum(1 << w for w in adj[v]) for v in range(n)]
    size = 1 << n
    wsum = [0] * size
    ok = [True] * size
    best, best_mask = 0, 0
    for s in range(1, size):
        low = s & -s
        i = low.bit_length() - 1
        rest = s ^ low
        wsum[s] = wsum[rest] + weights[i]
        ok[s] = ok[rest] and (adjm[i] & s) == 0
        if ok[s] and wsum[s] > best:
            best, best_mask = wsum[s], s
    return best, tuple(i for i in range(n) if best_mask >> i & 1)
