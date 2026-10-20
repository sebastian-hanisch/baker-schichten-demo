"""Plotly-Abbildungen: die Karte mit Schichten und Lösung, die k Verschiebungen, Güte und Zeit über k, Beutelbreite gegen Schranke, Größenreihe, Sonderfälle, DP-Kosten.
Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

from __future__ import annotations

import plotly.graph_objects as go

import bkr_constants as C


def _frame(fig, title=None, height=520):
    fig.update_layout(title=dict(text=title, x=0, font=dict(size=14)) if title else None, height=height, margin=dict(l=10, r=10, t=40 if title else 10, b=10),
                      plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
    fig.update_xaxes(visible=False, fixedrange=True, constrain="domain")
    fig.update_yaxes(visible=False, fixedrange=True, scaleanchor="x", scaleratio=1, constrain="domain")
    return fig


def build_map(graph, layer, k, best, title=None, height=520):
    """Die Karte: Kanten grau, Knoten nach Schicht gefärbt (Farbskala von der Wurzel nach außen), gelöschte Schicht der besten Verschiebung als graue Kreuze, gewählte Knoten groß und dunkelgrün.
    `best` ist die beste Verschiebung (`Shift`) oder None, wenn alle abbrachen."""
    xs, ys = [], []
    for u, v in graph.edges():
        xs += [graph.pos[u][0], graph.pos[v][0], None]
        ys += [graph.pos[u][1], graph.pos[v][1], None]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_EDGE, width=0.8), hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=[p[0] for p in graph.pos], y=[p[1] for p in graph.pos], mode="markers", marker=dict(size=6, color=list(layer), colorscale=[[0, "#1f4e79"], [1, "#d6e4f0"]], line=dict(width=0)),
        hovertext=[f"Knoten {v}, Schicht {layer[v]}" for v in range(graph.n)], hoverinfo="text"))
    if best is not None:
        deleted = [v for v in range(graph.n) if layer[v] % k == best.shift]
        fig.add_trace(go.Scatter(x=[graph.pos[v][0] for v in deleted], y=[graph.pos[v][1] for v in deleted], mode="markers", marker=dict(symbol="x", size=7, color=C.COLOR_DELETED), hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=[graph.pos[v][0] for v in best.chosen], y=[graph.pos[v][1] for v in best.chosen], mode="markers", marker=dict(size=9, color=C.COLOR_CHOSEN, line=dict(color="white", width=1)),
                                 hovertext=[f"Knoten {v} gewählt" for v in best.chosen], hoverinfo="text"))
    return _frame(fig, title, height)


def _layout(fig, title, height=340, y_title=None, x_title=None, log_y=False):
    fig.update_layout(title=dict(text=title, x=0, font=dict(size=14)) if title else None, height=height, margin=dict(l=10, r=10, t=40 if title else 10, b=10),
                      legend=dict(orientation="h", y=-0.25, x=0), plot_bgcolor="rgba(0,0,0,0)")
    fig.update_xaxes(fixedrange=True, title=x_title)
    fig.update_yaxes(fixedrange=True, title=y_title, type="log" if log_y else "linear")
    return fig


def build_shifts(shifts, greedy, ils, opt=None, guarantee=None):
    """Lösungsgröße je Verschiebung (abgebrochene fehlen), die beste hervorgehoben; Linien für Greedy, Lokalsuche, das Optimum und die Garantie (falls bekannt)."""
    done = [s for s in shifts if not s.aborted]
    best = max(done, key=lambda s: (len(s.chosen), -s.shift)) if done else None
    labels = [str(s.shift) for s in shifts]
    fig = go.Figure(go.Bar(
        x=labels, y=[None if s.aborted else len(s.chosen) for s in shifts], marker_color=[C.COLOR_CHOSEN if s is best else C.COLOR_BAKER for s in shifts],
        hovertemplate="Verschiebung %{x}: %{y} Knoten<extra></extra>", name="Baker"))
    fig.add_hline(y=greedy, line=dict(color=C.COLOR_GREEDY, dash="dash"), annotation_text="Greedy", annotation_position="top left")
    fig.add_hline(y=ils, line=dict(color=C.COLOR_ILS, dash="dot"), annotation_text="Lokalsuche", annotation_position="top right")
    if opt is not None:
        fig.add_hline(y=opt, line=dict(color=C.COLOR_OPT), annotation_text="Optimum", annotation_position="top left")
        if guarantee is not None:
            fig.add_hline(y=guarantee * opt, line=dict(color=C.COLOR_BOUND, dash="dash"), annotation_text="Garantie", annotation_position="bottom left")
    fig.update_xaxes(type="category")
    return _layout(fig, "Lösungsgröße je Verschiebung", x_title="Verschobene Schicht i (gelöscht werden die Schichten j ≡ i mod k)", y_title="Unabhängige Knoten")


def build_quality(rows):
    """Anteil am Optimum (Median) über k: Baker, die Garantie 1 − 1/k, Greedy und Lokalsuche als waagerechte Linien."""
    ks = [r["k"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ks, y=[r["baker_quota"] for r in rows], mode="lines+markers", line=dict(color=C.COLOR_BAKER, width=3), name="Baker", hovertemplate="k = %{x}: %{y:.3f}<extra>Baker</extra>"))
    fig.add_trace(go.Scatter(x=ks, y=[r["guarantee"] for r in rows], mode="lines+markers", line=dict(color=C.COLOR_BOUND, dash="dash"), name="Garantie 1 − 1/k", hovertemplate="k = %{x}: %{y:.3f}<extra>Garantie</extra>"))
    fig.add_trace(go.Scatter(x=ks, y=[r["greedy_quota"] for r in rows], mode="lines", line=dict(color=C.COLOR_GREEDY, dash="dash"), name="Greedy", hovertemplate="%{y:.3f}<extra>Greedy</extra>"))
    fig.add_trace(go.Scatter(x=ks, y=[r["ils_quota"] for r in rows], mode="lines", line=dict(color=C.COLOR_ILS, dash="dot"), name="Lokalsuche", hovertemplate="%{y:.3f}<extra>Lokalsuche</extra>"))
    fig.update_xaxes(dtick=1)
    return _layout(fig, "Anteil am Optimum (Median)", x_title="k", y_title="Größe / Optimum")


def build_time(rows):
    """Zeit des Baker je k (Median, logarithmisch) und größter Beutel (Beschriftung)."""
    fig = go.Figure(go.Scatter(x=[r["k"] for r in rows], y=[r["time"] * 1000 for r in rows], mode="lines+markers+text", text=[f"Beutel {r['bag']}" for r in rows], textposition="top center",
                               line=dict(color=C.COLOR_BAKER, width=3), hovertemplate="k = %{x}: %{y:.1f} ms<extra></extra>"))
    fig.update_xaxes(dtick=1)
    return _layout(fig, "Zeit des Baker (Median, logarithmisch)", x_title="k", y_title="Millisekunden", log_y=True)


def build_width(rows):
    """Gemessene Breite (größter Beutel minus 1) gegen die Schranke 3 (k − 1) − 1."""
    ks = [r["k"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ks, y=[r["bag"] - 1 for r in rows], mode="lines+markers", line=dict(color=C.COLOR_BAKER, width=3), name="Min-Fill (gemessen)", hovertemplate="k = %{x}: %{y}<extra>Min-Fill</extra>"))
    fig.add_trace(go.Scatter(x=ks, y=[r["width_bound"] for r in rows], mode="lines+markers", line=dict(color=C.COLOR_BOUND, dash="dash"), name="3 (k − 1) − 1", hovertemplate="k = %{x}: %{y}<extra>Schranke</extra>"))
    fig.update_xaxes(dtick=1)
    return _layout(fig, "Breite der Zerlegung gegen die Schranke", x_title="k", y_title="Breite")


def build_sizes(rows):
    """Anteil an der besten bekannten Größe je Kartengröße: Baker, Greedy, Lokalsuche."""
    labels = [f"n = {r['n']}" for r in rows]
    fig = go.Figure()
    for key, name, color in (("baker_quota", "Baker", C.COLOR_BAKER), ("greedy_quota", "Greedy", C.COLOR_GREEDY), ("ils_quota", "Lokalsuche", C.COLOR_ILS)):
        fig.add_trace(go.Bar(x=labels, y=[r[key] for r in rows], name=name, marker_color=color, hovertemplate="%{y:.3f}<extra>" + name + "</extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(range=[0.7, 1.02])
    return _layout(fig, "Anteil an der besten bekannten Größe (Median)", y_title="Größe / beste bekannte")


def build_special(rows, net, names):
    """Baker je k auf einem Sonderfall gegen Greedy, Lokalsuche und Optimum (Linien)."""
    mine = [r for r in rows if r["net"] == net]
    fig = go.Figure(go.Bar(x=[str(r["k"]) for r in mine], y=[r["baker"] for r in mine], marker_color=C.COLOR_BAKER, name="Baker", hovertemplate="k = %{x}: %{y}<extra></extra>"))
    fig.add_hline(y=mine[0]["greedy"], line=dict(color=C.COLOR_GREEDY, dash="dash"), annotation_text="Greedy", annotation_position="top left")
    fig.add_hline(y=mine[0]["ils"], line=dict(color=C.COLOR_ILS, dash="dot"), annotation_text="Lokalsuche", annotation_position="top right")
    fig.add_hline(y=mine[0]["opt"], line=dict(color=C.COLOR_OPT), annotation_text="Optimum", annotation_position="bottom right")
    fig.update_xaxes(type="category")
    return _layout(fig, names[net], height=300, x_title="k", y_title="Unabhängige Knoten")


def build_dp(rows):
    """Vorhergesagte Zellen der DP über den ganzen Graphen (Median, logarithmisch) gegen das Zellbudget."""
    fig = go.Figure(go.Scatter(x=[r["n"] for r in rows], y=[r["predicted"] for r in rows], mode="lines+markers+text", text=[f"Beutel {num_bag(r['bag'])}" for r in rows], textposition="top left",
                               line=dict(color=C.COLOR_BAKER, width=3), hovertemplate="n = %{x}: %{y:.2e} Zellen<extra></extra>"))
    fig.add_hline(y=rows[0]["budget"], line=dict(color=C.COLOR_BOUND, dash="dash"), annotation_text="Zellbudget", annotation_position="bottom right")
    fig.update_xaxes(type="category")
    return _layout(fig, "DP über den ganzen Graphen: vorhergesagte Zellen", x_title="Standorte n", y_title="Zellen", log_y=True)


def num_bag(x) -> str:
    return str(int(x)) if float(x) == int(x) else str(x).replace(".", ",")
