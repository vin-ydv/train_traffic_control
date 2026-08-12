"""Dark control-room theme + Plotly map drawing helpers."""
from __future__ import annotations

import plotly.graph_objects as go

from engine.model import PRIORITY_COLOR, PRIORITY_LABEL

BG = "#0b0f19"
PANEL = "#0f172a"
CARD = "#1e293b"
TEXT = "#f1f5f9"
MUTED = "#94a3b8"
ACCENT = "#38bdf8"
GREEN = "#22c55e"
RED = "#ef4444"
AMBER = "#f59e0b"
PURPLE = "#a855f7"


def inject_css(st) -> None:
    st.markdown(
        f"""
        <style>
        .stApp {{ background: {BG}; color: {TEXT}; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
        section[data-testid="stSidebar"] {{ background: {PANEL}; border-right: 1px solid #1e293b; }}
        .kpi-card {{
            background: {CARD};
            padding: 16px 20px;
            border-radius: 12px;
            border: 1px solid #334155;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
            margin-bottom: 12px;
        }}
        .kpi-label {{
            color: {MUTED};
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 600;
        }}
        .kpi-value {{
            font-size: 2.1rem;
            font-weight: 800;
            margin-top: 4px;
        }}
        .rec-card {{
            background: {CARD};
            padding: 16px;
            border-radius: 12px;
            border-left: 5px solid {ACCENT};
            border: 1px solid #334155;
            margin-bottom: 14px;
        }}
        .badge-ok {{ color: {GREEN}; font-weight: 700; }}
        .badge-bad {{ color: {RED}; font-weight: 700; }}
        .small {{ color: {MUTED}; font-size: 0.85rem; }}
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
            background-color: {PANEL};
            padding: 6px;
            border-radius: 10px;
            border: 1px solid #334155;
        }}
        .stTabs [data-baseweb="tab"] {{
            height: 40px;
            background-color: transparent;
            border-radius: 8px;
            color: {TEXT};
            font-weight: 600;
            padding: 0 16px;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {ACCENT} !important;
            color: #0b0f19 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, good: bool | None = None) -> str:
    cls = ""
    if good is True:
        cls = "badge-ok"
    elif good is False:
        cls = "badge-bad"
    return (
        f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value {cls}">{value}</div></div>'
    )


def draw_map(sim) -> go.Figure:
    net = sim.net
    fig = go.Figure()

    for blk in net.blocks:
        x1, y1, x2, y2 = net.block_xy(blk)
        occupied = bool(blk.occupant_up or blk.occupant_down)
        color = AMBER if (occupied and not blk.double_line) else "#475569"
        width = 6 if blk.double_line else 4
        dash = None if blk.double_line else "dot"
        fig.add_trace(go.Scatter(
            x=[x1, x2], y=[y1, y2], mode="lines",
            line=dict(color=color, width=width, dash=dash),
            hoverinfo="text",
            text=f"{blk.id} · {blk.length_km}km · "
                 f"{'double' if blk.double_line else 'single'} line"
                 + (" · OCCUPIED" if occupied else ""),
            showlegend=False,
        ))

    for c in sim.upcoming_conflicts(horizon=20):
        blk = next(b for b in net.blocks if b.id == c["block"])
        x1, y1, x2, y2 = net.block_xy(blk)
        fig.add_trace(go.Scatter(
            x=[x1, x2], y=[y1, y2], mode="lines",
            line=dict(color=RED, width=12), opacity=0.25,
            hoverinfo="text", text=f"Conflict in {c['in_min']}m",
            showlegend=False,
        ))

    sx, sy, slabel = [], [], []
    for s in net.stations.values():
        sx.append(s.x); sy.append(s.y); slabel.append(s.id)
    fig.add_trace(go.Scatter(
        x=sx, y=sy, mode="markers+text",
        marker=dict(size=14, color=ACCENT, line=dict(width=2, color="#0ea5e9")),
        text=slabel, textposition="top center",
        hovertext=[f"{s.name}<br>Loops: {s.loops}" for s in net.stations.values()],
        hoverinfo="text", name="Stations",
    ))

    for t in sim.trains:
        if not t.entered_section or t.finished:
            continue
        x, y = sim.train_position(t)
        fig.add_trace(go.Scatter(
            x=[x], y=[y + 1.8], mode="markers+text",
            marker=dict(size=18, color=PRIORITY_COLOR[t.priority],
                        line=dict(width=2, color="#000")),
            text=[t.number], textposition="middle center",
            textfont=dict(size=9, color="white"),
            hoverinfo="text",
            hovertext=(f"<b>{t.number} {t.name}</b><br>"
                       f"{t.type} · pax {t.pax}<br>"
                       f"{'At ' + t.at_station if t.at_station else 'On ' + (t.on_block or '')}<br>"
                       f"Delay: {max(0, sim.time - t.planned_dep):.0f}m"),
            showlegend=False,
        ))

    fig.update_layout(
        paper_bgcolor=BG, plot_bgcolor=BG, font=dict(color=TEXT),
        margin=dict(l=10, r=10, t=30, b=10), height=480,
        xaxis=dict(visible=False, showgrid=False, zeroline=False),
        yaxis=dict(visible=False, showgrid=False, zeroline=False, scaleanchor="x", scaleratio=1),
        title=dict(text=f"RailMind Live · T+{sim.time} min · {sim.mode.upper()} mode",
                   font=dict(size=16)),
        annotations=[],
    )
    return fig


def legend_html() -> str:
    parts = []
    for p, c in PRIORITY_COLOR.items():
        parts.append(
            '<span style="display:inline-block;margin-right:14px;">'
            f'<span style="display:inline-block;width:10px;height:10px;'
            f'border-radius:50%;background:{c};margin-right:6px;"></span>'
            f'{PRIORITY_LABEL[p]}</span>'
        )
    items = "".join(parts)
    return f'<div class="small" style="margin:6px 0 10px;">{items}</div>'
