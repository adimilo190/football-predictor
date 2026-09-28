# Project structure — a map of files and folders

> The whole project summarised in one place: what lives in every file/folder and why.
> **This file is updated whenever the structure changes** (a new file = a new entry here) —
> it is a fixed part of the end-of-session ritual.
> State as of: Session 19 (2026-09-28).

---

## Root directory

| File / folder | What it is and what it is for |
|---|---|
| `app/` | **Backend code** (Python package, FastAPI) — details below |
| `frontend/` | **Frontend code** (React + TypeScript + Vite + Tailwind) — details below |
| `tests/` | **pytest tests** — they exercise the API through `TestClient` on an isolated database, without starting a server |
| `alembic/` + `alembic.ini` | **Database migrations** — details below |
| `instructions/` | **Project documentation** (plans, logs, decisions) — details below |
| `venv/` | Python virtual environment (isolated packages). NOT in git. We use `venv/bin/python`, `venv/bin/pip` |
| `.env` | **SECRETS**: `DATABASE_URL`, `API_FOOTBALL_KEY`, `IMPORT_TOKEN`, `ALLOWED_ORIGINS`. NOT in git — never commit it! |
| `.env.example` | A template for `.env` with no real values — it IS in git, so everyone knows which variables to set |
| `Procfile` | **Deployment**: the one command the hosting provider runs — `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}` (migrations first, then the server on the port the host assigns) |
| `.python-version` | **Deployment**: pins the Python version (3.10.12) so the host builds with the same interpreter as the local venv |
| `.gitignore` | What git must NOT track (venv, `__pycache__`, `.env`, node_modules, dist) |
| `requirements.txt` | Frozen Python package versions — `pip install -r requirements.txt` recreates the environment (run `pip freeze` after every install) |
| `CLAUDE.md` | The working agreement: learning mode, rhythm (one step at a time), end-of-session ritual, environment (WSL, venv, PostgreSQL) |
| `.claude/` | Claude Code settings for this project (`settings.local.json` — tool permissions) |
| `.vscode/` | Local VS Code settings (`settings.json` — format-on-save: Ruff/Python 4 spaces, Prettier/TS 2 spaces). In `.gitignore` — NOT in git |
| `.git/` | Git's internal database (commit history). Never edited by hand |
| `__pycache__/`, `.ruff_cache/`, `.pytest_cache/` | Automatic Python / Ruff / pytest caches — safe to delete, they regenerate. NOT in git |

---

## `app/` — backend code (FastAPI)

A Python package (`__init__.py`). Layers from the bottom up:

| File | What it does |
|---|---|
| `__init__.py` | Marks the folder as a package, which is what makes `from app...` imports work |
| `config.py` | **The single source of configuration.** The `Settings` class (pydantic-settings) loads `.env`, validates it and fails loudly at startup if something is missing. Also holds the `ALLOWED_ORIGINS` → list split (CORS) and the validator rewriting a legacy `postgres://` URL to `postgresql://`. Everywhere else: `from app.config import settings` |
| `database.py` | **The PostgreSQL connection**: `engine`, `SessionLocal` (session factory), `Base` (model base class) + the `get_db` dependency (one session per request; it lives here to avoid an import cycle) |
| `models.py` | **SQLAlchemy models = tables**: `League` (competition), `Team` (a club — no league, because it plays in several), `Standing` (one table row: league + team + season + statistics), `Fixture` (a match: **two** FKs into `teams` — home/away, score, date, round, status) |
| `schemas.py` | **Pydantic schemas = the API contract** (what goes out): `LeagueResponse`, `TeamResponse`, `StandingResponse` (nested team), `FixtureResponse` (two teams, nullable goals), `BracketRound` (a round + its matches; built by hand), `PredictionResponse`+`ScoreLine` (the prediction: P(1/X/2) + top scores; computed values, so no `from_attributes`) |
| `constants.py` | **Business constants**: `TARGET_LEAGUE_IDS` (**15** competitions = `DOMESTIC_LEAGUE_IDS` + `DOMESTIC_CUP_IDS` + `EUROPEAN_COMPETITION_IDS` with CL/EL/Conference), `DEFAULT_SEASON = 2024`, `KNOCKOUT_ROUNDS` (round names for the `knockout_only` filter), `FINISHED_STATUSES` (`{FT, AET, PEN}` — a played match, for `past-matches`), `HOME_ADVANTAGE = 1.3` (the home-advantage multiplier for the Poisson predictor) |
| `security.py` | **Guard for the admin endpoints**: the `require_import_token` dependency checks the `X-Import-Token` header against `settings.IMPORT_TOKEN` (`secrets.compare_digest`, 401 when missing or wrong). Attached to the whole imports router, so the write endpoints are not public once deployed |
| `main.py` | **A thin entry point** (~35 lines): creates the `FastAPI` app, configures **CORS** (origins from the env variable), registers the routers. The endpoints live in `routers/`. Documentation: `/docs` (Swagger UI) |
| `routers/` | **Endpoints split into modules** — details below |
| `prediction/` | **The prediction model (Poisson)** — pure logic, independent of the API — details below |

