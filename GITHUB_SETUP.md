# GitHub Setup — RailMind Team Guide

The local git repo is already initialized and the first commit is made. Now you
create the GitHub repo and connect it. Follow these steps exactly.

---

## Part A — You do this once (repo owner)

### 1. Create the empty GitHub repo
1. Go to https://github.com/new and log in.
2. **Repository name:** `RailMind`
3. Choose **Private** (so other teams can't copy your idea).
4. **Do NOT** tick "Add a README", "Add .gitignore", or "Choose a license" — you
   already have all of these locally. Ticking them causes a conflict.
5. Click **Create repository**.
6. On the next page, copy the repo URL. It looks like:
   `https://github.com/YOUR_USERNAME/RailMind.git`

### 2. Tell git who you are (one time on your laptop)
Open a terminal in the `RailMind` folder and run (use your real name/email):
```
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### 3. Connect your local folder to GitHub and push
In the `RailMind` folder:
```
git remote add origin https://github.com/YOUR_USERNAME/RailMind.git
git push -u origin main
```
A browser or terminal login prompt for GitHub will appear. Log in. Done —
refresh the GitHub page and you'll see all the files.

> If you prefer no password prompts every push, install
> [GitHub CLI](https://cli.github.com/) and run `gh auth login`, or set up an SSH
> key. For a 2-week project, logging in via the browser prompt is fine.

### 4. Protect the main branch
1. On GitHub: **Settings → Branages → Branch protection rules → Add rule**.
2. Branch name pattern: `main`
3. Tick:
   - ✅ **Require a pull request before merging** (1 approval)
   - ✅ **Dismiss stale approvals when new commits are pushed** (optional)
4. Save.
Now nobody (including you) can break `main` with a bad push — everything goes
through a reviewed pull request.

### 5. Add your teammates as collaborators
1. On GitHub: **Settings → Collaborators → Add people**.
2. Enter each teammate's GitHub username or email, role: **Write**.
3. They'll get an email invite — they must click **Accept** before they can push.

---

## Part B — Each teammate does this once

1. Install Git from https://git-scm.com (Windows: includes Git Bash).
2. Make a free GitHub account at https://github.com/signup if they don't have one.
3. Tell the repo owner their GitHub username so they can be invited.
4. Accept the email invite.
5. Configure git (their own name/email), in any terminal:
   ```
   git config --global user.name "Their Name"
   git config --global user.email "their-email@example.com"
   ```
6. Clone the repo. Decide where you want it (e.g., `Documents`), then:
   ```
   cd Documents
   git clone https://github.com/OWNER_USERNAME/RailMind.git
   cd RailMind
   ```
7. Set up the Python environment:
   ```
   python -m venv .venv
   .venv\Scripts\activate          (Windows)
   source .venv/bin/activate       (Mac/Linux)
   pip install -r requirements.txt
   pip install pytest
   ```
8. Create your `.env` from the template and paste **your own** API keys:
   ```
   copy .env.example .env          (Windows)
   cp .env.example .env            (Mac/Linux)
   ```
   Then edit `.env` with your own Gemini/Groq keys. Never share this file.
9. Run the app to confirm your setup works:
   ```
   streamlit run app.py
   ```
10. **First PR to prove it works:** create a branch, add your name to `TEAM.md`,
    push, open a PR, ask one teammate to approve, merge it. (See Part C.)

---

## Part C — The daily workflow (everyone, every time)

### Golden rules
- 🚫 **Never commit directly to `main`.** Not even a "tiny fix".
- ⬇️ **Pull `main` every morning** before you start.
 -🌿 One task = one branch = one pull request.
- ✅ Run `pytest -q` before you push. Don't push broken code.
- 📝 Write clear commit messages in English: `add look-ahead conflict resolver`.
- 🔍 Review each other's PRs. If you don't understand a change, ask.

### Step-by-step for making a change

```bash
# 1. Get the latest code
git checkout main
git pull origin main

# 2. Create your branch (name it: feature/yourname-what-you-are-doing)
git checkout -b feature/arjun-recommendation-engine

# 3. WRITE YOUR CODE / make changes...

# 4. Check what changed
git status
git diff

# 5. Run tests
pytest -q

# 6. Stage and commit
git add .
git commit -m "add look-ahead conflict resolver and tests"

# 7. Push your branch to GitHub
git push origin feature/arjun-recommendation-engine
```

Then on GitHub:
1. You'll see a **"Compare & pull request"** button — click it.
2. Title: short summary. Description: what you changed and why.
3. Assign **one reviewer** (a teammate).
4. Click **Create pull request**.
5. Wait for approval. The reviewer reads the diff, may ask questions or request
   changes, then clicks **Approve**.
6. Click **Squash and merge** → confirm. Then delete the branch.

### The next day
```bash
git checkout main
git pull origin main
```
Start a new branch for your next task. Repeat.

---

## Part D — If something goes wrong

### "I have a merge conflict"
This happens when two people edited the same lines. Don't panic.
1. Git marks the conflicted file with `<<<<<<<`, `=======`, `>>>>>>>`.
2. Open the file in VS Code — it shows "Accept Current / Accept Incoming /
   Accept Both" buttons.
3. Pick the correct version, save.
4. `git add <file>` then `git commit` (git already wrote the merge message).
5. If you're truly stuck, ask the team lead — don't randomly click things.
6. **Prevention:** pull `main` every morning; split work by file/module so two
   people rarely touch the same code.

### "I committed something I shouldn't have (e.g., a secret key)"
- Tell the team lead immediately.
- If it's an API key, **revoke it** on the provider's website and make a new one.
- Git history can be cleaned, but assume the key is burned once pushed.

### "I committed a huge file / __pycache__ / .venv"
- Make sure `.gitignore` lists it.
- Remove it from git tracking (but keep the file locally):
  ```
  git rm -r --cached __pycache__
  git commit -m "stop tracking __pycache__"
  git push
  ```

### "My push was rejected"
- Someone else pushed new commits to `main` (or your branch). Do:
  ```
  git pull --rebase origin main     # if on main
  ```
  Fix any conflicts, then push again.

### "I want to undo my last commit (but keep the changes)"
```
git reset --soft HEAD~1
```

### "I messed up my branch and want to start over"
```
git checkout main
git pull origin main
git branch -D my-broken-branch
git checkout -b feature/fresh-start
```

---

## Part E — Good habits that save you pain

- **Commit small and often.** 5 small commits are better than 1 giant one.
- **Don't commit generated folders**: `.venv`, `__pycache__`, `.env`,
  `.streamlit/secrets.toml`. They're already in `.gitignore`.
- **Run the app and tests before you push.** Green tests = happy teammates.
- **Don't push model checkpoints or huge data files** (>50 MB). GitHub rejects
  files over 100 MB. Use a `.gitignore` or Git LFS only if absolutely necessary.
- **Review PRs kindly but carefully.** You're collectively responsible for the
  code. Ask "what does this line do?" if unsure.
- **Keep the README updated.** If you add a setup step, write it down.
- **One merge = still works.** After merging anyone's PR, the team lead should
  pull and run the app to confirm `main` still runs.

---

## Part F — File ownership (so people don't collide)

| File / folder | Owner |
|---|---|
| `app.py` | Team Lead / Integration |
| `engine/simulation.py`, `engine/conflict.py` | AI Lead |
| `engine/model.py`, `data/*.json` | Simulation / Domain Lead |
| `ui/theme.py`, `ui/screen_map.py`, `ui/screen_kpi.py` | Frontend Lead |
| `ui/screen_advice.py`, `ui/screen_whatif.py`, `engine/safety.py` | Team Lead / Integration |
| `tests/`, scenario design | Data / Testing Lead |
| `docs/`, `README.md`, `SETUP.md` styling | Design / PPT Lead |

When you need to change someone else's file, open a PR and **tag them as a
reviewer**. Don't edit their file without telling them.

---

## Quick reference card (print this)

```
FIRST TIME:
  git clone <repo-url>
  cd RailMind
  python -m venv .venv  → activate → pip install -r requirements.txt
  cp .env.example .env  → add your keys
  streamlit run app.py

EVERY MORNING:
  git checkout main
  git pull origin main

NEW TASK:
  git checkout -b feature/yourname-task

DONE TASK:
  pytest -q
  git add .
  git commit -m "describe the change"
  git push origin feature/yourname-task
  → Open Pull Request on GitHub → get 1 approval → Squash and merge

NEXT DAY:
  git checkout main && git pull
```
