# RailMind — Skills Required & Team Role Division

A 2-week, 6-person, first-project team. This document lists **every skill the
project touches**, splits them by role, and tells each person exactly what to
learn and what they own.

---

## 1. The full skill map (everything the project needs)

These are grouped by domain. Don't panic — **no single person learns all of this**.
Each role only needs its column.

### A. Programming fundamentals (everyone needs the basics)
- Python syntax: variables, numbers, strings, booleans
- Lists, dictionaries, tuples, sets
- `if/elif/else`, `for`/`while` loops, list comprehensions
- Functions: parameters, return values, default args, scope
- **Classes and objects** (`class`, `__init__`, `self`, methods) — *important*
- Imports: `from x import y`, how modules work
- File I/O: `open`, `json.load`, `json.dump`
- f-strings for formatting
- Reading a Python traceback (find the file + line + error type at the bottom)
- `print()` debugging and using VS Code's debugger

### B. Tooling / environment (everyone)
- Terminal basics: `cd`, `dir`/`ls`, `mkdir`, running a command, `Ctrl+C`
- **Virtual environments**: `python -m venv .venv`, activate, `deactivate`
- **pip**: `pip install`, `pip freeze > requirements.txt`
- **Git + GitHub**: clone, add, commit, push, pull, branch, checkout, merge,
  pull request, resolving simple conflicts
- **VS Code**: opening folders, extensions, integrated terminal, problems panel
- Running a Streamlit app and stopping it

### C. Data & domain knowledge
- JSON syntax (objects, arrays, numbers, strings, booleans, null)
- Editing JSON without breaking commas (VS Code flags errors in red)
- Railway domain: block section, station loop, signal, up/down direction,
  precedence, crossing, train priority (Rajdhani → freight), working timetable
- How to read a train schedule (origin, destination, departure, stops)
- Designing scenarios that *actually create conflicts* on single-line blocks
- Basic data validation (e.g., every `from`/`to` in blocks must be a real station)

### D. Simulation engine (backend logic)
- Object-oriented programming deeply: classes, instances, methods, inheritance
- Type hints (`str`, `int`, `float`, `Optional[str]`, `list[Train]`)
- Dataclasses (`@dataclass`) for clean data containers
- Enums / constants (priority levels, directions)
- A **discrete-time simulation loop**: `for step in range(N): ...`
- State machines: a train is WAITING → ON_BLOCK → ARRIVING → DWELLING → ...
- Enforcing invariants (one train per block — the safety rule)
- `copy.deepcopy` to clone the state for look-ahead / what-if
- The `random` module for injecting disruptions (optional)
- Performance awareness: don't do O(n²) work you don't need to

### E. Optimization / "AI" brain
- Writing a **scoring/objective function**: combine multiple factors with weights
- Enumerating candidate actions (hold 2/4/6 min, release, route via loop)
- Picking the min/max by score (`max(candidates, key=score)`)
- Greedy / heuristic search concepts
- **Constraints**: which actions are infeasible (block occupied, no free loop)
- A baseline controller (FCFS) to compare against
- Measuring outcomes: total delay, passenger-minutes, throughput
- (Stretch) **Google OR-Tools CP-SAT**: variables, constraints, objective,
  solving. Do the official job-shop tutorial first.
- (Stretch) Explanation: break the score into components so the UI can show
  "because pax=1180 and priority=5..."

### F. Frontend / dashboard (Streamlit + Plotly)
- Streamlit fundamentals: `st.title`, `st.markdown`, `st.columns`, `st.tabs`,
  `st.sidebar`, `st.button`, `st.slider`, `st.selectbox`, `st.dataframe`,
  `st.metric`, `st.plotly_chart`, `st.warning`/`st.success`/`st.info`
- **`st.session_state`** — the trickiest concept; how Streamlit reruns the script
  and how to keep state (the simulation, play/pause) across reruns
- Auto-refresh patterns for the live map (`st.fragment(run_every=...)` or
  `st_autorefresh`)
- Plotly: `go.Figure`, `go.Scatter` (lines + markers), `go.Bar`, `go.Layout`,
  traces, colors, hover text, turning axes off
- Coordinate math: interpolating a train's position along a block (x,y lerp)
- Basic **HTML/CSS** for custom cards via `st.markdown(..., unsafe_allow_html=True)`:
  divs, spans, background, color, padding, border-radius, flexbox
- Dark theme color choices and readable contrast
- Responsive layout with `st.columns`

