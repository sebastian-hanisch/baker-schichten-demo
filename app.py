"""Schichten zerlegen – die Baker-Technik - interaktive Fall-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import bkr_algorithm as A
import bkr_constants as C
import bkr_evaluation as ev
from bkr_layout import dunkles_design, kopf_css
from bkr_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from bkr_visualization import build_dp, build_map, build_quality, build_shifts, build_sizes, build_special, build_time, build_width

st.set_page_config(page_title="Schichten zerlegen – Baker-Technik – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return ev.analyse(settings)


@st.cache_data(show_spinner=False)
def _optimum(settings):
    return ev.optimum_for(settings)


@st.cache_data(show_spinner=False)
def _quality():
    return ev.quality_series()


@st.cache_data(show_spinner=False)
def _sizes():
    return ev.size_series()


@st.cache_data(show_spinner=False)
def _special():
    return ev.special_series()


@st.cache_data(show_spinner=False)
def _dp():
    return ev.dp_series()


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in bkr_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧱 Schichten zerlegen – die Baker-Technik")
st.markdown(
    """
Auf einer Karte sollen möglichst viele Orte gewählt werden, von denen keine zwei benachbart sind (die **größte unabhängige Menge**). Das ist schwer, auch auf planaren Karten. Die **Baker-Technik** macht daraus ein **Näherungsschema**:
Man sucht von einem Ort aus Schicht für Schicht (Breitensuche), **löscht jede k-te Schicht**, und was übrig bleibt, zerfällt in Reste aus höchstens k − 1 Schichten, die so schmal sind, dass man sie **exakt** lösen kann (Dynamische Programmierung auf einer Baumzerlegung).
Von den k möglichen Verschiebungen nimmt man die beste und hat **garantiert mindestens (1 − 1/k) des Optimums**; die Rechenzeit wächst dafür stark mit k.
Die Demo misst, wie gut das in der Praxis ist, gegen **Greedy** und die **Lokalsuche** aus `mis-local-search-demo` und gegen das **Optimum** (`scipy.milp`), und was es kostet. Der Befund ist **zweiseitig**: die Garantie hält und die Praxis liegt weit darüber,
aber auf diesen Karten ist die Lokalsuche in Güte **und** Zeit überlegen; der Wert der Technik ist die Garantie, nicht die Güte.
Siebtes Stück der Linie *Planarität und Zeichnen*; Verwandte: `tree-decomposition-dp-demo` (die exakte DP), `mis-local-search-demo`, `planar-separator-demo` (BFS-Schichten als Trennmenge).