**Data flow:** `.env` → `config.py` → `database.py` → `models.py` → (`schemas.py` +) `routers/` ← `main.py`.

### `app/routers/` — endpoints in modules

| File | What it does |
|---|---|
| `__init__.py` | Makes `routers/` a package |
| `competitions.py` | **Reads**: `GET /leagues`, `GET /leagues/{id}/standings` (sorted by `rank`, `joinedload` against N+1), `GET /leagues/{id}/fixtures` (flat list), `GET /leagues/{id}/bracket` (grouped by round + the `knockout_only` filter), `GET /leagues/{id}/seasons` (**available seasons** — a `UNION` of seasons from `standings` (leagues) and `fixtures` (cups), feeding both the table and bracket selectors). Helper `query_fixtures` (DRY) |
| `imports.py` | **Writes / ETL**: `POST /import-leagues`, `POST /import-standings`, `POST /import-fixtures` (leagues + cups + European = `TARGET_LEAGUE_IDS`) plus the `fetch_*` (Extract from API-Football) and `upsert_*` (Transform+Load) functions. Handles rate limits and HTTP errors. **The whole router requires the `X-Import-Token` header** (see `security.py`) |
| `teams.py` | **Team reads**: `GET /teams/{id}/past-matches` (latest finished — `or_` home/away + `FINISHED_STATUSES` + `date desc` + `limit`), `GET /teams/{id}/future-matches` (next scheduled — `status NS` + `date asc`), `GET /teams?search=` (search — `name.ilike("%…%")`, `limit 20`). Matches/results are **cross-competition** (a team's form regardless of the competition) |
| `predictions.py` | **Prediction**: `GET /predict` (two teams within one league → `PredictionResponse`: P(1/X/2) + top 5 scores). 404 validation (both teams must have `standings`), `float()` for clean JSON. Calls `prediction/strength.py` (λ) → `prediction/poisson.py` (the maths) |

### `app/prediction/` — the prediction model (Poisson)

A separate package: **pure prediction logic**. Layers: `strength.py` (data→λ, reads the database) → `poisson.py` (λ→probabilities, no DB). The `routers/predictions.py` endpoint wires them together.

| File | What it does |
|---|---|
| `__init__.py` | Makes `prediction/` a package |
| `poisson.py` | **Pure maths** (no DB): `poisson_pmf` (`λ^k·e^-λ/k!`), `goal_distribution` (the vector P(0..max)), `score_matrix` (`np.outer` of the two distributions + normalisation), `match_outcome_probabilities` (`np.tril(-1)`/`trace`/`triu(1)` → P(1/X/2)), `top_scorelines` (the n most likely scores) |
| `strength.py` | **λ from data** (`standings`): `league_baseline` (average goals per match in a league = the baseline), `team_attack_defence` (attack/defence strength relative to the baseline), `match_lambdas` (assembles λ_home/λ_away + `HOME_ADVANTAGE`). The predictor is **within-league** (strength is relative to its league) |

---

## `frontend/` — frontend code (React + TypeScript + Vite + Tailwind)

A single-page application. Run with `npm run dev` (inside WSL, Node through `nvm`). Node/npm and `node_modules` are NOT in git.

### `frontend/` — configuration files (root)

| File / folder | What it does |
|---|---|
| `index.html` | The page skeleton: `<div id="root">` + `<script src="/src/main.tsx">`. The entry point React injects the app into |
| `package.json` | JS dependencies (React 19, `react-router-dom`, `@tanstack/react-query`, `tailwindcss`, Vite, oxlint, prettier, TypeScript) + the `dev`/`build`/`lint`/`format` scripts |
| `package-lock.json` | Exact frozen versions of every package (the JS equivalent of `requirements.txt`) |
| `vite.config.ts` | Vite configuration: the React and Tailwind plugins |
| `tsconfig*.json` | TypeScript configuration (`tsconfig.json` ties it together, `.app`/`.node` — app code and tooling separately) |
| `.env` | Per-environment configuration: `VITE_API_URL` (the backend address). NOT secret (it ends up in the bundle) but NOT in git |
| `.env.example` | The template for the frontend `.env` — it IS in git |
| `public/` | Files served statically as-is (e.g. the favicon) |
| `README.md` | The default readme from the Vite template |

### `frontend/src/` — application code

| File / folder | What it does |
|---|---|
| `main.tsx` | **React's entry point**: mounts `<App/>` into `#root`, wrapped in `BrowserRouter` (routing) and `QueryClientProvider` (the TanStack Query cache); imports `index.css` |
| `App.tsx` | **Layout + routing**: a shared `<header>` (clickable title → `/`) above `<Routes>`; routes `/` → `HomePage`, `/leagues/:id` → `LeaguePage` (table), `/bracket/:id` → `BracketPage` (bracket), `/teams` → `SearchPage` (search), `/teams/:id` → `TeamPage` (a team's matches), `/predict` → `PredictPage` (the predictor) |
| `index.css` | Global styles: `@import "tailwindcss"` (utilities + preflight) + theme variables and `#root`/`h1` rules. **The dark theme is forced** (dark values in `:root` + `color-scheme: dark`, the `@media prefers-color-scheme` gate removed). ⚠️ The global `h1`/`h2` rules (font/margin) come from the template — being unlayered, they outrank Tailwind utilities; scheduled for cleanup |
| `api/config.ts` | `API_BASE_URL` from `VITE_API_URL` (`import.meta.env` + a fallback). The single source of the backend address |
| `api/standings.ts` | **API layer (tables)**: types `Team`/`Standing` + `getStandings(leagueId, season)` (`fetch` with `?season=` + a `throw` when `!res.ok`) + `getSeasons(leagueId)` (the list of available seasons). Used as a `queryFn` |
| `api/bracket.ts` | **API layer (brackets)**: types `Fixture`/`BracketRound` + `getBracket(leagueId, season, knockoutOnly)`; plus `Matchup` + `groupIntoMatchups` (grouping two-legged ties into pairs for the tree) |
| `api/teams.ts` | **API layer (teams)**: `searchTeams(search)` (`?search=` + `encodeURIComponent`), `getPastMatches(id)`, `getFutureMatches(id)` — the `Team`/`Fixture` types reused through `import type`. Used as a `queryFn` |
| `api/predictions.ts` | **API layer (prediction)**: types `ScoreLine`/`Prediction` (mirroring `PredictionResponse`) + `getPrediction(homeId, awayId, leagueId, season)` (`GET /predict`; **query keys in snake_case** = as the backend names them, JS variables in camelCase). Used as a `queryFn` |
| `hooks/useDebounce.ts` | **Custom hook** `useDebounce<T>(value, delayMs)`: a delayed copy of a value (`useState` + `useEffect` + `setTimeout` + a `clearTimeout` cleanup). Used by `SearchPage` — fetch once typing stops, not on every keystroke |
| `hooks/useSeasonSelector.ts` | **Custom hook** `useSeasonSelector(id)`: the season list (`useQuery`) + the user's choice (`useState`) + the effective season (`selectedSeason ?? seasons[0]` = **derived state**, newest by default). Reused by `LeaguePage` + `BracketPage` |
| `components/LeagueTable.tsx` | The league table: a `season` prop; `useQuery(["standings", leagueId, season], getStandings)` (**the season in the key** = a cache per season) → `data`/`isLoading`/`isError`, renders a `<table>` |
| `components/Bracket.tsx` | The bracket: `useQuery(["bracket", leagueId], getBracket)` + a **tournament tree** (round columns with `flex`+`items-stretch`+`justify-around`, `overflow-x-auto`); groups matches through `groupIntoMatchups` and renders `MatchupCard`s |
| `components/MatchupCard.tsx` | A tie card: two teams (crest + name) + per-leg scores in boxes; for a two-legged tie, `1/2/Σ` headers and the aggregate; a row of match dates/times (the `formatDate` helper, `toLocaleString`). **Reused in `TeamPage`** as well (a single match = a tie with one leg, through the `fixtureToMatchup` adapter). Dark-theme styling (`bg-gray-800` card, `bg-gray-700` boxes) |
| `components/PredictionResult.tsx` | **Prediction visualisation**: three 1/X/2 bars (the internal `OutcomeBar` — **DRY**, a `bg-gray-700` track + a fill whose `%` width comes from an **inline style**, because the value is dynamic; dark emerald/amber/sky colours) + the list of most likely scores. Receives `prediction` + team names through **props** (presentation only) |
| `pages/HomePage.tsx` | The home page: a **"Predict match"** card → `/predict` (the predictor) + a **"Find team"** card → `/teams` (search) + an **accordion** built on `<details>` — 6 countries (`COUNTRIES`: league→`/leagues/:id`, cup→`/bracket/:id`) + "European Competitions" (→`/bracket/:id`) |
| `pages/LeaguePage.tsx` | The league page: reads `:id` (`useParams`); **the season selector** — `useState` for the chosen season (UI state) + `useQuery(getSeasons)` (the list) + a `<select>`; passes `leagueId`+`season` to `LeagueTable` |
| `pages/BracketPage.tsx` | The cup competition page: reads `:id` through `useParams` (with a guard), passes `leagueId` to `Bracket` |
| `pages/SearchPage.tsx` | **Team search**: a controlled `<input>` → `useDebounce(300)` → `useQuery(["teamSearch", term], searchTeams, enabled: term.length>0)`; results as `<Link to={/teams/:id}>`. States rendered through a variable + `if` (so the input stays on screen) |
| `pages/TeamPage.tsx` | **A team's matches** (`/teams/:id`): two `useQuery` calls (`getPastMatches`/`getFutureMatches`), guards after the hooks (`if (!past||!future) return null` = type narrowing); the `fixtureToMatchup` adapter + `MatchupCard` reuse; a header (crest + name from the first match) + two columns past/future (`flex gap-8`) |
| `pages/PredictPage.tsx` | **The predictor** (`/predict`): pick a league (`COUNTRIES`→`<select>`) → two teams from it (`useQuery(getStandings)` + **`enabled`**, two selects, reset on league change) → `useQuery(getPrediction)` (**`enabled`**: both picked and different) → renders `PredictionResult`. The season is the `PREDICTION_SEASON` constant (the last full season). The predictor is **within-league** |
| `data/leagues.ts` | The navigation model: types `Competition`/`Country` + `COUNTRIES` (6 countries: league+cup) and `EUROPEAN_COMPETITIONS` (CL/EL/Conference) — ids from API-Football |
| `assets/` | Graphics from the Vite template (`react.svg`, `vite.svg`, `hero.png`) — currently unused |

**Flow:** `main.tsx` → `App.tsx` (routing) → `pages/` → `components/` → `api/` → backend.

---

## `tests/` — automated tests (pytest)

| File | What it does |
|---|---|
| `__init__.py` | Makes `tests/` a package (pytest then adds the project root to `sys.path`) |
| `conftest.py` | **Test infrastructure**: an isolated **in-memory SQLite** database (`StaticPool`), `get_db` swapped through `app.dependency_overrides`, an autouse fixture wiping the database per test, the `client`/`db_session` fixtures |
| `test_main.py` | **14 tests** of the endpoints (Arrange–Act–Assert, each seeding its own data): `/`, `/leagues`, `/standings`, `/fixtures`, `/bracket` (all rounds + proof of sorting, and the `knockout_only` filter), `/seasons` (the `UNION` of standings+fixtures + dedup + order), `/teams/{id}/past-matches` (an airtight scenario for `or_`/status/order), `/teams/{id}/future-matches` (`NS`+`asc`), `/teams?search=` (`ilike` substring + case-insensitivity + `order_by` + an empty result), wrong ids → 404 (standings + team), `/predict` (P(1/X/2) summing to ≈1 + top 5) and a 404 for a team outside the league |
| `test_poisson.py` | **5 tests** of the pure Poisson maths (no DB, known values): `poisson_pmf`, `goal_distribution` (sums to ≈1), `score_matrix` (shape + the 1:0 cell), `match_outcome_probabilities` (61/21/18), `top_scorelines` (ordering). Together with `test_main.py`: **pytest 19/19** |

**Running them:** `venv/bin/pytest -v` (inside WSL). The tests never touch the real database or API-Football.

---

## `alembic/` — database migrations

A migration is a versioned change to the schema (like a commit, but for the table structure). The schema is managed EXCLUSIVELY by Alembic (no `create_all`, no manual DROPs).

| File / folder | What it does |
|---|---|
| `alembic.ini` (in the root) | Alembic configuration; the database address there is a placeholder — the real one is injected by `env.py` from `.env` |
| `env.py` | The startup script: the database URL from `settings` + the models' `Base.metadata` (so `--autogenerate` can see the differences between models and database) |
| `versions/` | **The migration files** (chained through `down_revision`): 1) `create leagues table`, 2) `add teams and standings tables`, 3) `create fixtures table` |
| `script.py.mako` | The template for new migrations |
| `README` | Alembic's default note |

