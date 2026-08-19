# RailMind — Exact Setup & Build Guide (Start Here)

You have **Gemini Pro**. We will use **Gemini CLI** as your coding agent (it edits
files, runs commands, sees errors — no copy-pasting). This guide assumes you're on
**Windows**. Mac/Linux commands differ only where noted.

---

## PART 1 — Install everything (one time, ~30 min)

### Step 1: Install core tools
Download and install each with default options:

1. **Python 3.11 or 3.12** (NOT 3.13 — some libraries lag)
   - https://www.python.org/downloads/
   - ✅ Tick **"Add Python to PATH"** on the first installer screen.
2. **VS Code**
   - https://code.visualstudio.com/
3. **Git for Windows** (includes Git Bash)
   - https://git-scm.com/download/win
4. **Node.js LTS** (needed to install Gemini CLI)
   - https://nodejs.org/ (pick the LTS button)
5. **GitHub Desktop** (optional, makes git visual for beginners)
   - https://desktop.github.com/

**Verify** — open a new terminal (Command Prompt or PowerShell) and run:
```
python --version
git --version
node --version
```
All three should print version numbers. If "python" fails, try `py --version`.

### Step 2: Install Gemini CLI
In the terminal:
```
npm install -g @google/gemini-cli
```
Verify:
```
gemini --version
```

### Step 3: Create a project folder
```
cd Documents
mkdir RailMind
cd RailMind
```

### Step 4: Get the starter code
Option A (easiest): Download the `RailMind` folder from the Arena workspace where
this guide lives — copy all files into `Documents\RailMind`.

Option B (if no download): in VS Code create the file structure shown in Part 3
below; Gemini can also create it from the prompts in Part 4.

### Step 5: Create a Python virtual environment
In `Documents\RailMind`:
```
python -m venv .venv
.venv\Scripts\activate
```
You should see `(.venv)` at the start of your prompt. (Mac/Linux:
`source .venv/bin/activate`.)

### Step 6: Install dependencies
```
pip install -r requirements.txt
pip install pytest
```

### Step 7: Run it
```
streamlit run app.py
```
A browser tab opens at http://localhost:8501 with the dashboard. 🎉

Press `Ctrl+C` in the terminal to stop it.

---

## PART 2 — Start using Gemini CLI (this is how you "code")

### How it works
- Gemini CLI runs **in your project folder**. It can read all files, edit them,
  run commands, see errors, and fix them in a loop.
- You talk to it in plain English. It asks before editing.
- **You are the boss**: read every change before approving. If you don't
  understand something, type: `explain this change like I'm a second-year student`.

### First session
1. Open a terminal in `Documents\RailMind` and activate the venv (Step 5).
2. Run:
   ```
   gemini
   ```
3. A browser opens → log in with the **Google account that has Gemini Pro**.
4. You'll see a prompt. Paste **Prompt 0** below.

### Rules for every session
- Work on **one thing at a time**. Don't ask it to "build everything".
- After it finishes a task, type: `run pytest -q` — tests must pass.
- Then type: `run streamlit run app.py` and click around.
- Then commit in git (see Part 5).
- Keep chats focused. If the conversation gets long/confusing, exit and start a
  fresh `gemini` session in the same folder — it re-reads all files.

---

## PART 3 — Full code structure

```
RailMind/
├── app.py                     # Streamlit dashboard (entry point: streamlit run app.py)
├── requirements.txt           # Python dependencies
├── README.md                  # project overview
├── SETUP.md                   # this file
├── .gitignore                 # files git should ignore
│
├── data/                      # ALL data is JSON — no database
│   ├── section.json           # stations, blocks (length/speed/single/double), loops
│   ├── timetable.json         # trains: number, name, priority, pax, speed, route, dep time
│   └── scenarios.json         # normal, Rajdhani delay, signal fail, fog, breakdown
│
├── engine/                    # the simulation + "AI" (pure Python, no UI)
│   ├── __init__.py
│   ├── model.py               # Station, Block, Train, Network classes + JSON loaders
│   ├── simulation.py          # time-step loop, FCFS + AI controllers, conflict detection,
│   │                          #   recommendation engine, KPI tracker, safety shield
│   ├── conflict.py            # [WEEK 2] look-ahead conflict predictor (if extracted)
│   └── optimizer.py           # [STRETCH] OR-Tools CP-SAT solver (optional upgrade)
│
├── ui/                        # Streamlit screens + theme
│   ├── __init__.py
│   ├── theme.py               # dark control-room colors, KPI cards, Plotly map renderer
│   ├── screen_map.py          # [WEEK 2] Live Map screen (extract from app.py when it grows)
│   ├── screen_advice.py       # [WEEK 2] AI Recommendations screen
│   ├── screen_whatif.py       # [WEEK 2] What-If screen
│   ├── screen_kpi.py          # [WEEK 2] KPI dashboard screen
│   └── screen_audit.py        # [WEEK 2] Event log + train status screen
│
├── tests/                     # run with: pytest -q
│   ├── test_core.py           # zero safety violations in all scenarios
│   ├── test_conflict.py       # known scenario produces a conflict
│   └── test_decision.py       # AI beats FCFS on the delay scenario
│
├── research/                  # [STRETCH] not part of live demo
│   └── rl_compare.py          # RL comparison experiment + chart (offline)
│
└── docs/
    ├── architecture.md        # diagram + module descriptions
    ├── demo_script.md         # exact 3-minute demo words
    └── SIH25022_PPT.pptx      # final presentation
```

