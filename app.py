"""RailMind — AI-powered precise train traffic control.

Run with:  streamlit run app.py
"""
from __future__ import annotations

import io
import time
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from engine.model import load_scenarios
from engine.simulation import Simulation, compare
from ui.theme import (BG, GREEN, TEXT, draw_map, inject_css,
                      kpi_card, legend_html)

st.set_page_config(page_title="RailMind Control", page_icon="🚆", layout="wide")
inject_css(st)

SCENARIOS = load_scenarios()["scenarios"]


# ----------------------------- session -----------------------------
def init_state() -> None:
    if "sim" not in st.session_state:
        st.session_state.sim = Simulation.new("normal", mode="ai")
    if "playing" not in st.session_state:
        st.session_state.playing = False
    if "speed" not in st.session_state:
        st.session_state.speed = 1   # seconds per step
    if "baseline" not in st.session_state:
        st.session_state.baseline = None
    if "ai_compare" not in st.session_state:
        st.session_state.ai_compare = None
    if "ops_note" not in st.session_state:
        st.session_state.ops_note = "Monitor heavy-occupancy trains for single-line conflict windows."


def build_team_brief(sim: Simulation) -> dict:
    brief = sim.team_brief()
    rec = sim.current_recommendation()
    brief["infractions"] = sim.kpis()["safety_violations"]
    brief["recommendation"] = rec
    return brief


init_state()
sim: Simulation = st.session_state.sim

# Process external events posted to data/external_events.jsonl (from ingest gateway)
def process_external_events(sim: Simulation) -> None:
    """Read external_events.jsonl, convert common event types into sim.pending_events entries,
    and clear the queue file. This allows a simple REST gateway to push events for demos/pilots.
    """
    qf = Path(__file__).resolve().parent / 'data' / 'external_events.jsonl'
    if not qf.exists():
        return
    try:
        with open(qf, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f if l.strip()]
    except Exception:
        return
    if not lines:
        return
    for line in lines:
        try:
            ev = json.loads(line)
        except Exception:
            continue
        et = ev.get('event_type')
        # Map canonical events to simulation pending events where possible
        if et == 'departure_delay' or (et == 'train_delay'):
            # {"event_type":"departure_delay","train_id":"T1","minutes":20}
            t = ev.get('train_id') or ev.get('train')
            mins = ev.get('minutes') or ev.get('minutes_min') or 0
            sim.pending_events.append({'at_min': sim.time, 'action': 'departure_delay', 'train': t, 'minutes': mins})
        elif et == 'speed_restriction':
            blk = ev.get('block_id') or ev.get('block')
            sp = ev.get('speed') or ev.get('speed_kmh')
            dur = ev.get('duration_min') or ev.get('duration') or 0
            sim.pending_events.append({'at_min': sim.time, 'action': 'speed_restriction', 'block': blk, 'speed': sp, 'duration_min': dur})
        elif et == 'network_speed':
            sp = ev.get('speed') or ev.get('speed_kmh')
            dur = ev.get('duration_min') or ev.get('duration') or 0
            sim.pending_events.append({'at_min': sim.time, 'action': 'network_speed', 'speed': sp, 'duration_min': dur})
        elif et == 'train_hold':
            t = ev.get('train_id') or ev.get('train')
            mins = ev.get('minutes') or 0
            at_station = ev.get('at_station') or ev.get('station')
            sim.pending_events.append({'at_min': sim.time, 'action': 'train_hold', 'train': t, 'minutes': mins, 'at_station': at_station})
        # Add other mappings as needed for your sources
    # Clear queue file after processing
    try:
        qf.unlink()
    except Exception:
        # best-effort
        open(qf, 'w', encoding='utf-8').close()

# run processing at load time so any posted events are picked up immediately
process_external_events(sim)


