"""Greedy und Lokalsuche für die größte unabhängige Menge: Greedy nach kleinstem Grad und die Lokalsuche nach Andrade, Resende und Werneck (ARW) in vereinfachter Fassung.

Zustand: Lösungsmarke je Knoten und `tight[v]`, die Zahl der Lösungsnachbarn von v. Ein Knoten ist *frei*, wenn er nicht in der Lösung liegt und `tight` null hat (er kann ohne Verlust eingefügt werden).
Der (1,2)-Tausch: ein Lösungsknoten x wird entfernt, wenn zwei nicht benachbarte Nachbarn mit `tight` eins (x ist ihr einziger Lösungsnachbar) da sind; beide kommen hinein, die Lösung wächst um eins.
Die iterierte Lokalsuche stört die Lösung (ein zufälliger Nichtlösungsknoten wird erzwungen, seine Lösungsnachbarn gehen), steigt wieder ab und nimmt das Ergebnis an, wenn es nicht schlechter ist
(Gleichstand = Plateau); ein schlechteres Ergebnis nur mit der Wahrscheinlichkeit 1 / (1 + (aktuell − neu) · (beste − neu)), sonst wird die Störung über ein Protokoll der Änderungen rückgängig gemacht.

Aufwand wird in Adjazenzzugriffen (`ops`) gezählt, nie in Sekunden. Der Zufall kommt ausschließlich aus `random.Random(seed)`: dasselbe Seed gibt dieselbe Suche."""

import random
from dataclasses import dataclass


def greedy_min_degree(adj):
    """Greedy: Knoten nach (Grad, Nummer) durchgehen und jeden einfügen, der noch frei ist. Gibt die Lösung als sortiertes Tupel zurück."""
    taken, blocked = [], set()
    for v in sorted(range(len(adj)), key=lambda x: (len(adj[x]), x)):
        if v not in blocked:
            taken.append(v)
            blocked.add(v)
            blocked.update(adj[v])
    return tuple(sorted(taken))


@dataclass(frozen=True)
class SearchResult:
    best: tuple           # beste gefundene Lösung (sortiert)
    size: int
    curve: dict           # Haltepunkt (Zahl der Iterationen) -> beste Größe bis dahin; 0 = nach dem ersten Abstieg
    ops: int              # Adjazenzzugriffe
    iterations: int
    start: int            # Größe der Greedy-Lösung