**Workflow:** edit `models.py` → `alembic revision --autogenerate -m "description"` → **read the generated file** → `alembic upgrade head`.

---

## `instructions/` — project documentation

| File / folder | What it contains |
|---|---|
| `project-assumptions.md` | **WHAT we are building**: the goal (portfolio/CV) and the 5 phases (tables/brackets → favourites → predictor → simulator → ML) |
| `ROADMAP.md` | **HOW and WHEN**: the session plan up to 30 September, milestones, statuses, plus the **Risks** section (API limits) and the **Target UX vision** (future navigation) |
| `tools.md` | **WHAT we are building it with**: the stack and environment notes |
| `progres.md` | A condensed list of everything done (one section per session) |
| `project-structure.md` | This file — the project map (updated every session) |
| `sessions/` | **Session logs** (`session-01`…`session-19`): what was done, decisions, lessons, TODO, homework. Written in Polish — they are the owner's learning journal (see `sessions/README.md`) |

---

## Database (PostgreSQL in WSL, `football_db`)

Not a file in the repo, but part of the project:

| Table | What it holds |
|---|---|
| `leagues` | The **15** tracked competitions (6 leagues + 6 domestic cups + CL/EL/Conference; ids from API-Football, name, country, logo) |
| `teams` | Teams — **1962** (league + cup/European) |
| `standings` | League table rows: league + team + season + statistics — **572** (6 leagues × seasons **2022–2026**) |
| `fixtures` | Matches — **7980** (domestic cups + CL/EL/Conference **and** league matches; seasons **2024–2026**) |
| `alembic_version` | Alembic's "bookmark" — the id of the currently applied migration |

---

## What is still to come (per the ROADMAP)

- **Deployment (Session 19)** — IN PROGRESS: the code is prepared (CORS from an env variable, token-guarded import endpoints, `Procfile`, `.python-version`); next up are the hosting provider (backend + PostgreSQL), the frontend on Vercel and a **professional README** for the CV. BEFORE Phases 4/5.
- **Model #2 (Dixon-Coles)** — **blending several seasons** (time weights: the last plus the current one) + a low-score correction; a home/away split from `fixtures`. Then **model #3 (ML)** + a comparison of the models (Phase 5).
- **Phase 4 (Monte Carlo simulator)** — simulating a match/league (after deployment).
- **UI debt**: `TeamSelect` (the duplicated selects in `PredictPage`), cleaning up the element selectors in `index.css` (Vite template leftovers), a loading state for the team lists in `PredictPage`.
- **A league-phase table** (CL/EL/Conference) — computed from matches or imported from standings (postponed).
- Bracket cosmetics: connecting lines between ties; extending `KNOCKOUT_ROUNDS` with domestic cup rounds (so the FA Cup shows more than QF→Final).