# ----------------------------- sidebar -----------------------------
with st.sidebar:
    st.markdown("## 🚆 RailMind Control")
    st.caption("AI section controller — decision support, not autopilot.")

    scen_choice = st.selectbox(
        "Scenario",
        options=[s["id"] for s in SCENARIOS],
        format_func=lambda x: next(s["name"] for s in SCENARIOS if s["id"] == x),
        index=[s["id"] for s in SCENARIOS].index(st.session_state.sim.scenario_id),
    )
    mode = st.radio("Controller mode", ["ai", "fcfs"],
                    format_func=lambda m: "AI Assist" if m == "ai" else "Manual (FCFS)",
                    horizontal=True,
                    index=0 if st.session_state.sim.mode == "ai" else 1)

    if st.button("↻ Reset / Load scenario", width='stretch'):
        st.session_state.sim = Simulation.new(scen_choice, mode=mode)
        st.session_state.playing = False
        fcfs, ai = compare(scen_choice, minutes=120)
        st.session_state.baseline = fcfs.kpis()
        st.session_state.ai_compare = ai.kpis()
        st.rerun()

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶ Play" if not st.session_state.playing else "⏸ Pause",
                     width='stretch'):
            st.session_state.playing = not st.session_state.playing
            st.rerun()
    with col2:
        if st.button("⏭ Step", width='stretch'):
            st.session_state.sim.step()
            st.rerun()

    st.session_state.speed = st.select_slider(
        "Speed (sec/step)", options=[0.2, 0.5, 1.0, 1.5, 2.0], value=st.session_state.speed
    )

    st.divider()
    st.markdown("### Inject disruption")
    inj = st.selectbox("Choose", [
        "None",
        "Delay Rajdhani 20m",
        "Signal fail at KSV",
        "Fog (60 km/h) for 60m",
    ])
    if st.button("Apply", width='stretch') and inj != "None":
        sim = st.session_state.sim
        if inj.startswith("Delay"):
            t = next(x for x in sim.trains if x.number == "12956")
            t.delay_min += 20
            t.planned_dep += 20
            t.extra_hold += 0
        elif inj.startswith("Signal"):
            sim.speed_restrictions["B4"] = 40
        elif inj.startswith("Fog"):
            sim.network_speed = 60
            sim.network_speed_until = sim.time + 60
        st.rerun()

    st.divider()
    brief = build_team_brief(st.session_state.sim)
    st.markdown(f"**Ops risk:** {brief['risk_level']}")
    st.caption(brief['summary'])
    st.caption(f"Recommended release: {brief['recommended_release']}")
    st.caption("SIH 2025 · Problem 25022")


# auto-play loop (runs one step per rerun)
if st.session_state.playing and sim.time < 180:
    time.sleep(st.session_state.speed)
    sim.step()
    st.rerun()


# ----------------------------- main tabs -----------------------------
tab_map, tab_advice, tab_whatif, tab_kpi, tab_team, tab_log = st.tabs(
    ["🗺 Live Map", "🤖 AI Advice", "🔀 What-If", "📊 KPIs", "🧭 Team Ops", "📋 Log & Scenarios"]
)

