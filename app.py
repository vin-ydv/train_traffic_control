"""RailMind — AI-powered precise train traffic control.

Run with:  streamlit run app.py
"""
from __future__ import annotations
import time
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from engine.model import PRIORITY_LABEL, load_scenarios
from engine.simulation import Simulation, compare
from ui.theme import (AMBER, BG, GREEN, RED, TEXT, draw_map, inject_css,
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


init_state()


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

    if st.button("↻ Reset / Load scenario", use_container_width=True):
        st.session_state.sim = Simulation.new(scen_choice, mode=mode)
        st.session_state.playing = False
        # precompute comparison
        fcfs, ai = compare(scen_choice, minutes=120)
        st.session_state.baseline = fcfs.kpis()
        st.session_state.ai_compare = ai.kpis()
        st.rerun()

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶ Play" if not st.session_state.playing else "⏸ Pause",
                     use_container_width=True):
            st.session_state.playing = not st.session_state.playing
            st.rerun()
    with col2:
        if st.button("⏭ Step", use_container_width=True):
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
    if st.button("Apply", use_container_width=True) and inj != "None":
        sim = st.session_state.sim
        if inj.startswith("Delay"):
            t = next(x for x in sim.trains if x.number == "12956")
            t.delay_min += 20; t.planned_dep += 20; t.extra_hold += 0
        elif inj.startswith("Signal"):
            sim.speed_restrictions["B4"] = 40
        elif inj.startswith("Fog"):
            sim.network_speed = 60; sim.network_speed_until = sim.time + 60
        st.rerun()

    st.divider()
    st.caption("SIH 2025 · Problem 25022")

sim: Simulation = st.session_state.sim

# auto-play loop (runs one step per rerun)
if st.session_state.playing and sim.time < 180:
    time.sleep(st.session_state.speed)
    sim.step()
    st.rerun()


# ----------------------------- main tabs -----------------------------
tab_map, tab_advice, tab_whatif, tab_kpi, tab_log = st.tabs(
    ["🗺 Live Map", "🤖 AI Advice", "🔀 What-If", "📊 KPIs", "📋 Log & Scenarios"]
)

# ---------- TAB 1: MAP ----------
with tab_map:
    k = sim.kpis()
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.markdown(kpi_card("Time", f"T+{sim.time}m"), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("Throughput", f"{k['throughput']} trains"),
                         unsafe_allow_html=True)
    with c3: st.markdown(kpi_card("Avg delay", f"{k['avg_delay']}m",
                                  good=None if k['avg_delay'] <= 5 else False),
                         unsafe_allow_html=True)
    with c4: st.markdown(kpi_card("Punctuality", f"{k['punctuality']:.0f}%",
                                  good=k['punctuality'] >= 80),
                         unsafe_allow_html=True)
    with c5:
        good = k['safety_violations'] == 0
        st.markdown(kpi_card("Safety",
                             f"{k['safety_violations']} violations",
                             good=good), unsafe_allow_html=True)

    st.markdown(legend_html(), unsafe_allow_html=True)
    st.plotly_chart(draw_map(sim), use_container_width=True, config={"displayModeBar": False})

    confs = sim.upcoming_conflicts(horizon=30)
    if confs:
        st.warning(f"⚠ Predicted conflict(s): " +
                   ", ".join(f"{c['block']} in {c['in_min']}m" for c in confs[:3]))
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
            if st.button("✅ Accept AI advice", use_container_width=True):
                for hid in rec["hold"]:
                    t = sim._train(hid)
                    if t: t.extra_hold += 2
                st.success("Applied. The held trains will wait 2 more minutes.")
        with col_b:
            if st.button("✖ Reject (use my judgement)", use_container_width=True):
                st.info("Logged as controller override.")
    st.divider()
    st.caption("💡 (Stretch) LLM copilot: ask 'what if I route 12956 via KSV loop?' — "
               "connect a Groq/Gemini key to enable natural-language what-if.")

# ---------- TAB 3: WHAT-IF ----------
with tab_whatif:
    st.subheader("What-If Simulator")
    st.write("Override a decision and see the cost vs. the AI recommendation.")
    trains_now = [t for t in sim.trains if t.at_station and not t.finished]
    if not trains_now:
        st.info("No trains currently at stations to hold.")
    else:
        choice = st.selectbox(
            "Hold this train at its current station",
            options=[t.id for t in trains_now],
            format_func=lambda x: f"{sim._train(x).number} {sim._train(x).name}"
                                  f" at {sim._train(x).at_station}",
        )
        mins = st.slider("Hold (minutes)", 1, 10, 3)
        if st.button("Apply my decision", use_container_width=True):
            t = sim._train(choice)
            t.extra_hold += mins
            st.warning(f"{t.number} held for {mins} extra min at {t.at_station}.")
            rec = sim.current_recommendation()
            if rec:
                st.info(f"AI suggests instead: {rec['action']} — {rec['impact']}")

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

        # chart
        cats = ["Throughput", "Avg delay", "Punctuality"]
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Manual (FCFS)", x=cats,
                             y=[b["throughput"], b["avg_delay"], b["punctuality"]],
                             marker_color="#6b7280"))
        fig.add_trace(go.Bar(name="AI Assist", x=cats,
                             y=[a["throughput"], a["avg_delay"], a["punctuality"]],
                             marker_color=GREEN))
        fig.update_layout(barmode="group", paper_bgcolor=BG, plot_bgcolor=BG,
                          font=dict(color=TEXT), height=380)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Why the AI wins")
        st.write(
            "FCFS releases trains in arrival order, which lets slow freights and "
            "late-running low-priority trains block high-priority, high-occupancy "
            "trains. The AI scores every candidate by `priority × 20 + pax/10 + "
            "delay × 5`, so a Rajdhani carrying 1,180 passengers is cleared before "
            "a freight carrying none."
        )

# ---------- TAB 5: LOG ----------
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
        st.dataframe(pd.DataFrame(rows), use_container_width=True, height=380)
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
    st.dataframe(pd.DataFrame(trows), use_container_width=True)
