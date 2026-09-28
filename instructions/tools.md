# Technology Stack and Tools

## Frontend (user interface)
* **Language:** TypeScript (a layer on top of JavaScript that enforces typing).
* **Framework:** React.js (for building a dynamic single-page application).
* **Styling:** Tailwind CSS (modern, fast component styling).

## Backend (business logic and API)
* **Language:** Python.
* **Framework:** FastAPI (a modern, fast web framework).
* **Supporting libraries:**
  * `httpx`: asynchronous communication with the external API-Football service.
  * `SQLAlchemy`: ORM library for working with the database without raw SQL.

## Database
* **Engine:** PostgreSQL (relational database, running inside the WSL/Linux environment).

## Machine Learning & Data Science (planned for Phases 4 and 5)
* **Data processing:** pandas (working with large tables of historical data).
* **Machine learning:** scikit-learn (building models, e.g. Random Forest, logistic
  regression).

## DevOps and organisation
* **Version control:** Git & GitHub.
* **API testing:** Postman.
* **Python environment:** virtualenv (venv) for package isolation.
* **Editor:** VS Code (with the SQLTools extension for inspecting the database).
* **Shell / terminal:** **Bash in WSL** (Ubuntu). Note: a `bash`/Linux command typed in
  the terminal runs inside the **Linux virtual machine (WSL)**, not in Windows. All the
  code, git, Python and PostgreSQL live on the WSL side
  (`/home/micmilo190/football-predictor`). That is why git and Python are run inside WSL
  — git from Windows over a UNC path throws a "dubious ownership" error and is slow
  (details in `CLAUDE.md`).

---

## Additions after the stack review (Session 1, 2026-07-02)
The base stack was judged very good and in line with industry standards. Added:

* **python-dotenv → later pydantic-settings** — secrets and configuration in `.env`,
  never in code. *(already in place)*
* **Vite** — the standard build tool for React apps (fast dev server, simple TS setup).
* **Alembic** — database schema migrations; `create_all` can create tables but cannot
  change them (from Session 3).
* **pytest** — automated backend tests; a strong plus on a CV (from Session 5).
* **Ruff** — very fast Python linter + formatter (the 2025/26 standard).
* **TanStack Query** — professional data fetching in React (cache, loading/error states)
  (Block 2).
* **GitHub Actions** — simple CI (lint + tests on every push); low cost, high impact on a
  CV (Session 24).
* **Note on Postman:** FastAPI ships interactive `/docs` (Swagger UI) — enough for
  day-to-day work; Postman is still worth learning along the way.
* **API-Football risk:** the free plan allows 100 requests/day and may not expose the
  current season — verified in Session 3. Plan B: **football-data.org** (free: our 6
  leagues + Champions League, current season; no domestic cups). Historical data for ML:
  **football-data.co.uk** (CSV, no limits).
* **Stretch (if time allows):** Docker + docker-compose, deployment (Railway/Render +
  Vercel), JWT auth.