### G. Integration / glue
- Python module imports across folders (`from engine.simulation import Simulation`)
- `if __name__ == "__main__"` (conceptual)
- Sharing one `Simulation` object between UI tabs via session state
- Wiring buttons → engine actions → re-render
- API keys with **python-dotenv** / `.env` (for the stretch LLM copilot)
- Calling an HTTP API with the `requests` library (stretch)
- Basic error handling: `try/except`, showing a friendly message instead of crashing

### H. Testing & quality
- **pytest**: writing `test_*.py`, functions named `test_*`, `assert`
- Running `pytest -q`
- Safety test: no two trains ever share a single-line block
- Regression test: AI beats FCFS on the delay scenario
- Edge-case thinking: empty section, all loops full, train at destination,
  zero passengers (freight), broken signal
- Manual smoke test: click every button in the UI before each demo rehearsal

### I. Design, research, presentation
- Problem statement: explain it in 60 seconds to a stranger
- Railway operations research: what real controllers do (YouTube + papers)
- **Figma** basics: frames, rectangles, text, colors — for wireframes
- Google Slides / PowerPoint: title slide, problem, solution, architecture,
  novelty, demo, impact, feasibility, team, thank-you
- Storytelling: before (pain) → after (AI) → numbers → why it's safe
- **OBS Studio** (or phone) for a 3-minute backup screen recording
- A one-page PDF summary for judges to take away
- Basic Hindi/English labels if bilingual
- Confidence presenting and answering Q&A

### J. AI-tools literacy (everyone, this is how you build fast)
- Using **Gemini CLI** in the project folder
- Asking precise prompts: file + function + desired behavior + constraints
- Reading an AI-generated diff before accepting it
- Asking "explain this like I'm a second-year student" when confused
- Asking it to write tests, explain errors, and refactor
- **Not** blindly accepting code you cannot explain (judges will ask)
- Git-committing after every successful AI change so you can roll back

---

## 2. Role division for a 6-person team

Each role has: **primary skills**, **what they own**, **what they build**, and
**what to learn first**. One person = one owner; others can contribute via PRs.

> If your team is smaller: merge #4 into #1, #6 into #3. If someone is strong,
> they can own two adjacent roles.

### Role 1 — AI / Decision Lead
- **Primary skills:** E (optimization), D (engine), H (testing)
- **Owns:** `engine/simulation.py`, `engine/conflict.py`, `engine/optimizer.py`
  (stretch), `tests/test_conflict.py`, `tests/test_decision.py`
- **Builds:** the FCFS baseline, the AI scoring function, look-ahead conflict
  predictor, recommendation engine, confidence math, OR-Tools upgrade (stretch)
- **Learn first:** Python classes, dataclasses, scoring functions, deepcopy,
  pytest; then OR-Tools job-shop tutorial if time permits
- **Demo day:** explains *why* the AI holds train A instead of B

### Role 2 — Simulation / Domain Lead
- **Primary skills:** D (engine), C (data/domain), A
- **Owns:** `engine/model.py`, `data/section.json`, `data/timetable.json`,
  `data/scenarios.json`
- **Builds:** Station/Block/Train/Network classes, block occupancy & signal
  rules, time-step movement, realistic trains & scenarios that create conflicts,
  KPI math (throughput, delay, punctuality, passenger-minutes)
- **Learn first:** Python OOP, JSON, discrete-time loops, railway vocabulary;
  watch videos of real section controllers
- **Demo day:** explains the digital twin and the safety invariants

### Role 3 — Frontend / Dashboard Lead
- **Primary skills:** F (Streamlit + Plotly), J (AI tools), I (design sense)
- **Owns:** `ui/theme.py`, `ui/screen_map.py`, `ui/screen_kpi.py`, styling
- **Builds:** the live map (stations, blocks, moving trains, conflict glow),
  KPI tiles + charts, dark control-room theme, priority legend, animations
- **Learn first:** Streamlit fundamentals, `st.session_state`, Plotly scatter/
  bar, a little HTML/CSS for cards
- **Demo day:** drives the UI and narrates the map

### Role 4 — Integration / Safety Lead (also team lead)
- **Primary skills:** G (integration), D (engine), F (Streamlit), H (testing)
- **Owns:** `app.py`, `ui/screen_advice.py`, `ui/screen_whatif.py`,
  `engine/safety.py` (the safety shield), overall integration
- **Builds:** wires sidebar + tabs + buttons to the engine, Accept/Reject logic,
  what-if preview, the safety-shield validator, the LLM copilot (stretch)
- **Learn first:** Python imports, session state, how to read a traceback,
  dotenv; coordinate everyone's branches so `main` always runs
- **Demo day:** clicks through advice + what-if, owns the run-of-show

