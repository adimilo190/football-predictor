# Football Predictor — working agreement

## Context
Portfolio project (CV) — a web app for following football competitions, with result
prediction and ML.
Assumptions: `instructions/project-assumptions.md`. Stack: `instructions/tools.md`.
Plan: `instructions/ROADMAP.md`.
Deadline: end of September 2026.

## LEARNING MODE (the most important rule)
The project owner is still learning the tools in use (FastAPI, React, TS, SQL, git, ML...).
- Reply **in Polish** (chat conversations and explanations of concepts are always in Polish).
- For every new tool or concept: briefly explain **what it is, what it is for and how
  it works** — before using it.
- **Write code in English**: comments, docstrings, variable and function names —
  everything in English (professional standard, this repo goes on a CV). Comments must
  be helpful and explain the "why".
- Do not do everything for the user in one go — work in stages, explaining decisions.
  Prefer small steps that can actually be understood.
- **Session rhythm (agreed after Session 3):** do ONE item of the plan at a time → say
  exactly what changed and why → **ask whether to move on to the next step** — and wait
  for an answer. Never run through a whole session TODO in one stretch, even when "it is
  going well".

## End-of-session ritual (MANDATORY)
1. Write the log `instructions/sessions/session-NN.md`: what was done, which decisions
   were taken and why, what we learned, a precise TODO for the next session.
2. Update the statuses in `instructions/ROADMAP.md`, add a section to
   `instructions/progres.md` and refresh `instructions/project-structure.md` (new
   files/folders + the "State as of: Session NN" heading).
3. **Set homework:** list the specific documentation/materials to read before the next
   session — tied to that session's TODO. For each item give a link, why it matters
   (which concept or tool) and what to pay attention to. Append this at the end of the
   session log as a "Homework" section.
4. Commit (descriptive message in English) + push to GitHub.

## Environment (important technical details)
- The code lives in WSL: `/home/micmilo190/football-predictor` (from Windows:
  `\\wsl.localhost\ubuntu\home\micmilo190\football-predictor`).
- **Run git and Python INSIDE WSL**, e.g.:
  `wsl.exe -d ubuntu -e sh -c "cd /home/micmilo190/football-predictor && git status"`
  (git from Windows over a UNC path throws "dubious ownership" and is slow).
- venv: `venv/` (Python 3.10) — use `venv/bin/python`, `venv/bin/pip`.
- PostgreSQL runs in WSL (localhost:5432, database `football_db`).
- Secrets in `.env` (do NOT commit!). Template: `.env.example`. After adding a new
  variable — update `.env.example`.
- After installing packages: `venv/bin/pip freeze > requirements.txt`.

## Conventions
- Backend: FastAPI + SQLAlchemy + PostgreSQL; frontend (from Block 2 onwards): React +
  TypeScript + Vite + Tailwind in the `frontend/` folder.
- **Language in code: English** — commits, comments, docstrings, variable and function
  names in English. Chat conversations (learning mode) stay in Polish.
- Formatting and linting: **Ruff** (`venv/bin/ruff format app/` +
  `venv/bin/ruff check app/`) — the code must pass with no complaints.
- Tests: pytest in `tests/` (from Session 5).
- Database schema changes: through Alembic migrations (from Session 3), never through
  manual DROP/CREATE.