### What each file does (plain English)
- **`data/section.json`** = the railway map. Stations have x/y coordinates for
  drawing; blocks connect stations and say if they're single-line (one train at a
  time — where conflicts happen) or double-line.
- **`data/timetable.json`** = the trains. Each has priority (Rajdhani=5 down to
  Freight=1), passenger count, speed, origin/destination, departure time.
- **`data/scenarios.json`** = disruption events (delay a train, fail a signal,
  fog, breakdown) with the time they happen.
- **`engine/model.py`** = data classes: `Station`, `Block`, `Train`, `Network`.
  The Block enforces one-train-per-block (the safety rule).
- **`engine/simulation.py`** = the brain. It advances time 1 minute per step,
  moves trains, detects when two trains want the same single-line block, and the
  controller picks which goes: **FCFS** (first-come-first-served, the "manual"
  baseline) or **AI** (highest priority × pax × delay score). It also computes
  KPIs and builds the recommendation text.
- **`app.py`** = the 5-screen Streamlit dashboard. It calls the engine, draws the
  map with Plotly, shows recommendation cards, KPIs, and the event log.
- **`ui/theme.py`** = dark styling + the `draw_map(sim)` function that renders
  stations, tracks, and moving trains.

### The data flow (understand this!)
```
scenario.json + section.json + timetable.json
            │
            ▼
     Simulation.new()
            │
   ┌────────┴────────┐
   ▼                 ▼
 FCFS run (120m)   AI run (120m)
   │                 │
   └────────┬────────┘
            ▼
      KPI comparison ──► Screen 4
            │
      current state  ──► Screen 1 (map), Screen 2 (advice), Screen 5 (log)
```

---

## PART 4 — Exact prompts for Gemini CLI

Paste these **in order**, one at a time. Wait for each to finish, test, then
continue.

### Prompt 0 — Orientation (first thing)
```
You are helping me build RailMind, an SIH 2025 hackathon project (problem 25022:
AI-powered train traffic control). I am a second-year student with no prior
project experience. The project is a Streamlit dashboard that simulates a railway
section, detects conflicts, recommends which train to hold/release, and compares
AI vs manual dispatching.

First: read README.md, SETUP.md, app.py, requirements.txt, and every file in
engine/ and ui/. Then run `pytest -q` and `python -c "from engine.simulation
import compare; print(compare('rajdhani_delay',120)[1].kpis())"` to confirm
everything works.

Do NOT change any code yet. When done, give me:
1. a 5-line plain-English summary of how the current code works,
2. a list of the 10 most important things to improve or add next, in priority
   order,
3. which file each change belongs in.
Wait for my approval before editing anything.
```

### Prompt 1 — Verify and fix the baseline
```
Run the app and the tests. There may be bugs in the KPI math (throughput is low
because schedules span more than 120 minutes, and the AI and FCFS controllers
produce nearly identical results).

