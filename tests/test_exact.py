"""Die kopierten Bausteine der exakten Lösung (`bkr_exact`): gekürzte Kopie aus `mis-local-search-demo`; hier die Handwerte, die die Mutationsprüfung dieser Demo zusätzlich verlangt hat."""

import bkr_exact as X
from conftest import adj_from_edges


def test_fill_count_by_hand():
    path = [set(a) for a in adj_from_edges(3, [(0, 1), (1, 2)])]
    assert X.fill_count(path, 1) == 1 and X.fill_count(path, 0) == 0                      # Mitte: zwei nicht verbundene Nachbarn
    triangle = [set(a) for a in adj_from_edges(3, [(0, 1), (0, 2), (1, 2)])]
    assert [X.fill_count(triangle, v) for v in range(3)] == [0, 0, 0]
    star = [set(a) for a in adj_from_edges(5, [(0, i) for i in range(1, 5)])]
    assert X.fill_count(star, 0) == 6 and X.fill_count(star, 1) == 0                      # vier Blätter: 6 Paare, keines verbunden
    mixed = [set(a) for a in adj_from_edges(4, [(0, 1), (0, 2), (0, 3), (1, 2)])]
    assert X.fill_count(mixed, 0) == 2                                                    # drei Nachbarn: 3 Paare, eines verbunden


def test_min_fill_order_starts_with_a_zero_fill_vertex_of_smallest_index():
    adj = adj_from_edges(4, [(0, 1), (0, 2), (0, 3), (1, 2)])                             # Füllzahlen: Knoten 1, 2, 3 haben 0, Knoten 0 hat 2
    order = X.min_fill_order(adj)
    assert order[0] == 1 and sorted(order) == [0, 1, 2, 3] and X.eliminate(adj, order).fill == 0
