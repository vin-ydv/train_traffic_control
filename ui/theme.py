"""Indian Railways Section Control desk theme + Plotly map drawing helpers."""
from __future__ import annotations

import plotly.graph_objects as go

from engine.model import PRIORITY_COLOR, PRIORITY_LABEL

# IR Control Desk palette — DARK operations-room look (not AI blue)
# Real control rooms: dark charcoal, warm industrial tones, signal lamps
PAGE_BG = "#0d1115"        # deep charcoal (control room dark)
HEADER_BG = "#0a0d10"      # near-black header
HEADER_RED = "#c8102e"     # IR red strip (primary accent)
CARD_BG = "#151a1f"        # dark card surface
CARD_BORDER = "#2a3138"    # subtle card border
TEXT = "#e8eae8"           # warm off-white text
MUTED = "#7a8488"          # muted warm grey
SIGNAL_GREEN = "#2eb85c"   # signal lamp green (brighter for dark bg)
SIGNAL_AMBER = "#ffb300"   # signal lamp amber
SIGNAL_RED = "#e84d3a"     # signal lamp red / IR red
PLOT_BG = "#0f1418"        # map background (slightly lighter than page)
RAIL_GREY = "#4a545c"      # rail colour (muted steel)
RAIL_GREY_DARK = "#3a4248" # darker rail for double line