Tasks:
1. Read engine/simulation.py carefully.
2. Explain why FCFS and AI give almost the same total_delay.
3. Propose a concrete fix so the AI controller measurably outperforms FCFS on the
   rajdhani_delay scenario (e.g., look-ahead to hold a low-priority train earlier
   so a high-priority train isn't blocked at a single-line block).
4. Implement the fix in small steps, running pytest after each change.
5. Add a test in tests/test_decision.py proving AI total_delay is at least 10%
   lower than FCFS on rajdhani_delay over 180 minutes.

Explain every change before making it. Keep all existing tests passing.
```

### Prompt 2 — Improve the data so the demo is believable
```
We need the demo to be more realistic. In data/timetable.json and data/section.json:

1. Add 4-6 more trains so there are ~15 trains total, with a mix of Rajdhani,
   Shatabdi, Superfast, Express, Passenger, and Freight in both directions.
2. Spread departures so conflicts on single-line blocks B3 (PWL-KSV) and
   B4 (KSV-MTJ) are common in the first 60 minutes.
3. Give realistic 5-digit train numbers and passenger counts.
4. After editing, run all 5 scenarios through compare() for 180 minutes and print
   a table of throughput, total_delay, punctuality, pax_minutes, and
   safety_violations for both FCFS and AI. AI should beat FCFS on delay in at
   least 4 scenarios; safety must stay 0.

Do not change the simulation logic, only the data. Show me the table when done.
```

### Prompt 3 — Extract screens into separate files (clean architecture)
```
Right now app.py contains all 5 screens inline. Refactor without changing
behavior:

- Move each tab into its own file under ui/: screen_map.py, screen_advice.py,
  screen_whatif.py, screen_kpi.py, screen_audit.py.
- Each file exports a single function, e.g. `render_map(sim, state)` that takes
  the simulation and a state dict.
- app.py becomes a thin shell: sidebar + tab routing.
- Keep state in st.session_state as it is now.

After refactoring, run the app and click through every tab to confirm nothing
broke. Run pytest. Explain the new app.py structure.
```

### Prompt 4 — Make the Live Map look like a real control room
```
Improve ui/screen_map.py and ui/theme.py:

1. Draw stations as labeled boxes with loop count shown, not just dots.
2. Color blocks by state: grey=free, amber=occupied (single line), red glow =
   conflict predicted in next 15 min.
3. Add a small direction arrow on each train and show its speed on hover.
4. Add a legend for train priority colors.
5. Add a "speed" label on each block (km/h).
6. When a conflict is predicted, make the block pulse (animate opacity in
   Plotly) and show a small warning tag with the countdown.

Keep everything in Plotly (no JS). Test all 5 scenarios.
```

### Prompt 5 — Build the real recommendation engine
```
Right now the AI is a simple greedy score at the moment a train wants to enter a
block. Replace/augment it in engine/simulation.py with a look-ahead:

1. Add a function `predict_conflicts(sim, horizon_min=15)` that fast-copies the
   simulation and finds every block where two trains will collide-wait in the
   next horizon minutes.
2. For each conflict, enumerate the 3-5 cheapest resolutions (hold train A at
   its current station for 2/4/6 min, or route via loop if one exists).
3. Score each resolution by: total passenger-weighted delay added + priority
   penalty, with a hard constraint of zero block collisions.
4. Pick the best, and return a Recommendation object with: action, train(s)
   affected, hold duration, plain-English reason, and estimated KPI impact.
5. Show this on Screen 2 with Accept/Reject buttons; Accept applies the hold and
   Reject logs an override.

Add tests for predict_conflicts and the resolver in tests/test_conflict.py.
Explain the scoring math in comments.
```

### Prompt 6 — What-If screen + audit log
```
In ui/screen_whatif.py and ui/screen_audit.py:

1. What-If: let the user pick a train currently at a station, set a hold time,
   and "preview" the outcome by cloning the simulation and running it 30 min.
   Show the resulting total_delay vs the AI recommendation in a small bar chart.
   Buttons: "Apply my decision" and "Use AI instead".
2. Audit: show a table of every decision (time, train, AI action recommended,
   controller action accepted/rejected, outcome KPI). Persist it for the run in
   session state. Add an auto-generated "shift summary" paragraph at the top:
   "N conflicts resolved, M overrides, X passenger-minutes saved, 0 safety
   violations."

Test manually by running the app and clicking through.
```

### Prompt 7 — Polish, KPIs, and the comparison chart
```
Final polish:

1. In screen_kpi.py, make the AI-vs-Manual comparison run automatically when a
   scenario loads, and show animated number tiles + a grouped bar chart.
2. Add a line chart of cumulative delay over the 180 minutes for both modes.
3. Add a "Safety Shield" badge that is always visible and shows 0 violations;
   if a violation ever occurs (it shouldn't), it turns red and stops the sim.
4. Add a "confidence" percentage to each recommendation (e.g., how much better
   it is than the second-best option).
5. Add a replay time-slider on Screen 5 so you can scrub through the event log.

Run all tests and all 5 scenarios. Give me a final checklist of what works.
```

### Prompt 8 — Stretch only if core is solid (LLM copilot)
```
Add an optional LLM copilot to screen_advice.py:

1. Read the API key from an environment variable GEMINI_API_KEY (do not hardcode).
2. Add a text box where the controller types "what if I hold train 12956 at Palwal
   for 5 minutes?"
3. Send the current simulation state + the question to the Gemini API (free tier
   is fine). Parse the response, and if it contains a suggested action, show it
   as a card with "Apply" / "Ignore".
4. If the API fails or no key is set, show a friendly message and keep working.
5. Cache 3 known demo questions so the demo works without internet.

Add .env to .gitignore. Explain how to get a key from aistudio.google.com.
```

---

## PART 5 — Git / how your team works in parallel

Do this on **Day 1 with all 6 members** on a call.

1. One person creates a GitHub repo named `RailMind` (private is fine) at
   https://github.com/new. Don't add a README (you already have one).
2. On your laptop, in `Documents\RailMind`:
   ```
   git init
   git add .
   git commit -m "starter scaffold"
   git branch -M main
   git remote add origin https://github.com/<your-username>/RailMind.git
   git push -u origin main
   ```
3. In GitHub → Settings → Collaborators → add the other 5 teammates.
4. Each teammate clones:
   ```
   git clone https://github.com/<your-username>/RailMind.git
   cd RailMind
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   pip install pytest
   ```
5. Each person works on **their own branch**, never on `main`:
   ```
   git checkout -b feature/<their-name>-<what-they-are-building>
   ```
   Example: `feature/arjun-recommendation-engine`.
6. When done with a piece:
   ```
   git add .
   git commit -m "add look-ahead conflict resolver"
   git push origin feature/arjun-recommendation-engine
   ```
   Then on GitHub click **"Open a Pull Request"**, ask one teammate to read it,
   they click **Approve**, then **Squash and merge**.
7. Every morning, each person runs:
   ```
   git checkout main
   git pull origin main
   ```
   before starting work. This prevents giant merge conflicts.

**File ownership so people don't collide:**
- AI person → `engine/simulation.py`, `engine/conflict.py`, `tests/`
- Simulation person → `engine/model.py`, `data/*.json`
- UI person → `ui/screen_map.py`, `ui/screen_kpi.py`, `ui/theme.py`
- Integration lead → `app.py`, `ui/screen_advice.py`, `ui/screen_whatif.py`
- Data/testing person → `data/`, `tests/`, scenario design
- Design/PPT person → `docs/`, styling, Hindi labels, PPT, video

---

## PART 6 — What each of you needs to learn

You do **NOT** all learn everything. Each person learns their slice.

### Everyone (first 2 days)
- [ ] Basic terminal: `cd`, `dir`/`ls`, running commands, `Ctrl+C` to stop.
- [ ] Git basics: clone, add, commit, push, pull, branch, PR. (Do the GitHub
      "Hello World" tutorial: https://docs.github.com/en/get-started)
- [ ] Python: variables, lists, dicts, `if/for`, functions, classes, `import`,
      f-strings, `with open(...)` for JSON.
- [ ] Virtual environments: `python -m venv .venv`, activate, `pip install`.
- [ ] How to read a traceback when code errors (the last line + file/line).
- [ ] Railway vocabulary: block section, loop, signal, precedence, crossing,
      priority (Rajdhani → freight). Watch 2 YouTube videos.

### AI / decision lead
- [ ] Python dictionaries/lists fluency; list comprehensions.
- [ ] Object-oriented programming (classes, `self`, `__init__`).
- [ ] The `copy.deepcopy` trick (for look-ahead simulation).
- [ ] Scoring/objective functions and why you weight passenger-minutes.
- [ ] (Stretch) Google OR-Tools CP-SAT — do their official "job shop" example:
      https://developers.google.com/optimization/scheduling/job_shop
- [ ] pytest: writing a test that asserts something.

### Simulation / domain lead
- [ ] Python classes and type hints.
- [ ] JSON editing and the `json` module.
- [ ] Discrete-time simulation: a `for` loop where each step = 1 minute.
- [ ] NetworkX basics (optional — only if you want graph algorithms).
- [ ] How to read an Indian Railways timetable (station codes, train numbers).

### Frontend / UI lead
- [ ] Streamlit: `st.tabs`, `st.columns`, `st.button`, `st.slider`,
      `st.selectbox`, `st.plotly_chart`, `st.dataframe`, `st.session_state`.
      Walk through https://docs.streamlit.io/get-started/fundamentals
- [ ] Plotly: `go.Figure`, `Scatter`, `Bar`, layouts, colors.
- [ ] A little HTML/CSS for the custom cards (Streamlit `st.markdown(...,
      unsafe_allow_html=True)`).
- [ ] How to use Streamlit's auto-rerun model (don't fight it).

### Integration / backend lead
- [ ] Streamlit session state (this is the trickiest thing — read the docs).
- [ ] How modules import each other (`from engine.simulation import Simulation`).
- [ ] `if __name__ == "__main__"` (not needed for streamlit but good to know).
- [ ] Basic debugging: print statements, reading errors, using `gemini` to
      explain a traceback.
- [ ] dotenv for API keys (`pip install python-dotenv`).

### Data / testing lead
- [ ] pytest: `assert`, test files named `test_*.py`, running `pytest -q`.
- [ ] Edge cases: empty station, all loops full, two trains at same block,
      train at final station.
- [ ] How to read and edit JSON without breaking it (use VS Code — it flags
      syntax errors in red).
- [ ] Good scenarios: design them so they actually create conflicts.

### Design / research / PPT lead
- [ ] Figma basics (free): frames, rectangles, text — for wireframes.
- [ ] Google Slides / PowerPoint storytelling: one idea per slide.
- [ ] OBS Studio for screen recording (the backup demo video).
- [ ] The problem statement front to back; be able to explain it in 60 seconds.
- [ ] Indian Railways operations: how a section control room actually works.
      Search YouTube for "railway section controller working".
- [ ] A little Streamlit/CSS to help polish colors and spacing.

### Good free learning resources
- Python basics: https://docs.python.org/3/tutorial/ (do chapters 1–9)
- Streamlit: https://docs.streamlit.io/get-started
- Plotly: https://plotly.com/python/plotly-fundamentals/
- Git: https://docs.github.com/en/get-started/using-git
- OR-Tools: https://developers.google.com/optimization/introduction/python
- Railway signals (10-min video): search "railway block signalling explained"
- Flatland (inspiration, optional): https://flatland-association.github.io/flatland-book/

---

## PART 7 — Your first 3 days, hour by hour

### Today (Day 0 — tonight)
- [ ] Install Python, VS Code, Git, Node.
- [ ] `npm i -g @google/gemini-cli`.
- [ ] Get the RailMind files into `Documents\RailMind`.
- [ ] Create venv, install deps, `streamlit run app.py` → see it working.
- [ ] Run `gemini`, paste **Prompt 0**.
- [ ] Read the summary it gives you. Don't code more tonight.

### Day 1 — Team setup + shared repo
- [ ] Everyone on a call; one person makes the GitHub repo and pushes.
- [ ] Everyone clones, installs, runs the app.
- [ ] Each person makes their first branch, adds their name to `TEAM.md`,
      opens a PR, merges it. (Proves the whole team can use git.)
- [ ] Walk through the code together: who owns which file.
- [ ] Each person reads their own file with Gemini and asks it to explain.

### Day 2 — Fix + understand the core
- [ ] AI + simulation leads: run **Prompt 1** with Gemini. Understand every line
      of the fix it proposes; don't approve blind.
- [ ] UI lead: experiment with `st.plotly_chart` and the map colors.
- [ ] Data lead: run **Prompt 2**, design believable trains.
- [ ] Design lead: start wireframes for the 5 screens in Figma.
- [ ] End of day: merge to `main`; all tests pass.

### Day 3 — Refactor + visible progress
- [ ] Run **Prompt 3** (split screens) under the integration lead.
- [ ] AI lead starts **Prompt 5** (look-ahead resolver).
- [ ] UI lead starts **Prompt 4** (prettier map).
- [ ] Design lead has first PPT outline (problem, approach, architecture,
      novelty, impact).

By end of Day 3 you should have a prettier map, a smarter AI, and a clear
architecture. The remaining prompts (5→8) fill Days 4–10; Days 11–14 are polish,
testing, video, and rehearsal.

---

## The one thing to remember
**Work small, test after every change, commit after every prompt.** Gemini will
try to do too much if you let it — keep prompts focused on one screen or one
function. When in doubt, ask it: *"explain this to me like I have never coded
before"*. If you don't understand a change, don't approve it.