### Role 5 — Data / Testing / QA Lead
- **Primary skills:** H (testing), C (data), A, J
- **Owns:** `tests/`, scenario design, data validation, the "break it" job
- **Builds:** all pytest tests, edge-case scenarios, the 10× demo-run checklist,
  bug reports for the team; may also help with timetable realism
- **Learn first:** pytest, JSON, how to construct a scenario that forces a
  conflict, reading tracebacks; learn enough git to file issues
- **Demo day:** has tested every scenario 10 times; is the reason the demo
  doesn't crash

### Role 6 — Design / Research / PPT Lead
- **Primary skills:** I (design/research/presentation), C (domain), basic F
- **Owns:** `docs/`, Figma wireframes, `SIH25022_PPT.pptx`, demo video, one-pager,
  helps with UI polish & Hindi labels
- **Builds:** the 10-slide deck, the 3-minute demo script, the backup video,
  the "what makes us unique" slide, architecture diagram; helps the UI lead with
  colors/spacing
- **Learn first:** the problem statement front-to-back, Figma basics, Google
  Slides, OBS recording; learn enough Streamlit/CSS to tweak styling
- **Demo day:** opens with the problem, closes with impact; handles PPT and
  backup video if anything fails

---

## 3. Skill overlap matrix (who needs what)

| Skill | Everyone | AI | Sim | UI | Integration | QA | Design |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Python basics + OOP | ✅ | ✅✅ | ✅✅ | ✅ | ✅✅ | ✅ | — |
| JSON / data | ✅ | ✅ | ✅✅ | — | ✅ | ✅✅ | — |
| Git/GitHub | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Terminal + venv + pip | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Streamlit | — | — | — | ✅✅ | ✅✅ | — | ◐ |
| Plotly | — | — | — | ✅✅ | ◐ | — | — |
| HTML/CSS | — | — | — | ✅ | ✅ | — | ◐ |
| Simulation logic | — | ✅ | ✅✅ | — | ✅ | ◐ | — |
| Optimization/scoring | — | ✅✅ | ✅ | — | ◐ | — | — |
| pytest | — | ✅ | ◐ | — | ◐ | ✅✅ | — |
| OR-Tools (stretch) | — | ✅✅ | — | — | — | — | — |
| API/dotenv (stretch) | — | — | — | — | ✅✅ | — | — |
| Railway domain | ✅ | ✅ | ✅✅ | ◐ | ◐ | ◐ | ✅✅ |
| Figma / Slides / OBS | — | — | — | ◐ | — | — | ✅✅ |
| Gemini CLI usage | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

✅✅ = deep, must be strong · ✅ = working knowledge · ◐ = light exposure · — = not needed

---

## 4. How to pick who does what (practical)

Sit together (or on a call) and ask each person:
1. **What do you already know a little?** (e.g., "I made a HTML page in school"
   → UI; "I like logic puzzles" → AI; "I'm good at design/posters" → design)
2. **What do you want to learn?** Motivation matters more than existing skill.
3. **Who is the most organized / can chase people?** That's your integration
   lead and team lead — not necessarily the best coder.
4. **Who is comfortable talking / presenting?** The design/PPT lead and the
   people who'll demo (usually UI + integration leads).

Then assign by **interest + aptitude**, not friendship. It is fine if two people
co-own a role (e.g., AI + Simulation pair up on the engine). Just make sure
**every file has one name next to it** so there are no gaps.

---

## 5. What everyone should learn in the first 2 days (no exceptions)

Before anyone touches a feature file:
1. Install Python, VS Code, Git, Node; verify in terminal.
2. Create a venv, `pip install -r requirements.txt`, run `streamlit run app.py`,
   and click every tab.
3. Clone the repo, make a branch, add your name to `TEAM.md`, push, open a PR,
   merge it.
4. Read your own module's code with Gemini CLI and ask it to explain every
   function out loud.
5. Be able to answer: "What is a block section?" "What happens when two trains
   want the same single-line block?" "Which file would I change to add a new
   train?"

If all 6 of you can do those five things by end of Day 1, you're already ahead of
most SIH teams.

---

## 6. The honest truth about skills for a 2-week first project
- You do **not** need to be "good at Python." You need to be comfortable reading
  code and asking Gemini to explain or modify it.
- The hardest skill is **integration** — making six people's files work together.
  That's why the integration lead is also the team lead and why `main` must
  always run.
- The second-hardest skill is **not overbuilding**. A small thing that works and
  is explained well beats a grand thing that crashes.
- Every person should be able to explain *their* module on a whiteboard. If you
  can't, you don't own it yet — go read it with Gemini until you can.