class Search:
    def __init__(self, adj, seed=1):
        self.n = len(adj)
        self.adj = [tuple(sorted(a)) for a in adj]
        self.nbr = [frozenset(a) for a in adj]
        self.rng = random.Random(seed)
        self.in_s = [False] * self.n
        self.tight = [0] * self.n
        self.size = 0
        self.ops = 0
        self.journal = None
        for v in greedy_min_degree(adj):
            self.insert(v)

    # --- Grundoperationen (mit Protokoll für das Rückgängigmachen) ---------------------------------------------------------------------------------

    def insert(self, v):
        self.in_s[v] = True
        self.size += 1
        for w in self.adj[v]:
            self.tight[w] += 1
        self.ops += len(self.adj[v])
        if self.journal is not None:
            self.journal.append((True, v))

    def remove(self, v):
        self.in_s[v] = False
        self.size -= 1
        for w in self.adj[v]:
            self.tight[w] -= 1
        self.ops += len(self.adj[v])
        if self.journal is not None:
            self.journal.append((False, v))

    def undo(self, journal):
        """Macht die protokollierten Änderungen in umgekehrter Reihenfolge rückgängig (ohne Zugriffe zu zählen)."""
        for was_insert, v in reversed(journal):
            sign = -1 if was_insert else 1
            self.in_s[v] = not was_insert
            self.size += sign
            for w in self.adj[v]:
                self.tight[w] += sign

    # --- Lokalsuche --------------------------------------------------------------------------------------------------------------------------------

    def insert_free(self, candidates):
        """Fügt alle freien Knoten unter den Kandidaten ein (in aufsteigender Nummer)."""
        for v in sorted(candidates):
            if not self.in_s[v] and self.tight[v] == 0:
                self.insert(v)

    def two_improvement(self, x):
        """(1,2)-Tausch bei dem Lösungsknoten x: Gibt die neu eingefügten Knoten zurück (leer, wenn es keinen Tausch gibt)."""
        cand = [w for w in self.adj[x] if not self.in_s[w] and self.tight[w] == 1]
        self.ops += len(self.adj[x])
        for i, u in enumerate(cand):
            for w in cand[i + 1:]:
                self.ops += 1
                if w not in self.nbr[u]:
                    self.remove(x)
                    self.insert(u)
                    self.insert(w)
                    extra = [y for y in self.adj[x] if not self.in_s[y] and self.tight[y] == 0]
                    for y in extra:
                        if not self.in_s[y] and self.tight[y] == 0:
                            self.insert(y)
                    return [u, w] + extra
        return []

    def solution_neighbours_of(self, vertices):
        """Lösungsknoten, die an einem Nachbarn der angegebenen Knoten hängen (deren Kandidaten sich geändert haben können)."""
        out = set()
        for v in vertices:
            for z in self.adj[v]:
                self.ops += len(self.adj[z])
                for s in self.adj[z]:
                    if self.in_s[s]:
                        out.add(s)
        return out

    def local_search(self, queue):
        """Absteigen: Lösungsknoten aus der Warteschlange auf einen (1,2)-Tausch prüfen; nach einem Tausch kommen die betroffenen Lösungsknoten wieder in die Warteschlange."""
        queue = sorted(set(queue), reverse=True)
        while queue:
            x = queue.pop()
            if self.in_s[x]:
                added = self.two_improvement(x)
                if added:
                    touched = set(added) | {x}
                    queue.extend(sorted(self.solution_neighbours_of(touched) | set(added), reverse=True))

    # --- iterierte Lokalsuche ----------------------------------------------------------------------------------------------------------------------

    def perturb(self):
        """Störung: ein zufälliger Nichtlösungsknoten wird erzwungen, seine Lösungsnachbarn gehen, freie Knoten rücken nach. Gibt die Warteschlange für den Abstieg zurück oder None."""
        for _ in range(20):
            v = self.rng.randrange(self.n)
            if not self.in_s[v]:
                break
        else:
            return None
        gone = [w for w in self.adj[v] if self.in_s[w]]
        for w in gone:
            self.remove(w)
        self.insert(v)
        around = set()
        for w in gone:
            around.update(self.adj[w])
        self.insert_free(around)
        return {v} | self.solution_neighbours_of({v} | set(gone))

    def run(self, iterations, checkpoints=()):
        """Erster Abstieg von der Greedy-Lösung, dann `iterations` Störungen. Gibt das Ergebnis mit dem Verlauf der besten Größe an den Haltepunkten zurück."""
        start = self.size
        self.local_search([v for v in range(self.n) if self.in_s[v]])
        best_size, best_flags = self.size, list(self.in_s)
        curve = {0: best_size} if 0 in checkpoints else {}
        for it in range(1, iterations + 1):
            before = self.size
            self.journal = []
            queue = self.perturb()
            if queue is not None:
                self.local_search(queue)
                if self.size < before:
                    gap = (before - self.size) * (best_size - self.size)
                    if self.rng.random() >= 1.0 / (1 + gap):
                        self.undo(self.journal)
            self.journal = None
            if self.size > best_size:
                best_size, best_flags = self.size, list(self.in_s)
            if it in checkpoints:
                curve[it] = best_size
        best = tuple(v for v in range(self.n) if best_flags[v])
        return SearchResult(best, best_size, curve, self.ops, iterations, start)


def iterated_local_search(adj, iterations, seed=1, checkpoints=()):
    return Search(adj, seed).run(iterations, checkpoints)
