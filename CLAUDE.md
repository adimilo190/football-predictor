# Football Predictor — working agreement

Conventions for this repository: how the code is written, how the project is documented,
and how work is split between the repo owner and an AI assistant (Claude Code). Read this
before contributing or before running an assistant against the project.

Project documents: [`instructions/project-assumptions.md`](instructions/project-assumptions.md)
(what is being built), [`instructions/tools.md`](instructions/tools.md) (the stack),
[`instructions/ROADMAP.md`](instructions/ROADMAP.md) (the plan),
[`instructions/project-structure.md`](instructions/project-structure.md) (a map of every file).

## Language

- **Code and documentation are English** — comments, docstrings, variable and function
  names, commit messages, README, the docs in `instructions/`. Comments explain the
  **why**, not the what; the code already says what it does.
- **Working conversations are held in Polish**, and the session logs in
  `instructions/sessions/` are written in Polish (see that folder's `README.md`).

## How work is done

- **Implementation is written by the repo owner.** An assistant explains the approach,
  points at the file and the place, and reviews the result — it does not type the code
  unless explicitly asked to.
- **One planned item at a time.** Finish it, state exactly what changed and why, then
  confirm before moving on. No batching a whole session's TODO into one stretch.
- **Git is operated by the owner.** An assistant may stage nothing and push nothing:
  it prepares changes, shows `git status`/diffs and suggests a commit message, but
  `commit`, `push`, `reset` and anything rewriting history are run by hand.
- **New tool or concept → explain it first.** What it is, what problem it solves and how
  it works, before it lands in the project.

## End-of-session ritual (mandatory)

1. Write `instructions/sessions/session-NN.md`: what was done, which decisions were taken
   and why, what was learned, and a precise TODO for the next session.
2. Update the statuses in `instructions/ROADMAP.md`, add a section to
   `instructions/progres.md`, and refresh `instructions/project-structure.md` (new
   files/folders + the "State as of: Session NN" heading).
3. List the documentation to read before the next session, tied to its TODO — link, why
   it matters, what to pay attention to. Append it to the session log as "Praca domowa".
4. Commit (descriptive message, English) and push.

## Environment

- The code lives in WSL: `/home/micmilo190/football-predictor` (from Windows:
  `\\wsl.localhost\ubuntu\home\micmilo190\football-predictor`).
- **Run git and Python inside WSL**, e.g.
  `wsl.exe -d ubuntu -e sh -c "cd /home/micmilo190/football-predictor && git status"` —
  git from Windows over a UNC path throws "dubious ownership" and is slow.
- Python 3.10 in `venv/` — use `venv/bin/python`, `venv/bin/pip`. After installing a
  package: `venv/bin/pip freeze > requirements.txt`.
- Node through `nvm` (v20); a shell must load it explicitly
  (`export NVM_DIR=$HOME/.nvm; . $NVM_DIR/nvm.sh`) or it picks up an ancient system Node.
- PostgreSQL runs in WSL (`localhost:5432`, database `football_db`).
- Secrets live in `.env` and are never committed. Template: `.env.example` — update it
  whenever a variable is added.

## Code conventions

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL. Endpoints live in `app/routers/`,
  the prediction model in `app/prediction/` (pure logic, no framework or database
  dependencies in `poisson.py`).
- **Frontend**: React + TypeScript + Vite + Tailwind in `frontend/`. Data fetching goes
  through `src/api/` and TanStack Query — components never call `fetch` directly.
- **Formatting and linting must pass clean**: `venv/bin/ruff format app/` +
  `venv/bin/ruff check app/`; `npm run lint` + `npx tsc -b` on the frontend.
- **Tests**: pytest in `tests/`, run with `venv/bin/pytest`. They use an isolated
  in-memory database and never touch the real one or the external API.
- **Database schema changes go through Alembic migrations** — never `create_all`, never
  a manual `DROP`/`CREATE`. Generate, read the generated file, then `alembic upgrade head`.
- Prefer explicit loops over dense comprehensions where it helps readability.

## Deployment

Frontend on Vercel, backend on Render, PostgreSQL on Neon — see the README for the
architecture. Things that are easy to forget:

- Configuration that differs between environments (`DATABASE_URL`, `ALLOWED_ORIGINS`,
  `VITE_API_URL`) is set in the hosting panels, not in code.
- A new frontend domain must be added to `ALLOWED_ORIGINS` on the backend, or the browser
  blocks every request.
- `VITE_*` variables are baked into the bundle at build time: they are public, and
  changing one requires a rebuild.
- The `POST /import-*` endpoints require the `X-Import-Token` header (`app/security.py`).