# ---------- TAB 1: MAP ----------
with tab_map:
    k = sim.kpis()
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(kpi_card("Time", f"T+{sim.time}m"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("Throughput", f"{k['throughput']} trains"), unsafe_allow_html=True)
    with c3:
        st.markdown(
            kpi_card("Avg delay", f"{k['avg_delay']}m", good=None if k['avg_delay'] <= 5 else False),
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            kpi_card("Punctuality", f"{k['punctuality']:.0f}%", good=k['punctuality'] >= 80),
            unsafe_allow_html=True,
        )
    with c5:
        good = k['safety_violations'] == 0
        st.markdown(
            kpi_card("Safety", f"{k['safety_violations']} violations", good=good),
            unsafe_allow_html=True,
        )

    st.markdown(legend_html(), unsafe_allow_html=True)
    st.plotly_chart(draw_map(sim), width='stretch', config={"displayModeBar": False})

    confs = sim.upcoming_conflicts(horizon=30)
    if confs:
        st.warning(
            "⚠ Predicted conflict(s): " +
            ", ".join(f"{c['block']} in {c['in_min']}m" for c in confs[:3])
        )
    else:
        st.success("✓ No conflicts predicted in the next 30 minutes.")

# ---------- TAB 2: ADVICE ----------
with tab_advice:
    st.subheader("AI Recommendations")
    rec = sim.current_recommendation()
    if rec is None:
        st.info("No active conflict requiring a decision. The AI is watching the section.")
    else:
        st.markdown(
            f"""<div class="rec-card">
            <div class="small">RECOMMENDATION · BLOCK {rec['block']}</div>
            <h3 style='margin:6px 0;'>🟢 {rec['action']}</h3>
            <p><b>Why:</b> {rec['reason']}</p>
            <p class="small"><b>Expected impact:</b> {rec['impact']}</p>
            </div>""",
            unsafe_allow_html=True,
        )
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✅ Accept AI advice", width='stretch'):
                for hid in rec["hold"]:
                    t = sim._train(hid)
                    if t:
                        t.extra_hold += 2
                st.success("Applied. The held trains will wait 2 more minutes.")
        with col_b:
            if st.button("✖ Reject (use my judgement)", width='stretch'):
                st.info("Logged as controller override.")
    st.divider()
    st.caption("💡 (Stretch) LLM copilot: ask 'what if I route 12956 via KSV loop?' — "
               "connect a Groq/Gemini key to enable natural-language what-if.")

# ---------- TAB 3: WHAT-IF ----------
with tab_whatif:
    st.subheader("🔀 What-If Scenario Sandbox")
    st.caption(
        "Test alternate dispatch decisions in real-time. Override the AI or "
        "adjust train holds to inspect downstream impact."
    )

    colA, colB = st.columns(2)
    with colA:
        active_trains = [t.number for t in sim.trains if t.entered_section and not t.finished]
        if not active_trains:
            st.info("No active trains currently on section.")
        else:
            def _format_train(n):
                return f"{n} - {next(t.name for t in sim.trains if t.number == n)}"

            choice = st.selectbox(
                "Select Active Train",
                options=active_trains,
                format_func=_format_train,
            )
            mins = st.slider("Hold Duration (minutes)", 1, 15, 3)
            if st.button("Apply Custom Hold Override", width='stretch'):
                t = sim._train(choice)
                if t:
                    t.extra_hold += mins
                    st.warning(f"⚠️ Train {t.number} ({t.name}) held for {mins} extra minutes.")
                    rec = sim.current_recommendation()
                    if rec:
                        st.info(f"💡 AI Counter-Advice: {rec['action']} — {rec['impact']}")

    with colB:
        st.markdown("#### Scenario Impact Estimator")
        st.write("Simulate how holding high-priority trains affects network throughput and cumulative delay.")
        if st.session_state.baseline:
            b = st.session_state.baseline
            a = st.session_state.ai_compare
            st.metric("Estimated Delay Delta", f"{a['avg_delay'] - b['avg_delay']:.1f} min", delta_color="inverse")
            st.metric("Passenger Punctuality Delta", f"{a['punctuality'] - b['punctuality']:.1f}%")
        else:
            st.info("Run baseline comparison by clicking **Reset / Load scenario** in the sidebar.")

# ---------- TAB 4: KPIs ----------
with tab_kpi:
    st.subheader("AI vs Manual (FCFS) — 120-min scenario")
    if st.session_state.baseline is None:
        st.caption("Press **↻ Reset / Load scenario** in the sidebar to run the comparison.")
    else:
        b = st.session_state.baseline
        a = st.session_state.ai_compare
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Throughput", f"{a['throughput']}",
                  delta=f"{a['throughput']-b['throughput']} vs manual")
        m2.metric("Avg delay (min)", f"{a['avg_delay']}",
                  delta=f"{a['avg_delay']-b['avg_delay']:.1f} vs manual", delta_color="inverse")
        m3.metric("Punctuality", f"{a['punctuality']:.0f}%",
                  delta=f"{a['punctuality']-b['punctuality']:.1f} pts")
        m4.metric("Passenger-min saved",
                  f"{int(b['pax_minutes']-a['pax_minutes']):,}",
                  delta="vs manual")

        cats = ["Throughput", "Avg delay", "Punctuality"]
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                name="Manual (FCFS)",
                x=cats,
                y=[b["throughput"], b["avg_delay"], b["punctuality"]],
                marker_color="#6b7280",
            )
        )
        fig.add_trace(
            go.Bar(
                name="AI Assist",
                x=cats,
                y=[a["throughput"], a["avg_delay"], a["punctuality"]],
                marker_color=GREEN,
            )
        )
        fig.update_layout(
            barmode="group",
            paper_bgcolor=BG,
            plot_bgcolor=BG,
            font=dict(color=TEXT),
            height=380,
        )
        st.plotly_chart(fig, width='stretch')

        st.markdown("### Why the AI wins")
        st.write(
            "FCFS releases trains in arrival order, which lets slow freights and "
            "late-running low-priority trains block high-priority, high-occupancy "
            "trains. The AI scores every candidate by `priority × 20 + pax/10 + "
            "delay × 5`, so a Rajdhani carrying 1,180 passengers is cleared before "
            "a freight carrying none."
        )

