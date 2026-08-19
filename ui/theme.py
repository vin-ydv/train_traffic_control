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

    # O(1) block lookup, built once instead of a linear search per conflict.
    blocks_by_id = {b.id: b for b in net.blocks}

    for c in sim.upcoming_conflicts(horizon=20):
        blk = blocks_by_id.get(c["block"])
        if blk is None:
            continue
        x1, y1, x2, y2 = net.block_xy(blk)
        fig.add_trace(go.Scatter(
            x=[x1, x2], y=[y1, y2], mode="lines",
            line=dict(color=RED, width=12), opacity=0.25,
            hoverinfo="text", text=f"Conflict in {c['in_min']}m",
            showlegend=False,
        ))

    sx, sy, slabel = [], [], []
    for s in net.stations.values():
        sx.append(s.x)
        sy.append(s.y)
        slabel.append(s.id)
    fig.add_trace(go.Scatter(
        x=sx, y=sy, mode="markers+text",
        marker=dict(size=14, color=ACCENT, line=dict(width=2, color="#0ea5e9")),
        text=slabel, textposition="top center",
        hovertext=[f"{s.name}<br>Loops: {s.loops}" for s in net.stations.values()],
        hoverinfo="text", name="Stations",
    ))

    # Group trains for unstacking logic
    active_at_stations = {}
    active_on_blocks = {}
    finished_at_stations = {}
    resolved_positions = {}

    for t in sim.trains:
        if t.entered_section and not t.finished:
            if t.at_station is not None:
                active_at_stations.setdefault(t.at_station, []).append(t)
            if t.on_block is not None:
                active_on_blocks.setdefault(t.on_block, []).append(t)
        elif t.finished:
            finished_at_stations.setdefault(t.dest, []).append(t)

    # Draw active trains with unstacking
    for t in sim.trains:
        if not t.entered_section or t.finished:
            continue
            
        base_x, base_y = sim.train_position(t)
        x, y = base_x, base_y
        
        if t.at_station is not None:
            station_trains = sorted(active_at_stations.get(t.at_station, []), key=lambda tr: tr.number)
            idx = station_trains.index(t)
            N = len(station_trains)
            x = base_x + (idx - (N - 1) / 2) * 3.5
            y = base_y + (2.5 if t.direction == "up" else -2.5)
        elif t.on_block is not None:
            block_trains = sorted(active_on_blocks.get(t.on_block, []), key=lambda tr: tr.block_progress_km)
            idx = block_trains.index(t)
            nudge_count = 0
            for j in range(idx):
                other = block_trains[j]
                if other.direction == t.direction and abs(t.block_progress_km - other.block_progress_km) < 2.0:
                    nudge_count += 1
            y = base_y + (2.5 if t.direction == "up" else -2.5)
            y += nudge_count * 1.5 * (1 if t.direction == "up" else -1)
        else:
            y = base_y + (2.5 if t.direction == "up" else -2.5)

        resolved_positions[t.id] = (x, y)
        fig.add_trace(go.Scatter(
            x=[x], y=[y], mode="markers+text",
            marker=dict(size=18, color=PRIORITY_COLOR[t.priority], line=dict(width=2, color="#000")),
            text=[t.number], textposition="middle center",
            textfont=dict(size=9, color="white"),
            hoverinfo="text",
            hovertext=(f"<b>{t.number} {t.name}</b><br>{t.type} · pax {t.pax}<br>"
                       f"{'At ' + t.at_station if t.at_station else 'On ' + (t.on_block or '')}<br>"
                       f"Delay: {max(0, sim.time - t.planned_dep):.0f}m"),
            showlegend=False,
        ))

    # Draw finished trains
    for s_id, f_trains in finished_at_stations.items():
        if s_id not in net.stations:
            continue
        station = net.stations[s_id]
        f_trains = sorted(f_trains, key=lambda tr: tr.number)
        M = len(f_trains)
        for idx, t in enumerate(f_trains):
            x = station.x + (idx - (M - 1) / 2) * 2.5
            y = station.y + (1.0 if t.direction == "up" else -1.0)
            fig.add_trace(go.Scatter(
                x=[x], y=[y], mode="markers",
                marker=dict(size=8, color=PRIORITY_COLOR[t.priority], opacity=0.35),
                hoverinfo="text",
                hovertext=f"FINISHED · {t.number} {t.name}",
                showlegend=False,
            ))

    # status line info
    active_count = len(resolved_positions)
    finished_count = sum(1 for t in sim.trains if t.finished)
    rounded_positions = {(round(pos[0], 1), round(pos[1], 1)) for pos in resolved_positions.values()}
    distinct_positions = len(rounded_positions)
    
    stacked_parts = []
    for s_id, s_trains in sorted(active_at_stations.items()):
        if len(s_trains) >= 2:
            stacked_parts.append(f"{len(s_trains)} at {s_id}")
    stacked_str = ("Stacked: " + ", ".join(stacked_parts)) if stacked_parts else "Stacked: No stacks"
    status_line = f"Active {active_count} · Finished {finished_count} · Distinct positions {distinct_positions} · {stacked_str}"
    title_text = f"RailMind Live · T+{sim.time} min · {sim.mode.upper()} mode<br><span style='font-size:12px;color:{MUTED};'>{status_line}</span>"

    fig.update_layout(
        paper_bgcolor=BG, plot_bgcolor=BG, font=dict(color=TEXT),
        margin=dict(l=10, r=10, t=55, b=10), height=480,
        xaxis=dict(visible=False, showgrid=False, zeroline=False),
        yaxis=dict(visible=False, showgrid=False, zeroline=False, scaleanchor="x", scaleratio=1),
        title=dict(text=title_text, font=dict(size=16)),
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
