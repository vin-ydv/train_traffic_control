# RailMind Architecture & Technical Design Document

## 1. Executive Summary
**RailMind** is an AI-powered decision support system designed for railway section controllers, addressing **Smart India Hackathon (SIH) Problem Statement 25022**: *Maximizing Section Throughput Using AI-Powered Precise Train Traffic Control*.

In high-density mixed-traffic railway networks (single-line and multi-line sections carrying high-speed Vande Bharat, Rajdhani, passenger, and freight trains), human dispatchers often face cognitive overload during disruptions. RailMind acts as an intelligent co-pilot that simulates network state, predicts block conflicts, recommends optimal hold/release actions with explainable plain-English reasoning, and guarantees absolute safety.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       Streamlit UI                          │
│  (Live Map, AI Advice, What-If, KPIs, Team Ops, Event Log)  │
└──────────────┬──────────────────────────────┬───────────────┘
               │ User Actions / Toggles       │ Real-time State & KPIs
               ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Simulation Engine                      │
│  - Time-step advancement (1-minute intervals)               │
│  - Movement Authority & Block Interlocking (Safety Shield)  │
│  - Conflict Resolution (FCFS vs. AI Optimization)           │
└──────────────┬──────────────────────────────┬───────────────┘
               │ Data Models                  │ Ingest Service
               ▼                              ▼
┌──────────────────────────────┐    ┌─────────────────────────┐
│     engine/model.py          │    │     data/               │
│  - Train, Station, Block,    │    │  - section.json         │
│    Section Data Classes      │    │  - timetable.json       │
│                              │    │  - scenarios.json       │
└──────────────────────────────┘    └─────────────────────────┘
```

---

## 3. Core Component Breakdown

### A. Data Layer (`data/`)
- **`section.json`**: Defines network topology including stations, track blocks, loop lengths, and single/double-line attributes.
- **`timetable.json`**: Specifies train consists, priorities (1 = Highest, e.g. Rajdhani; 4 = Lowest, e.g. Freight), passenger load, maximum speeds, and scheduled departure/arrival times.
- **`scenarios.json`**: Configures operational scenarios such as normal operations, rolling stock delays, signal failures, heavy fog, and freight breakdowns.

### B. Engine Layer (`engine/`)
- **`model.py`**: Immutable dataclasses and network representations for trains, blocks, stations, and section layouts.
- **`simulation.py`**:
  - **Deterministic Time-Step Model**: Advances simulation time by 1-minute increments, updating train positions, speeds, signal states, and station queues.
  - **Safety Shield (Interlocking)**: Enforces absolute block signaling. No two trains can occupy the same single-line block simultaneously. Opposite directions on single lines require strict station loop meets/passes.
  - **AI Heuristic (Passenger-Weighted Delay Optimization)**:
    $$\text{Score} = (\text{Priority} \times 20) + \left(\frac{\text{Passenger Count}}{10}\right) + (\text{Current Delay} \times 5)$$
    Trains with higher scores are prioritized for block clearance. This minimizes total passenger-weighted delay rather than just crude train count.

### C. Presentation Layer (`ui/` & `app.py`)
- **`theme.py`**: Custom CSS styling and Plotly map integration for real-time spatial visualization of train positions and conflict zones.
- **`app.py`**: Interactive 6-tab Streamlit dashboard providing live control, AI advisory cards, what-if counterfactual scenario analysis, KPI tracking, team operational logs, and exportable audit trails.

---

## 4. Key Innovation & Differentiators

1. **Human-in-the-Loop (Co-pilot Architecture)**: RailMind does not override controller authority. It provides explainable recommendations ("Hold Train 12951 at Station B for 4 mins to allow Express 22436 to cross") with Accept/Reject actions.
2. **Passenger-Weighted Optimization**: Standard dispatchers prioritize freight or raw train counts; RailMind factors in passenger volume (e.g., 1,200 passengers on a passenger train vs. empty freight) to minimize societal and economic delay impact.
3. **Deterministic & Explainable AI**: Avoids black-box neural networks in favor of rigorous heuristic optimization and constraint satisfaction solvers, ensuring 100% predictability and safety compliance.
4. **Instant Containerized Deployment**: Fully Dockerized for seamless deployment across control-room servers or cloud infrastructure.