# ---------- TAB 5: TEAM OPS ----------
with tab_team:
    st.subheader("Control-room briefing")
    brief = build_team_brief(sim)
    k = sim.kpis()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Risk level", brief["risk_level"])
    with c2:
        st.metric("Active trains", k["active_trains"])
    with c3:
        st.metric("Safety infractions", k["safety_violations"])

    st.info(brief["summary"])

    if brief["recommendation"]:
        rec = brief["recommendation"]
        st.markdown(
            f"""<div class="rec-card">
            <div class="small">TEAM DECISION BRIEF</div>
            <h3 style='margin:6px 0;'>🚦 {rec['action']}</h3>
            <p><b>Why it matters:</b> {rec['reason']}</p>
            <p class="small"><b>Expected effect:</b> {rec['impact']}</p>
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.success("No immediate dispatch intervention required; the section is stable.")

    with st.expander("Controller notes", expanded=True):
        note = st.text_area("Add a team note for shift handover", value=st.session_state.ops_note, key="ops_note_text")
        if st.button("Save note"):
            st.session_state.ops_note = note
            st.success("Controller note saved for this session.")

    export_rows = [{
        "Time": f"T+{e.time}m",
        "Type": e.kind,
        "Train": e.train or "",
        "Block": e.block or "",
        "Detail": e.detail,
    } for e in sim.events[-100:]]
    csv_buffer = io.StringIO()
    pd.DataFrame(export_rows).to_csv(csv_buffer, index=False)
    st.download_button(
        "Download ops report (CSV)",
        data=csv_buffer.getvalue().encode("utf-8"),
        file_name="railmind_ops_report.csv",
        mime="text/csv",
        width='stretch',
    )

# ---------- TAB 6: LOG ----------
with tab_log:
    st.subheader("Scenario description")
    scen = next(s for s in SCENARIOS if s["id"] == sim.scenario_id)
    st.write(f"**{scen['name']}** — {scen['description']}")

    st.subheader("Event log")
    rows = [
        {"Time": f"T+{e.time}m", "Type": e.kind, "Train": e.train or "",
         "Block": e.block or "", "Detail": e.detail}
        for e in reversed(sim.events[-200:])
    ]
    if rows:
        st.dataframe(pd.DataFrame(rows), width='stretch', height=380)
    else:
        st.caption("No events yet.")

    st.subheader("Train status")
    trows = []
    for t in sim.trains:
        trows.append({
            "No.": t.number, "Name": t.name, "Type": t.type,
            "Prio": t.priority, "Pax": t.pax,
            "State": ("Finished" if t.finished else
                      ("At " + t.at_station if t.at_station else "On " + (t.on_block or ""))),
            "Delay (m)": max(0, sim.time - t.planned_dep),
        })
    st.dataframe(pd.DataFrame(trows), width='stretch')
