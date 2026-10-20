# Schichten zerlegen – die Baker-Technik – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-baker-schichten-demo.streamlit.app/)** -->

Siebtes Stück der **Planarität-und-Zeichnen-Linie** (Graphentheorie) in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Es verbindet die Linie mit der Härte-Reihe: die exakte Dynamische Programmierung auf Baumzerlegungen ([tree-decomposition-dp-demo](https://github.com/sebastian-hanisch/tree-decomposition-dp-demo)) und die Praxisverfahren Greedy und Lokalsuche ([mis-local-search-demo](https://github.com/sebastian-hanisch/mis-local-search-demo)); die BFS-Schichten kommen aus dem dritten Stück ([planar-separator-demo](https://github.com/sebastian-hanisch/planar-separator-demo)).

Auf einer Karte sollen möglichst viele Orte gewählt werden, von denen keine zwei benachbart sind (die **größte unabhängige Menge**). Das ist auch auf planaren Karten schwer. Die **Baker-Technik** macht daraus ein **Näherungsschema**: man sucht von einem Ort aus Schicht für Schicht (Breitensuche), löscht **jede k-te Schicht**, löst die Reste aus höchstens k − 1 Schichten **exakt** und nimmt die beste der k Verschiebungen. Garantie: **mindestens (1 − 1/k) des Optimums**. Die Demo misst, wie nah die Praxis an diese Garantie kommt, was k kostet, und wie sich das Verfahren gegen Greedy, Lokalsuche und das Optimum schlägt.

## Warum dieses Problem

„Beschränkte Baumweite pro Rest reicht, um beliebig nah ans Optimum zu kommen“ ist ein schöner Satz mit einem handfesten Preis: die Rechenzeit wächst stark mit k. Kernfrage: **Wie weit liegt die Praxis von der Garantie, was kostet k, und lohnt das gegen Verfahren ohne Garantie?** Die Antwort ist zweiseitig: die Garantie hält und die gemessene Güte liegt weit darüber, aber auf diesen Karten ist die Lokalsuche in Güte und Zeit überlegen. Der Wert der Technik ist die Garantie, nicht die Güte.

## Modell

Graphen: **Delaunay-Karten** (zufällige Standorte, alle Kanten der Triangulierung), **dünne Karten** (80 % der Kanten, können zerfallen), **Gitter mit Diagonalen** und **Gitter** (bipartit). **Schichten:** Breitensuche von einer Wurzel (Mitte oder linker Rand); weitere Komponenten beginnen mit Schicht 0. **Verschiebung i:** die Schichten j ≡ i (mod k) werden gelöscht, die Reste aus höchstens k − 1 aufeinanderfolgenden Schichten sind durch gelöschte Schichten getrennt und werden exakt gelöst (Dynamische Programmierung über eine Min-Fill-Zerlegung, Zellbudget 3 Mio je Rest, darüber bricht die Verschiebung ab). Die Vereinigung der Lösungen ist unabhängig; die beste Verschiebung gewinnt (Gleichstand: die kleinere). **Garantie:** die gelöschten Klassen zerlegen eine größte Menge; ein i verliert höchstens ein k-tel, also ist die beste Verschiebung mindestens (1 − 1/k) · OPT. Formeln im 📐-Expander der App.

## Methodik

- **Eine Karte:** Graph, Knotenzahl, k, Wurzel, Zufalls-Seed; Baker, Greedy (kleinster Grad zuerst) und Lokalsuche (1 500 Iterationen) nebeneinander, Zeichnung mit Schichten, gelöschter Schicht und Lösung, Urteil; auf Klick das Optimum (`scipy.milp` mit Dreiecks-Cliquen, bis n = 400).
- **Die k Verschiebungen:** Tabelle und Balken der Lösungsgröße je Verschiebung, mit Greedy, Lokalsuche, Optimum und Garantie als Linien.
- **Messreihen auf Klick** (feste Pläne 100000 bis 100004, Mediane): Güte und Zeit über k (n = 400), Beutelbreite gegen die Schranke, über die Größe (n = 100 bis 800, k = 6), Sonderfälle (Gitter mit Diagonalen, Gitter, dünne Karte), der ganze Graph per DP.
- **Aufwandsmaß:** Lösungsgrößen und Tabellenzellen sind exakt, Zeiten gelten für diese Python-Umsetzung.

## Befunde (gemessen, keine Behauptungen)

Zeiten sind auf dem Entwicklungsrechner (Windows, reines Python) gemessen; die Tests prüfen dazu nur Richtungen und weite Verhältnisse. Gittergrößen sind exakt, bei Delaunay-Karten und der dünnen Karte gilt im Test ein Band von ±2 Knoten.

| Frage | Befund | Test |
|---|---|---|
| Hält die Garantie? | In allen Plänen und für alle k der Reihen (5 Pläne × 6 Werte von k): Baker liegt zwischen (1 − 1/k) · OPT und OPT, die Lösung jeder Verschiebung ist unabhängig. Gegen Brute Force (26 Graphen bis 18 Knoten, k = 2 bis 5, zwei Wurzeln), ein zweites ganzzahliges Programm nur mit Kantenbedingungen (24 Graphen mit 60 Knoten) und die DP über den ganzen Graphen (15 Graphen mit 40 Knoten). | `test_the_guarantee_holds_in_every_plan_and_the_estimate_is_far_above_it`, `test_the_oracle_covers_26_small_24_medium_and_15_whole_graph_cases`, `tests/test_oracle_baker.py` |
| Wie weit liegt die Praxis über der Garantie? (Karten mit 400 Standorten, 5 Pläne, Mediane; k = 2 / 3 / 4 / 5 / 6 / 8) | Baker **99 / 108 / 111 / 116 / 119 / 121** Knoten bei Optimum 127: **77,5 / 84,1 / 88,0 / 92,0 / 93,6 / 96,0 %**; Garantie 50,0 / 66,7 / 75,0 / 80,0 / 83,3 / 87,5 %. Greedy 115 (90,7 %), Lokalsuche 126 (99,2 %). | `test_quality_by_k_matches_the_readme` |
| Ab wann schlägt Baker Greedy? | In allen 5 Plänen **ab k = 6**, bei k = 5 in 3 von 5, bei k ≤ 4 in keinem (k = 4: 111 gegen 115). | `test_baker_beats_greedy_from_k_6_in_every_plan_and_never_beats_local_search` |
| Schlägt Baker die Lokalsuche? | **Nein**, in keiner Zeile (Lokalsuche 126 gegen Baker 121 bei k = 8). Über die Größe (k = 6; n = 100 / 200 / 400 / 800): Baker 32 / 61 / 119 / 235, Greedy 27 / 56 / 115 / 224, Lokalsuche 32 / 64 / 126 / 249, Optimum 32 / 64 / 127 / –. | `test_sizes_by_n_match_the_readme` |
| Was kostet k? (n = 400, Mediane) | Zeit des Baker etwa **0,007 / 0,03 / 0,07 / 0,2 / 0,7 / 1,4 s** (k = 2 bis 8), die Lokalsuche etwa 0,04 s. Größter Beutel 3 / 6 / 9 / 13 / 16 / 22. Bei k = 8 brechen 18 von 40 Verschiebungen am Zellbudget ab (Test: einzelne brechen ab, bei k ≤ 6 keine). Über die Größe (k = 6) braucht Baker 0,05 / 0,23 / 0,71 / 1,8 s, mehr als das Doppelte der Lokalsuche ab n = 200. | `test_beutel_sizes_and_time_grow_with_k_and_pass_the_bound_from_k_5`, `test_baker_is_slower_than_local_search_from_n_200` |
| Hält die Schranke 3 (k − 1) − 1 für die Breite? | Die Schranke ist ein Literaturwert (nicht im Original geprüft). Min-Fill misst Breite 2 / 5 / 8 / 12 / 15 / 21 gegen 2 / 5 / 8 / 11 / 14 / 20: **ab k = 5 über der Schranke**, weil Min-Fill nicht die beste Zerlegung findet. | dieselbe |
| Warum nicht gleich alles per DP? | Größter Beutel des ganzen Graphen (Delaunay, Min-Fill) 10 / 14 / 19 / 28 / 38 bei n = 50 / 100 / 200 / 400 / 800; ab n = 200 bricht in 3 von 5 Plänen das Zellbudget von 2 Mio ab, ab n = 400 in allen. | `test_the_whole_graph_dp_breaks_at_n_200` |
| Ist Baker monoton in k? | **Nein.** Gitter (bipartit): Baker 200 / **146** / 200 / **176** / 200 / 200 für k = 2 / 3 / 4 / 5 / 6 / 8 bei Optimum 200 und Greedy 182: bei ungeradem k geht die Parität der Schichten verloren. Gitter mit Diagonalen (Optimum 134, Greedy 102, Lokalsuche 133): 105 / **98** / 109 / 117 / 118 / 121, bei k = 3 unter Greedy. Dünne Karte (Optimum 155, Greedy 142, Lokalsuche 154): 115 / 131 / 135 / 141 / 144 / 147, erst bei k = 8 über Greedy. Die Garantie hält überall. | `test_grid_cases_are_exact`, `test_thin_map_is_in_bands` |
| Was zeigen die Presets? | Voreinstellung (Karte, k = 5, Seed 35): Baker **116**, Greedy 109, Lokalsuche 124, Optimum 124, Garantie hält. k = 2: 98; k = 6: 118 (langsamer als k = 5). Gitter mit Diagonalen, k = 3: 98 gegen Greedy 102 und Lokalsuche 133. Bipartites Gitter, k = 3: 146 in allen drei Verschiebungen gegen Greedy 182 und Optimum 200. | `test_presets_hold_what_their_help_texts_say`, `test_the_default_map_has_known_optimum_and_the_guarantee_holds` |

## Ehrliche Grenzen

- **Die Technik ist ein Garantieverfahren, kein Praxisverfahren.** Auf diesen Karten ist die Lokalsuche in Güte und Zeit besser; die Garantie ist ein Satz über den schlechtesten Fall.
- **Zeit wächst stark mit k.** Die Tabellen haben 2^Beutel Zellen; bei k = 8 brechen schon bei n = 400 einzelne Verschiebungen am Zellbudget ab, die Garantie gilt dann nur für fertige Verschiebungen. Die App zeigt Abbrüche ausdrücklich.
- **Min-Fill findet nicht die beste Zerlegung.** Die Schranke 3 (k − 1) − 1 gilt für die beste Zerlegung; die Heuristik liegt ab k = 5 darüber.
- **Nur unabhängige Mengen.** Die Knotenüberdeckung ist das Komplement, aber die Güte überträgt sich nicht (ein Stern hat Überdeckung 1).
- **Optimum mit Zeitgrenze.** `scipy.milp` rechnet bis n = 400 in Sekunden; darüber bezieht sich die Reihe auf die beste bekannte Größe.
- **Zeiten gelten für diese Umsetzung.** Reines Python, ein Rechner, ein Lauf je Karte; Lokalsuche mit festem Zufalls-Seed.
- **Zufallskarten.** Die Zahlen gelten für Delaunay-Karten mit gleichverteilten Standorten, dünne Karten und Gitter; echte Netze haben andere Strukturen.
- **Literatur nicht im Original gelesen.** Baker (1994), Bodlaender (Baumweite k-außenplanarer Graphen), Bidimensionalität: nur als Einordnung, Angaben vor einer Zitation zu prüfen. Näherungsschemata für weitere Probleme auf planaren Graphen (Travelling Salesman, Steinerbaum) sind nicht nachgebaut.

## Befunde und Korrekturen gegenüber dem Plan

- **Wurzel und Pläne:** die Vormessung im Einzelplan lief mit Knoten 0 als Wurzel und je drei Seeds; die Demo nimmt die Mitte der Karte und fünf feste Pläne (100000 bis 100004). Einzelwerte weichen ab, die Richtungen sind dieselben (Baker bei k = 5 und n = 400: 116 im Median gegen 115 bis 119 in der Vormessung).
- **Beutelbreite gegen die Schranke:** der Plan nannte „ab k = 4 über der Schranke“; im Median der Reihe liegt die größte Breite bei k = 4 genau auf der Schranke (8), erst ab k = 5 darüber (12 gegen 11). Einzelne Pläne der Vormessung lagen bei k = 4 schon darüber.
- **Zellbudget:** der Plan erwartete den Abbruch bei k = 8 erst ab n = 1 600; mit der Wurzel in der Mitte brechen schon bei n = 400 18 von 40 Verschiebungen ab.
- **Dünne Karte:** in der Vormessung lag Baker ab k = 5 über Greedy (138 gegen 137 bis 142); in der Reihe erst bei k = 8 (147 gegen 142), bei k = 5 darunter (141 gegen 142).
- **Preset „Großes k = 6“** statt k = 7: k = 7 braucht etwa 2 s und bricht bei Seed 35 eine Verschiebung ab.
- **Port:** 9133 statt 9132 (9132 hat inzwischen `quellensuche-demo` bekommen).

## Verifikation

- **Kern gegen Handrechnung** (`tests/test_algorithm.py`): BFS-Schichten (Weg, Stern, 3 × 3-Gitter, mehrere Komponenten), gelöschte Schichten und Reste, Baker an Weg, Stern und Gitter mit allen Verschiebungen von Hand, Gleichstand zur kleineren Verschiebung, Abbruch am Zellbudget (ganz und teilweise), Garantie und Schranke als reine Funktionen, Dreiecks-Bedingungen, `milp`-Optimum.
- **Orakel:** `tests/test_oracle_baker.py`: Baker gegen Brute Force (26 Graphen), gegen ein zweites ganzzahliges Programm nur mit Kantenbedingungen (24 Graphen mit 60 Knoten), gegen die DP über den ganzen Graphen (15 Graphen); jede Verschiebung unabhängig, ohne Knoten der gelöschten Schichten, keine Kante zwischen verschiedenen Resten, Reste aus höchstens k − 1 Schichten; der Kern des Beweises (die Klassen einer größten Menge verlieren im besten Fall höchstens ein k-tel).
- **Szenario, Randfälle, Auswertung, Darstellung:** Gitter, Karten, Wurzelwahl (`tests/test_scenario.py`); einzelner Knoten, isolierte Knoten, vollständiger Graph, k größer als die Höhe, kleinste Graphen an allen Reglergrenzen (`tests/test_edge_cases.py`); Messreihen (`tests/test_evaluation.py`); Spuren der Zeichnung (`tests/test_visualization.py`).
- **Verdikte** als reine Funktionen, jede Zahl im Text (`tests/test_verdicts.py`); **Claims:** jede Zahl dieser README (`tests/test_claims.py`); Presets halten, was ihre Hilfetexte sagen.
- **Mutationsprüfung** (`tools/mutate_demo.py`, Stand vor dem ersten Commit): 108 von 170 Stellen der Module gesichert (104 gefangen, dazu 4 durch wortgleiche Zeilen des kopierten `bkr_exact.py` in Nachbar-Demos; `tests/mutation_state.json`), keine überlebende Stelle; 62 Mutanten ergaben Zeitüberschreitungen (Endlosschleifen, zählen nicht). Im ersten Lauf überlebten 2 Mutanten der kopierten Funktion `fill_count` (Konstante in der Füllzahl); `tests/test_exact.py` fängt sie, von Hand nachgeprüft. Der Lauf lief mit grüner Gesamtsuite im Ausgangslauf und ohne alte Bytecode-Dateien (`PYTHONDONTWRITEBYTECODE=1`).
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler an beiden Enden), Layout, Footer, Laufzeit-Importe.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `bkr_algorithm.py` | Kern: Schichten, Reste, Baker mit Verschiebungen, Garantie, Schranke, `milp`-Optimum |
| `bkr_exact.py` | Eliminationsordnung, Zerlegung und DP für die größte unabhängige Menge (gekürzte Kopie aus `mis-local-search-demo`, dort aus `tree-decomposition-dp-demo`) |
| `bkr_search.py` | Greedy und Lokalsuche (Kopie aus `mis-local-search-demo`) |
| `bkr_constants.py` | Regler-Grenzen, Rechengrenzen, feste Pläne, Farben, Presets |
| `bkr_evaluation.py` | Analyse, Urteile (reine Funktionen), Messreihen |
| `bkr_scenario.py` | Delaunay-Karten, dünne Karten, Gitter, Wurzelwahl |
| `bkr_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `bkr_layout.py` | Fester Kopf (Stylesheet) |
| `bkr_presets.py` | Permalink (Begrenzen), Presets (Schnellstart oben, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Handrechnung, Orakel, Szenario, Randfälle, Verdikte, Claims, Darstellung, Presets, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Knotenüberdeckung mit Garantie:** die Güte überträgt sich nicht auf das Komplement; eigene Aufgabe.
- **Näherungsschemata für weitere Probleme** (planares Travelling Salesman, Steinerbaum) und **Algorithmen mit Laufzeit 2^O(√k)** über Bidimensionalität: nur Einordnung.
- **Beste Zerlegung statt Min-Fill:** exakte Baumweite ist selbst schwer; die Schranke wird nur gemessen, nicht erreicht.
- **Eigene Wurzelsuche** (Wurzel mit kleinster Exzentrizität): nur Mitte und Rand.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und SciPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