# Backward-compat aliases used by app.py
BG = PAGE_BG
GREEN = SIGNAL_GREEN
RED = SIGNAL_RED
ACCENT = HEADER_RED
PANEL = "#11161a"
CARD = CARD_BG
def inject_css(st) -> None:
    st.markdown(
        f"""
        <style>
        .stApp {{ background: {PAGE_BG}; color: {TEXT}; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
        section[data-testid="stSidebar"] {{ background: {PANEL}; border-right: 1px solid {CARD_BORDER}; }}
        .control-header {{
            background: {HEADER_BG};
            border-bottom: 4px solid {HEADER_RED};
            padding: 12px 20px;
            margin: -1rem -1rem 1.5rem -1rem;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 16px;
        }}
        .control-header__title {{
            color: #fff;
            font-size: 1.25rem;
            font-weight: 700;
            letter-spacing: 0.04em;
        }}
        .control-header__subtitle {{
            color: #9fb0c8;
            font-size: 0.8rem;
            font-weight: 400;
        }}
        .control-header__meta {{
            display: flex;
            gap: 24px;
            margin-left: auto;
            font-size: 0.85rem;
            color: #cbd5e1;
        }}
        .control-header__meta span {{ display: flex; align-items: center; gap: 6px; }}
        .control-header__lamp {{
            width: 10px; height: 10px; border-radius: 50%;
            background: {SIGNAL_GREEN};
            box-shadow: 0 0 6px {SIGNAL_GREEN};
        }}
        .control-header__lamp--violation {{ background: {SIGNAL_RED}; box-shadow: 0 0 6px {SIGNAL_RED}; }}
        .kpi-card {{
            background: {CARD_BG};
            border: 1px solid {CARD_BORDER};
            border-radius: 8px;
            padding: 14px 16px;
            min-height: 84px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        .kpi-label {{
            color: {MUTED};
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 700;
            margin-bottom: 4px;
        }}
        .kpi-value {{
            font-size: 1.85rem;
            font-weight: 800;
            color: {TEXT};
            line-height: 1.1;
        }}
        .kpi-hint {{
            color: {MUTED};
            font-size: 0.7rem;
            margin-top: 2px;
        }}
.kpi-value--good {{ color: {SIGNAL_GREEN}; }}
        .kpi-value--bad {{ color: {SIGNAL_RED}; }}
        .decision-ticket {{
            background: {CARD_BG};
            border: 1px solid {CARD_BORDER};
            border-radius: 8px;
            padding: 16px;
            margin: 8px 0;
        }}
        .decision-ticket__header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
            padding-bottom: 10px;
            border-bottom: 1px solid {CARD_BORDER};
        }}
        .decision-ticket__label {{
            background: {HEADER_BG};
            color: #fff;
            font-size: 0.65rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            padding: 4px 10px;
            border-radius: 4px;
        }}
        .decision-ticket__block {{
            color: #9fb0c8;
            font-size: 0.75rem;
            font-family: monospace;
        }}
        .decision-ticket__confidence {{
            margin-left: auto;
            color: {MUTED};
            font-size: 0.7rem;
        }}
        .decision-ticket__actions {{ display: flex; flex-direction: column; gap: 8px; }}
        .decision-ticket__action {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 12px;
            border-radius: 6px;
            background: {PANEL};
            font-size: 0.85rem;
        }}
        .decision-ticket__action--hold {{
            border-left: 4px solid {SIGNAL_AMBER};
        }}
        .decision-ticket__action--allow {{
            border-left: 4px solid {SIGNAL_GREEN};
        }}
        .decision-ticket__action-label {{
            font-weight: 700;
            text-transform: uppercase;
            font-size: 0.7rem;
            letter-spacing: 0.05em;
            min-width: 55px;
        }}
        .decision-ticket__action-label--hold {{ color: {SIGNAL_AMBER}; }}
        .decision-ticket__action-label--allow {{ color: {SIGNAL_GREEN}; }}
        .decision-ticket__action-detail {{ color: {TEXT}; }}
        .decision-ticket__reason {{
            margin-top: 10px;
.decision-ticket__action-label--hold {{ color: {SIGNAL_AMBER}; }}
        .decision-ticket__action-label--allow {{ color: {SIGNAL_GREEN}; }}
        .decision-ticket__action-detail {{ color: {TEXT}; }}
        .decision-ticket__reason {{
            margin-top: 10px;
            padding: 10px 12px;
            background: {PANEL};
            border-radius: 6px;
            font-size: 0.8rem;
            color: {TEXT};
        }}
        .decision-ticket__reason-label {{
            color: {MUTED};
            font-size: 0.65rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 4px;
        }}
        .stButton > button {{
            height: 40px !important;
            font-weight: 600 !important;
            font-size: 0.8rem !important;
            border-radius: 6px !important;
            border: 1px solid {CARD_BORDER} !important;
            background: {CARD_BG} !important;
            color: {TEXT} !important;
            transition: all 0.15s ease;
        }}
        .stButton > button:hover {{
            background: {PANEL} !important;
            border-color: {HEADER_RED} !important;
        }}
        .stButton > button:focus {{
            outline: 2px solid {HEADER_RED} !important;
            outline-offset: 2px;
        }}
        .stButton > button[kind="primary"] {{
            background: {HEADER_RED} !important;
            border-color: {HEADER_RED} !important;
            color: #fff !important;
        }}
        button[data-testid="baseButton-accept"] {{
            background: {SIGNAL_GREEN} !important;
            border-color: {SIGNAL_GREEN} !important;
            color: #fff !important;
        }}
        button[data-testid="baseButton-reject"] {{
            background: {SIGNAL_RED} !important;
            border-color: {SIGNAL_RED} !important;
            color: #fff !important;
        }}
        .stTabs [data-baseweb="tab-list"] {{
            gap: 4px;
            background-color: transparent;
            padding: 0;
            border: none;
        }}
        .stTabs [data-baseweb="tab"] {{
            height: 38px;
            background-color: {PANEL};
            border: 1px solid {CARD_BORDER};
            border-radius: 6px 6px 0 0;
            color: {TEXT};
            font-weight: 600;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            padding: 0 18px;
            margin-right: 2px;
            border-bottom: none;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {CARD_BG} !important;
            color: {HEADER_RED} !important;
            border-color: {CARD_BORDER};
            border-bottom: 2px solid {CARD_BG};
            z-index: 1;
        }}
        .stDataFrame {{ border: 1px solid {CARD_BORDER}; border-radius: 8px; overflow: hidden; }}
        .stDataFrame [data-testid="stTable"] {{ background: {CARD_BG}; }}
        .stSelectbox > div > div {{ background: {CARD_BG}; border-color: {CARD_BORDER}; }}
        .stSlider [data-baseweb="slider"] {{ color: {HEADER_RED}; }}
        .small {{ color: {MUTED}; font-size: 0.8rem; }}
        .ir-red {{ color: {HEADER_RED}; font-weight: 700; }}
        .signal-green {{ color: {SIGNAL_GREEN}; }}
        .signal-amber {{ color: {SIGNAL_AMBER}; }}
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}
        header[data-testid="stHeader"] {{ background: transparent; }}
        .block-container {{ padding-top: 1rem; padding-bottom: 1rem; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, good: bool | None = None, hint: str = "") -> str:
    cls = ""
    if good is True:
        cls = "kpi-value--good"
    elif good is False:
        cls = "kpi-value--bad"
    hint_html = f'<div class="kpi-hint">{hint}</div>' if hint else ""
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value {cls}">{value}</div>'
        f'{hint_html}'
        f'</div>'
    )
def draw_map(sim) -> go.Figure:
    net = sim.net
    fig = go.Figure()

    finished_trains = [t for t in sim.trains if t.finished]
    finished_at_station = {}
    for t in finished_trains:
        if t.at_station:
            finished_at_station.setdefault(t.at_station, []).append(t)

    for blk in net.blocks:
        x1, y1, x2, y2 = net.block_xy(blk)
        occupied = bool(blk.occupant_up or blk.occupant_down)

        if blk.double_line:
            fig.add_trace(go.Scatter(
                x=[x1, x2], y=[y1 + 0.35, y2 + 0.35],
                mode="lines", line=dict(width=5, color=RAIL_GREY_DARK),
                hoverinfo="none", showlegend=False,
            ))
            fig.add_trace(go.Scatter(
                x=[x1, x2], y=[y1 - 0.35, y2 - 0.35],
                mode="lines", line=dict(width=5, color=RAIL_GREY_DARK),
                hoverinfo="none", showlegend=False,
            ))
            fig.add_trace(go.Scatter(
                x=[x1, x2], y=[y1, y2],
                mode="lines", line=dict(width=1, color=RAIL_GREY, dash="dot"),
                hoverinfo="none", showlegend=False,
            ))
        else:
            dash = "dash" if not occupied else "solid"
            width = 3 if not occupied else 4
            color = RAIL_GREY if not occupied else SIGNAL_AMBER
            fig.add_trace(go.Scatter(
                x=[x1, x2], y=[y1, y2],
                mode="lines", line=dict(width=width, color=color, dash=dash),
                hoverinfo="text",
                hovertext=f"{blk.id} · Single-line · {blk.length_km} km · {'Occupied' if occupied else 'Clear'}",
                showlegend=False,
            ))

        if not blk.double_line and blk.id in getattr(sim, "predicted_conflicts", set()):
            fig.add_trace(go.Scatter(
                x=[x1, x2], y=[y1, y2],
                mode="lines", line=dict(width=8, color=SIGNAL_RED, dash="solid"),
                opacity=0.18, hoverinfo="none", showlegend=False,
            ))

    station_offsets = {}
    block_offsets = {}
    active_at_station = {}

    for stn in net.stations.values():
        x, y = stn.x, stn.y
        loop_count = stn.loops
        
        box_w = 1.6 + loop_count * 0.35
        box_h = 0.9
        
        fig.add_trace(go.Scatter(
            x=[x - box_w/2, x + box_w/2, x + box_w/2, x - box_w/2, x - box_w/2],
            y=[y - box_h/2, y - box_h/2, y + box_h/2, y + box_h/2, y - box_h/2],
            mode="lines", fill="toself",
            fillcolor=CARD_BG,
            line=dict(width=1.5, color=RAIL_GREY),
            hoverinfo="text",
            hovertext=f"{stn.id} · {stn.name} · {loop_count} loops",
            showlegend=False,
        ))
        
        fig.add_trace(go.Scatter(
            x=[x], y=[y + box_h/2 + 0.35],
            mode="text",
            text=[stn.id],
            textfont=dict(size=11, color=HEADER_RED, family="monospace", weight=700),
            hoverinfo="none", showlegend=False,
        ))
        
        fig.add_trace(go.Scatter(
            x=[x], y=[y + box_h/2 + 0.15],
            mode="text",
            text=[stn.name],
            textfont=dict(size=9, color=TEXT, weight=500),
            hoverinfo="none", showlegend=False,
        ))
        
        if loop_count > 1:
            fig.add_trace(go.Scatter(
                x=[x + box_w/2 - 0.2], y=[y - box_h/2 - 0.25],
                mode="text",
                text=[f"L{loop_count}"],
                textfont=dict(size=8, color=MUTED, weight=600),
                hoverinfo="none", showlegend=False,
            ))

        if stn.id in finished_at_station:
            for i, t in enumerate(finished_at_station[stn.id]):
                fig.add_trace(go.Scatter(
                    x=[x + (i - len(finished_at_station[stn.id])/2 + 0.5) * 0.4],
                    y=[y + box_h/2 + 0.6],
                    mode="markers",
                    marker=dict(size=6, color=PRIORITY_COLOR[t.priority], opacity=0.3, symbol="circle"),
                    hoverinfo="text",
                    hovertext=f"FINISHED · {t.number} {t.name}",
                    showlegend=False,
                ))

        for t in sim.trains:
            if t.at_station == stn.id and t.entered_section and not t.finished:
                active_at_station.setdefault(stn.id, []).append(t)

        trains_here = active_at_station.get(stn.id, [])
        for i, t in enumerate(trains_here):
            station_offsets[(stn.id, t.id)] = (i - (len(trains_here) - 1) / 2) * 0.5

    for blk in net.blocks:
        trains_on_blk = [t for t in sim.trains if t.on_block == blk.id and t.entered_section and not t.finished]
        for i, t in enumerate(trains_on_blk):
            block_offsets[(blk.id, t.id)] = (i - (len(trains_on_blk) - 1) / 2) * 0.4

    active_positions = []
    
    for t in sim.trains:
        if not t.entered_section or t.finished:
            continue
        base_x, base_y = sim.train_position(t)
        
        y_offset = 2.5 if t.direction == "up" else -2.5
        
        x_offset = 0.0
        if t.at_station:
            x_offset = station_offsets.get((t.at_station, t.id), 0.0)
        
        block_nudge = 0.0
        if t.on_block:
            block_nudge = block_offsets.get((t.on_block, t.id), 0.0)
            y_offset += block_nudge * (1 if t.direction == "up" else -1)
        
        x = base_x + x_offset
        y = base_y + y_offset
        
        active_positions.append((round(x, 1), round(y, 1)))
        
        fig.add_trace(go.Scatter(
            x=[x], y=[y], mode="markers+text",
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

    active_count = len(active_positions)
    finished_count = len(finished_trains)
    
    distinct_positions = len(set(active_positions))
    
    stacked_parts = []
    for station_id, trains in active_at_station.items():
        if len(trains) >= 2:
            stacked_parts.append(f"{len(trains)} at {station_id}")
    
    stacked_str = "Stacked: " + ", ".join(stacked_parts) if stacked_parts else "Stacked: No stacks"
    
    status_line = f"Active {active_count} · Finished {finished_count} · Distinct positions {distinct_positions} · {stacked_str}"
    
    title_text = (
        f"NZM–AGC Section · T+{sim.time} min · {sim.mode.upper()} mode<br>"
        f"<span style='font-size:11px;color:{MUTED};'>{status_line}</span>"
    )

    fig.update_layout(
        paper_bgcolor=PLOT_BG, plot_bgcolor=PLOT_BG, font=dict(color=TEXT),
        margin=dict(l=10, r=10, t=55, b=10), height=480,
        xaxis=dict(visible=False, showgrid=False, zeroline=False),
        yaxis=dict(visible=False, showgrid=False, zeroline=False, scaleanchor="x", scaleratio=1),
        title=dict(text=title_text, font=dict(size=14)),
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


def decision_ticket_html(rec: dict, sim) -> str:
    """Render AI advice as a decision ticket."""
    if not rec:
        return ""
    
    hold_trains = rec.get("hold", [])
    allow_trains = rec.get("allow", [])
    block_id = rec.get("block", "—")
    confidence = rec.get("confidence", 0)
    reason = rec.get("reason", "No reason provided.")
    impact = rec.get("impact", "No impact estimate.")
    
    hold_html = ""
    for tid in hold_trains:
        tr = sim._train(tid)
        name = f"{tr.number} {tr.name}" if tr else tid
        hold_html += (
            f'<div class="decision-ticket__action decision-ticket__action--hold">'
            f'<span class="decision-ticket__action-label decision-ticket__action-label--hold">HOLD</span>'
            f'<span class="decision-ticket__action-detail">{name} at {tr.at_station if tr else "station"}</span>'
            f'</div>'
        )
    
    allow_html = ""
    for tid in allow_trains:
        tr = sim._train(tid)
        name = f"{tr.number} {tr.name}" if tr else tid
        allow_html += (
            f'<div class="decision-ticket__action decision-ticket__action--allow">'
            f'<span class="decision-ticket__action-label decision-ticket__action-label--allow">ALLOW</span>'
            f'<span class="decision-ticket__action-detail">{name} into block {block_id}</span>'
            f'</div>'
        )
    
    return (
        f'<div class="decision-ticket">'
        f'<div class="decision-ticket__header">'
        f'<span class="decision-ticket__label">DECISION</span>'
        f'<span class="decision-ticket__block">BLOCK {block_id}</span>'
        f'<span class="decision-ticket__confidence">Confidence: {confidence:.0f}%</span>'
        f'</div>'
        f'<div class="decision-ticket__actions">'
        f'{hold_html}'
        f'{allow_html}'
        f'</div>'
        f'<div class="decision-ticket__reason">'
        f'<div class="decision-ticket__reason-label">Why</div>'
        f'{reason}'
        f'</div>'
        f'<div class="decision-ticket__reason">'
        f'<div class="decision-ticket__reason-label">Expected effect</div>'
        f'{impact}'
        f'</div>'
        f'</div>'
    )


def safety_lamp_html(violations: int) -> str:
    """Render safety lamp indicator."""
    if violations == 0:
        return (
            f'<span style="display:inline-flex;align-items:center;gap:6px;">'
            f'<span class="control-header__lamp"></span>'
            f'<span style="color:#fff;font-weight:600;">CLEAR</span>'
            f'</span>'
        )
    else:
        return (
            f'<span style="display:inline-flex;align-items:center;gap:6px;">'
            f'<span class="control-header__lamp control-header__lamp--violation"></span>'
            f'<span style="color:#fff;font-weight:600;">{violations} VIOLATION{"S" if violations > 1 else ""}</span>'
            f'</span>'
        )