Weiter unten: **🔬 Die k Verschiebungen**, **🔬 Messreihen** (Güte und Zeit über k, über die Größe, Sonderfälle, ganzer Graph per DP), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert die Technik", expanded=True):
    st.markdown(
        """
1. **Schichten:** Die Breitensuche von der Wurzel gibt jedem Ort eine Schicht (Abstand zur Wurzel). Die Farbskala der Karte zeigt sie.
2. **Löschen:** Für eine Verschiebung i werden alle Schichten j mit j ≡ i (mod k) gelöscht (graue Kreuze). Die übrigen Orte zerfallen in **Reste aus höchstens k − 1 aufeinanderfolgenden Schichten**; zwischen zwei Resten liegt immer eine gelöschte Schicht, also gibt es keine Kante zwischen Resten.
3. **Reste exakt lösen:** Ein Rest aus wenigen Schichten eines planaren Graphen hat kleine Baumweite (Literatur: höchstens 3 (k − 1) − 1). Die Dynamische Programmierung über eine Min-Fill-Zerlegung findet seine größte unabhängige Menge. Die Lösungen der Reste zusammen sind unabhängig.
4. **Beste Verschiebung:** Jeder Knoten einer größten Menge liegt in genau einer gelöschten Schicht-Klasse, im Mittel über die k Verschiebungen gehen also höchstens 1/k der Knoten verloren; die beste Verschiebung hat **mindestens (1 − 1/k) · OPT**.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    net = st.selectbox("Graph", list(C.NET_TYPES), key="net_select", format_func=C.NET_TYPES.get, help=C.NET_HELP)
    n = st.slider("Knoten n", *bounds("n_slider"), key="n_slider", help="Beim Gitter wird die Seite Wurzel aus n gerundet (n wird also k²).")
    k = st.slider("k (jede k-te Schicht löschen)", *bounds("k_slider"), key="k_slider", help="Garantie (1 − 1/k) des Optimums; Reste aus k − 1 Schichten; die Zeit wächst etwa um den Faktor 3 bis 4 je Schritt.")
    root = st.selectbox("Wurzel der Breitensuche", list(C.ROOTS), key="root_select", format_func=C.ROOTS.get, help=C.ROOT_HELP)
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)

sync_query_params({"net_select": net, "n_slider": int(n), "k_slider": int(k), "root_select": root, "seed_input": int(seed)})

settings = ev.Settings(net, int(n), int(k), root, int(seed))
a = _analysis(settings)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Graph", f"{a.graph.n} Knoten", delta=f"{ev.num(a.graph.m)} Kanten, {a.baker.height} Schichten", delta_color="off", help="Knoten, Kanten und Zahl der Schichten der Breitensuche von der Wurzel (weitere Stücke zählen mit).")
m2.metric("Baker", "abgebrochen" if a.baker_size is None else ev.num(a.baker_size), delta=f"k = {k}, Garantie {ev.percent(A.guarantee_ratio(k))}", delta_color="off", help="Unabhängige Knoten der besten Verschiebung.")
m3.metric("Greedy", ev.num(a.greedy_size), delta="kleinster Grad zuerst", delta_color="off")
m4.metric("Lokalsuche", ev.num(a.ils_size), delta=f"{ev.num(C.ILS_ITERATIONS)} Iterationen, {ev.ms_text(a.ils_time)}", delta_color="off", help="Iterierte Lokalsuche aus `mis-local-search-demo`, ein Lauf mit festem Zufalls-Seed.")
can_opt = a.graph.n <= C.OPT_MAX_N
if can_opt and st.button("Optimum für diese Karte berechnen", key="opt_start", help=f"`scipy.milp` mit Dreiecks-Cliquen, Zeitgrenze {int(C.OPT_TIME_LIMIT)} s."):
    st.session_state["opt_for"] = settings
opt = None
if can_opt and st.session_state.get("opt_for") == settings:
    with st.spinner("Rechne das Optimum..."):
        opt = _optimum(settings)
elif not can_opt:
    st.caption(f"Das Optimum rechnet die App bis n = {C.OPT_MAX_N} auf Klick (darüber dauert das ganzzahlige Programm zu lange).")
kind, text = ev.verdict_baker(a, opt)
getattr(st, kind)(text)
st.plotly_chart(build_map(a.graph, a.baker.layers, k, a.baker.best, title=f"{a.graph.name}: Baker mit k = {k}"), width="stretch", key="main_chart")
st.caption(
    "Knoten nach Schicht gefärbt (dunkel = nah an der Wurzel), graue Kreuze: die gelöschte Schicht der besten Verschiebung, grün: die gewählten Knoten. "
    f"Zeit des Baker: {ev.ms_text(a.baker_time)}, größter Beutel {a.baker.max_bag}, {ev.num(a.baker.cells)} Tabellenzellen in allen Verschiebungen."
)

st.markdown("---")

# --- Die k Verschiebungen ----------------------------------------------------------------------------------------------------------------------

st.markdown("## 🔬 Die k Verschiebungen")
kind, text = ev.verdict_shifts(a)
getattr(st, kind)(text)
st.dataframe(
    [{"Verschiebung": s.shift, "Reste": s.pieces, "Gewählte Knoten": "abgebrochen" if s.aborted else len(s.chosen), "Größter Beutel": s.max_bag, "Zellen": ev.num(s.cells)} for s in a.baker.shifts],
    hide_index=True, width="stretch",
)
st.plotly_chart(build_shifts(a.baker.shifts, a.greedy_size, a.ils_size, opt.value if opt is not None else None, A.guarantee_ratio(k) if opt is not None else None), width="stretch", key="chart_shifts")

st.markdown("---")

# --- Messreihen ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🔬 Messreihen")
st.markdown(
    f"Feste Pläne ({len(C.SWEEP_SEEDS)} je Zeile, Mediane), Wurzel in der Mitte. Größen und Zellen sind exakt, Zeiten gelten für diese Umsetzung und diesen Rechner (reines Python). "
    "Das Optimum ist das ganzzahlige Programm (`scipy.milp`)."
)
tab_quality, tab_sizes, tab_special, tab_dp = st.tabs(["Güte und Zeit über k", "Über die Größe", "Gitter und dünne Karten", "Warum nicht gleich alles per DP"])

with tab_quality:
    st.caption(f"Karten mit n = {C.QUALITY_N}, k = {', '.join(str(x) for x in C.QUALITY_KS)}: Baker gegen das Optimum, Greedy und Lokalsuche.")
    if st.button("Güte über k messen (etwa 40 Sekunden)", key="quality_start"):
        st.session_state["quality_done"] = True
    if st.session_state.get("quality_done"):
        with st.spinner("Rechne die Optima und den Baker für jedes k..."):
            rows = _quality()
        getattr(st, ev.verdict_quality(rows)[0])(ev.verdict_quality(rows)[1])
        st.dataframe(
            [{"k": r["k"], "Baker": ev.num(r["baker"], 1), "Anteil am Optimum": ev.percent(r["baker_quota"]), "Garantie": ev.percent(r["guarantee"]), "Greedy": ev.num(r["greedy"], 1), "Lokalsuche": ev.num(r["ils"], 1),
              "Optimum": ev.num(r["opt"], 1), "Über Greedy": f"{r['above_greedy']} von {r['plans']}", "Garantie gehalten": f"{r['meets']} von {r['finished']}", "Abgebrochene Verschiebungen": r["aborted"], "Zeit (Median)": ev.ms_text(r["time"]), "Größter Beutel": r["bag"]} for r in rows],
            hide_index=True, width="stretch",
        )
        left, right = st.columns(2)
        left.plotly_chart(build_quality(rows), width="stretch", key="chart_quality")
        right.plotly_chart(build_time(rows), width="stretch", key="chart_time")
        getattr(st, ev.verdict_width(rows)[0])(ev.verdict_width(rows)[1])
        st.plotly_chart(build_width(rows), width="stretch", key="chart_width")
with tab_sizes:
    st.caption(f"Karten mit n = {', '.join(str(x) for x in C.SIZE_SERIES)} und k = {C.SIZE_SERIES_K}: Baker gegen Greedy und Lokalsuche; das Optimum nur bis n = {C.OPT_MAX_N} (darüber bezieht sich der Anteil auf die beste bekannte Größe).")
    if st.button("Über die Größe messen (etwa 20 Sekunden)", key="sizes_start"):
        st.session_state["sizes_done"] = True
    if st.session_state.get("sizes_done"):
        with st.spinner("Messe Baker, Greedy und Lokalsuche..."):
            rows = _sizes()
        getattr(st, ev.verdict_sizes(rows)[0])(ev.verdict_sizes(rows)[1])
        st.dataframe(
            [{"Karte": f"n = {r['n']}", "Baker": ev.num(r["baker"], 1), "Greedy": ev.num(r["greedy"], 1), "Lokalsuche": ev.num(r["ils"], 1), "Optimum": "-" if r["opt"] is None else ev.num(r["opt"], 1),
              "Baker (Anteil)": ev.percent(r["baker_quota"]), "Zeit Baker": ev.ms_text(r["baker_time"]), "Zeit Lokalsuche": ev.ms_text(r["ils_time"]), "Abgebrochene Verschiebungen": r["aborted"]} for r in rows],
            hide_index=True, width="stretch",
        )
        st.plotly_chart(build_sizes(rows), width="stretch", key="chart_sizes")
with tab_special:
    st.caption(f"Gitter mit Diagonalen und Gitter ({C.SPECIAL_SIDE} × {C.SPECIAL_SIDE}) und eine dünne Karte mit {C.SPECIAL_SIDE ** 2} Standorten, k = {', '.join(str(x) for x in C.SPECIAL_KS)}; je ein fester Graph.")
    if st.button("Sonderfälle messen (einige Sekunden)", key="special_start"):
        st.session_state["special_done"] = True
    if st.session_state.get("special_done"):
        with st.spinner("Messe die Sonderfälle..."):
            rows = _special()
        getattr(st, ev.verdict_special(rows)[0])(ev.verdict_special(rows)[1])
        st.dataframe(
            [{"Graph": C.NET_TYPES[r["net"]], "k": r["k"], "Baker": ev.num(r["baker"]), "Anteil am Optimum": ev.percent(r["baker_quota"]), "Garantie": ev.percent(r["guarantee"]), "Greedy": r["greedy"],
              "Lokalsuche": r["ils"], "Optimum": r["opt"]} for r in rows],
            hide_index=True, width="stretch",
        )
        cols = st.columns(3)
        for col, net_key in zip(cols, ("grid_diag", "grid", "thin")):
            col.plotly_chart(build_special(rows, net_key, C.NET_TYPES), width="stretch", key=f"chart_special_{net_key}")
with tab_dp:
    st.caption(f"Delaunay-Karten mit n = {', '.join(str(x) for x in C.DP_SIZES)}: die Dynamische Programmierung über eine Min-Fill-Zerlegung des **ganzen** Graphen, Zellbudget {ev.num(C.DP_BUDGET)}.")
    if st.button("Ganzen Graphen per DP prüfen (einige Sekunden)", key="dp_start"):
        st.session_state["dp_done"] = True
    if st.session_state.get("dp_done"):
        with st.spinner("Zerlege die Karten..."):
            rows = _dp()
        getattr(st, ev.verdict_dp(rows)[0])(ev.verdict_dp(rows)[1])
        st.dataframe(
            [{"Karte": f"n = {r['n']}", "Größter Beutel": ev.num(r["bag"], 1), "Vorhergesagte Zellen": f"{r['predicted']:.2e}".replace(".", ","), "Über dem Budget": f"{r['aborted']} von {r['plans']}"} for r in rows],
            hide_index=True, width="stretch",
        )
        st.plotly_chart(build_dp(rows), width="stretch", key="chart_dp")

st.markdown("---")

# --- Wo die Annahmen enden -------------------------------------------------------------------------------------------------------------------

st.markdown("## 🚧 Wo die Annahmen enden")
st.markdown(
    f"""
- **Die Technik ist ein Garantieverfahren, kein Praxisverfahren.** Auf diesen Karten ist die Lokalsuche in Güte und Zeit besser. Der Wert der Baker-Technik ist der Satz: beliebig nah ans Optimum bei beschränkter Baumweite je Rest, bewiesen, nicht gemessen.
- **Zeit wächst stark mit k.** Die Tabellen haben 2^Beutel Zellen, die Beutel wachsen mit k; bei k = 8 brechen schon auf Karten mit 400 Standorten einzelne Verschiebungen beim Zellbudget ({ev.num(C.CELL_BUDGET)}) ab. Die App zeigt abgebrochene Verschiebungen ausdrücklich.
- **Nicht monoton in k.** Auf dem Gitter zerstört ein ungerades k die Parität der Schichten; die Garantie hält trotzdem, aber die Güte kann bei größerem k sinken.
- **Min-Fill findet nicht die beste Zerlegung.** Die Schranke 3 (k − 1) − 1 für die Baumweite eines Rests gilt für die beste Zerlegung; Min-Fill liegt ab k = 5 darüber. Die Schranke ist ein Literaturwert, nicht im Original geprüft.
- **Nur unabhängige Mengen.** Die Knotenüberdeckung ist das Komplement, aber die Güte überträgt sich nicht (ein Stern hat Überdeckung 1).
- **Das Optimum ist ein Programm mit Zeitgrenze.** Bis n = {C.OPT_MAX_N} in Sekunden; darüber wird es nicht gerechnet, die Messreihe über die Größe bezieht sich dann auf die beste bekannte Größe.
- **Zeiten gelten für diese Umsetzung.** Reines Python, ein Rechner, ein Lauf je Karte; die Lokalsuche läuft mit festem Zufalls-Seed.
- **Einordnung.** Verwandt sind Bidimensionalität und Algorithmen mit Laufzeit 2^O(√k) sowie Näherungsschemata für weitere Probleme auf planaren Graphen (Travelling Salesman, Steinerbaum); nicht nachgebaut.
    """
)

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        """
| Symbol | Bedeutung |
|---|---|
| $G=(V,E)$ | planarer Graph mit $n$ Knoten |
| $\\ell(v)$ | Schicht von $v$: Abstand zur Wurzel in der Breitensuche |
| $L_j=\\{v:\\ell(v)=j\\}$ | Schicht $j$ |
| $V_i=\\{v:\\ell(v)\\not\\equiv i \\pmod k\\}$ | Knoten, die bei Verschiebung $i$ bleiben |
| $S_i$ | Vereinigung exakter Lösungen der Komponenten von $G[V_i]$ |

**Reste.** Zwischen zwei Komponenten von $G[V_i]$ liegt eine gelöschte Schicht, also gibt es keine Kante zwischen ihnen, und $S_i$ ist unabhängig. Jede Komponente liegt in höchstens $k-1$ aufeinanderfolgenden Schichten.

**Garantie.** Sei $I^*$ eine größte unabhängige Menge. Die Klassen $I^*\\cap\\bigcup_{j\\equiv i}L_j$ für $i=0,\\dots,k-1$ zerlegen $I^*$; für ein $i$ hat die Klasse höchstens $|I^*|/k$ Elemente, und $I^*\\cap V_i$ ist eine unabhängige Menge in $G[V_i]$. Damit

$$\\max_i |S_i|\\;\\ge\\;|I^*|-\\frac{|I^*|}{k}\\;=\\;\\Bigl(1-\\frac1k\\Bigr)\\,\\mathrm{OPT}.$$

**Baumweite eines Rests** (Literaturwert, Außenplanarität $r\\le k-1$, nicht im Original geprüft): $\\mathrm{tw}\\le 3r-1\\le 3(k-1)-1$.

**Aufwand der Dynamischen Programmierung:** die Tabelle eines Beutels der Größe $b$ hat $2^{b}$ Zellen; bei Beutelgröße höchstens $3(k-1)$ also $O\\bigl(2^{3(k-1)}\\cdot n\\bigr)$ je Verschiebung, insgesamt $O\\bigl(k\\,2^{3(k-1)}\\,n\\bigr)$ (Größenordnung, nicht gemessen).

**Literatur** (nicht im Original gelesen; Angaben vor einer Zitation zu prüfen): B. S. Baker, *Approximation algorithms for NP-complete problems on planar graphs*, Journal of the ACM 41(1) (1994), 153–180. H. L. Bodlaender zur Baumweite von k-außenplanaren Graphen; Demaine, Hajiaghayi u. a. zur Bidimensionalität.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
