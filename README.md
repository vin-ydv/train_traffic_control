# RailMind 🚆

**SIH 2025 — Problem Statement 25022: Maximizing Section Throughput Using AI-Powered Precise Train Traffic Control**

A decision-support dashboard for railway section controllers. RailMind simulates a
rail section, predicts train conflicts on single-line blocks, recommends the best
hold/release decision (with a plain-English reason), and shows the measurable
improvement vs. manual (first-come-first-served) dispatching.

> The human stays in charge. RailMind is a co-pilot, not an autopilot.

## Quick start

```bash
# 1. (recommended) create a virtual env
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 2. install deps
pip install -r requirements.txt

# 3. run the app
streamlit run app.py
```

Open the URL it prints (usually http://localhost:8501).

## Run the tests

```bash
pip install pytest
pytest -q
```

The tests assert **zero safety violations** across every scenario and that AI mode
does no worse than FCFS on the delay scenario.

## What's in the box

```
RailMind/
├── app.py                 # Streamlit dashboard (entry point)
├── data/
│   ├── section.json       # stations, blocks, loops, single/double line
│   ├── timetable.json     # trains, priorities, pax, speeds, schedules
│   └── scenarios.json     # normal day, delays, signal fail, fog, breakdown
├── engine/
│   ├── model.py           # Station / Block / Train / Network data classes
│   └── simulation.py      # time-step engine, FCFS + AI controller, KPIs, conflicts
├── ui/
│   └── theme.py           # dark theme + Plotly map drawing
└── tests/
    └── test_core.py       # safety + AI-beats-FCFS tests
```

## The 6 screens
1. **Live map** — trains moving block-by-block; conflict glow; PLAY/PAUSE/STEP.
2. **AI Advice** — recommendation card with reason + Accept/Reject.
3. **What-If** — manually hold a train; see cost vs AI suggestion.
4. **KPIs** — AI vs Manual comparison (throughput, delay, punctuality, pax-min).
5. **Team Ops** — control-room risk brief, shift notes, and CSV export of recent dispatch events.
6. **Log** — event timeline + live train status table.

## How the "AI" works (honest version)
- Conflict detection: at each step, trains waiting at a station to enter an occupied
  single-line block form a conflict set.
- Scoring: `priority × 20 + pax/10 + current_delay × 5`. The highest-scoring train
  is released; the others are held. This minimizes **passenger-weighted delay**,
  not just train-delay, which is the project's novelty.
- Safety shield: only one train ever occupies a block, enforced in the engine;
  double-line blocks allow opposite directions.
- Compare against a true FCFS baseline on the identical 120-minute scenario to
  show the improvement.

This is a classical-AI / optimization approach. It is **deterministic and
explainable** — exactly what a railway judge wants to see.

## Roadmap (next 2 weeks)
See `SIH25022_Final_Build_Spec.md` in the parent folder for the day-by-day plan
and the must/should/stretch feature tiers.
