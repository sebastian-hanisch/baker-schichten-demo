"""Konstanten: Regler-Grenzen, Rechengrenzen, feste Pläne, Farben und Presets."""

NET_TYPES = {
    "delaunay": "Karte (Delaunay-Triangulierung)",
    "thin": "Karte mit 80 % der Kanten",
    "grid_diag": "Gitter mit Diagonalen",
    "grid": "Gitter (bipartit)",
}
NET_HELP = (
    "Karte: zufällige Standorte im Quadrat, alle Kanten ihrer Delaunay-Triangulierung. Dünne Karte: dieselbe mit zufällig 80 % der Kanten (kann in Stücke zerfallen). "
    "Gitter mit Diagonalen: k × k Knoten, je Zelle eine Diagonale (trianguliert). Gitter: k × k Knoten ohne Diagonalen (bipartit, das Optimum ist jeder zweite Knoten)."
)
DEFAULT_NET = "delaunay"

ROOTS = {"center": "Mitte", "edge": "Rand (linkester Knoten)"}
ROOT_HELP = "Die Breitensuche beginnt in der Mitte der Karte (Knoten nächst dem Schwerpunkt) oder am linken Rand. Das ändert die Schichten, nicht die Garantie."
DEFAULT_ROOT = "center"

N_MIN, N_MAX, DEFAULT_N = 20, 1600, 400
K_MIN, K_MAX, DEFAULT_K = 2, 8, 5
SEED_MAX, DEFAULT_SEED = 999999, 35

CELL_BUDGET = 3_000_000                 # Tabellenzellen je Rest; mehr bricht die Verschiebung ab
ILS_ITERATIONS = 1500                   # Iterationen der Lokalsuche
OPT_MAX_N = 400                         # bis zu dieser Größe rechnet die App das Optimum auf Klick
OPT_TIME_LIMIT = 60.0
THIN_KEEP = 0.8

SWEEP_SEEDS = tuple(range(100000, 100005))        # feste Pläne für alle Messreihen: nie ein einzelner Seed als Befund
QUALITY_N = 400
QUALITY_KS = (2, 3, 4, 5, 6, 8)
SIZE_SERIES = (100, 200, 400, 800)
SIZE_SERIES_K = 6
SPECIAL_SIDE = 20
SPECIAL_KS = (2, 3, 4, 5, 6, 8)
DP_SIZES = (50, 100, 200, 400, 800)
DP_BUDGET = 2_000_000

COLOR_CHOSEN = "#2F6B65"
COLOR_DELETED = "#9a9a9a"
COLOR_EDGE = "rgba(150,150,150,0.45)"
COLOR_BAKER = "#4c78a8"
COLOR_GREEDY = "#e8a33d"
COLOR_ILS = "#2F6B65"
COLOR_OPT = "#222222"
COLOR_BOUND = "#d62728"

PRESETS = {
    "Karte mit 400 Standorten, k = 5 (Voreinstellung)": {"net": DEFAULT_NET, "n": DEFAULT_N, "k": DEFAULT_K, "root": DEFAULT_ROOT, "seed": DEFAULT_SEED},
    "Kleines k = 2 (Garantie ½)": {"net": DEFAULT_NET, "n": DEFAULT_N, "k": 2, "root": DEFAULT_ROOT, "seed": DEFAULT_SEED},
    "Großes k = 6": {"net": DEFAULT_NET, "n": DEFAULT_N, "k": 6, "root": DEFAULT_ROOT, "seed": DEFAULT_SEED},
    "Gitter mit Diagonalen, k = 3": {"net": "grid_diag", "n": DEFAULT_N, "k": 3, "root": DEFAULT_ROOT, "seed": DEFAULT_SEED},
    "Bipartites Gitter, k = 3": {"net": "grid", "n": DEFAULT_N, "k": 3, "root": DEFAULT_ROOT, "seed": DEFAULT_SEED},
}
PRESET_HELP = {
    "Karte mit 400 Standorten, k = 5 (Voreinstellung)": "400 Standorte, jede fünfte Schicht wird gelöscht: Baker liegt über Greedy, unter der Lokalsuche.",
    "Kleines k = 2 (Garantie ½)": "Jede zweite Schicht wird gelöscht: die Reste sind winzig und die Rechnung blitzschnell, die Garantie ist nur die Hälfte des Optimums.",
    "Großes k = 6": "Reste aus fünf Schichten: die Güte steigt, die Zeit auch (die Zahl der Tabellenzellen wächst mit k exponentiell).",
    "Gitter mit Diagonalen, k = 3": "Auf dem Gitter mit Diagonalen liegt k = 3 in dieser Messung unter Greedy, obwohl die Garantie von 2/3 gilt: die Güte ist in k nicht monoton.",
    "Bipartites Gitter, k = 3": "Auf dem Gitter ohne Diagonalen löscht ein ungerades k die Parität der Schichten (das Optimum nimmt jede zweite): das Ergebnis liegt deutlich unter dem Optimum.",
}
