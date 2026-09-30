# ROADMAP — Football Predictor & Tracker

> A work plan from 2 July to 30 September 2026. It assumes **2 sessions per week** (2–4h each).
> **Update (30 Sep 2026):** the September goal — a working, publicly deployed app with the
> predictor — was met. Phases 4 (simulator) and 5 (ML) continue into October on the live
> project, per the "ship early, improve in public" decision taken in Session 17.
> Statuses: `[ ]` to do · `[~]` in progress · `[x]` done.
> After every session we update the statuses here and write a log in `instructions/sessions/`.

---

## Milestones

| Date    | Milestone                                                   | Status |
|---------|-------------------------------------------------------------|--------|
| 6 Jul   | Repo on GitHub, secrets in `.env`, backend tidied up        | [x]    |
| 20 Jul  | **Phase 1 backend**: league tables + cups in the DB and API | [x]    |
| 10 Aug  | **Phase 1 complete**: the tables and brackets UI works      | [x]    |
| 24 Aug  | **Phase 2**: team search + match view (no favourites — a narrowed MVP) | [x] |
| 7 Sep   | **Phase 3 complete**: the predictor (Poisson model)         | [x]    |
| 28–30 Sep | **Public deployment**: live demo + professional README     | [x]    |
| Oct     | **Phase 4 complete**: match and league simulator            | [ ]    |
| Oct     | **Phase 5 complete**: ML model + comparison against Poisson | [ ]    |
| Oct     | CI (GitHub Actions) + final polish                          | [ ]    |

---

## BLOCK 0 — Foundations and housekeeping (week 1: 2–6 Jul)

### Session 1 — 2 Jul [x] Audit, security, plan, GitHub
- [x] Project analysis and stack review
- [x] Secrets (API key, DB password) moved into `.env` + `.env.example`
- [x] `.gitignore` (venv, `__pycache__`, `.env`, node_modules)
- [x] `requirements.txt` (frozen package versions)
- [x] ROADMAP + the session-log system + `CLAUDE.md`
- [x] First commit on the `main` branch
- [x] **Homework:** create the `football-predictor` repo on GitHub and push (commands in `sessions/session-01.md`)

**Concepts covered:** git (staging, commit, branch, remote, push), what `.env` and `.gitignore` are for, what `requirements.txt` is.

### Session 2 — 5 Jul [x] Backend structured like a real project
- [x] Restructuring: a single `main.py` → the `app/` package (`app/main.py`, `app/database.py`, `app/models.py`, `app/schemas.py`, `app/config.py`) — `app/routers/` postponed until there are more endpoints
- [x] `pydantic-settings` — configuration from `.env` in one place (the `Settings` class)
- [x] Pydantic schemas (`response_model`) — control over what the API returns (`LeagueResponse` on `/my-leagues`)
- [x] A tour of Swagger UI (`/docs`) — why FastAPI generates documentation for free
- [x] Ruff — Python linter/formatter + first run (code clean; comments switched to English)

**Concepts covered:** how a production FastAPI project is organised, what Pydantic and validation are, what REST is, code linting.

---

## BLOCK 1 — Phase 1 backend: league and cup data (weeks 2–3: 7–20 Jul)

### Session 3 — 8 Jul [x] Data models + Alembic migrations + target competitions
- [x] **KEY:** test the API-Football free plan — already settled in Session 1: standings only for seasons 2022–2024 (details under "Risks")
- [x] Decision: the live data source is postponed to the start of Phase 2 (owner's decision of 2 Jul — described under "Risks"); Phases 1/3/4 run on API-Football, season 2024/25
- [x] Models: `Team`, `Standing` (+ `ForeignKey` to `League`, `UniqueConstraint`, `relationship`)
- [x] **Alembic** — init + configuration (URL from `.env` through `Settings`) + TWO migrations (`leagues`, `teams`+`standings`); `create_all` removed from `main.py`
- [x] Test data cleaned up (46 UK leagues) — the database now holds the 13 target competitions (6 leagues + 6 cups + Champions League), imported through `POST /import-leagues` with the `TARGET_LEAGUE_IDS` filter (1 API request)

**Concepts covered:** relationships in databases (foreign keys), schema migrations (why `create_all` is not enough), reading API documentation.

### Session 4 — 9 Jul [x] League table import (ETL)
- [x] Standings imported for the 6 leagues (Premier League, La Liga, Serie A, Bundesliga, Ligue 1, Primeira Liga) — `POST /import-standings`, season 2024/25; 114 teams + 114 table rows, champions verified
- [x] Rate-limit strategy: max 100 requests/day → we keep the data ourselves; refreshing = a deliberate `POST /import-standings` call (6 requests); HTTP error handling (`raise_for_status`, timeout, an error inside a 200 OK body, an empty response → `HTTPException` 502/404)
- [x] Upsert (update existing rows instead of creating duplicates) — done in the application through the ORM, idempotency tested (second run: 0 inserts)

**Concepts covered:** the ETL pattern, working with an external API's limits, upserts, HTTP error handling.

### Session 5 — 3 Aug [x] Public endpoints + first tests
- [x] Pydantic schemas `TeamResponse`/`StandingResponse` (`StandingResponse` with a nested team)
- [x] `GET /leagues` (renamed from `/my-leagues`), `GET /leagues/{id}/standings` (path param, season, sorted by `rank`, `joinedload` against N+1)
- [x] **pytest** + `TestClient` — 4 API tests (root, `/leagues`, standings, wrong id → 404), all green
- [x] Test structure: the `tests/` folder (`pytest` installed, `requirements.txt` frozen)
- [~] `app/routers/` — considered, POSTPONED to Session 6 (`main.py` is still readable)

**Concepts covered:** writing automated tests, why a test suite is what makes later refactoring safe.

### Session 6 — 5 Aug [x] Cups and brackets
- [x] The `Fixture` model (a match: home/away teams, score, date, round, status) — two FKs into `teams` + `foreign_keys=`
- [x] Cup fixtures imported: 6 domestic cups + the Champions League (`POST /import-fixtures`, 1733 matches, season 2024)
- [x] Endpoints `GET /leagues/{id}/fixtures` (flat list) and `GET /leagues/{id}/bracket` (grouped by round, sorted by date)
- [x] Alembic migration no. 3 (`create fixtures table`)
- [x] Routers (`app/routers/`) + tests — **DONE in Session 7** (log `sessions/session-07.md`): `competitions.py` + `imports.py`, the `query_fixtures` helper, `get_db` → `database.py`, 6 pytest tests on an isolated database

**Concepts covered:** modelling more complex data (two FKs into one table), grouping/transforming data for the UI, ETL resilience to data gaps.

---

## BLOCK 2 — Frontend from scratch + the Phase 1 UI (weeks 4–6: 21 Jul – 10 Aug)

> **Progress (5 Aug):** the Phase 1 backend was finished off with an extra housekeeping session — routers + pytest tests (log `sessions/session-07.md`). The session numbers below are **phases**; on the calendar they run one later (a housekeeping session was inserted). We do not renumber — the plan serves us (risk #4).
>
> **Progress (10 Aug):** "Frontend kick-off" done (calendar Session 8, log `sessions/session-08.md`) — Vite + React + TS, the first `LeagueCard` component, CORS; the `bracket` debt repaid (the `knockout_only` filter). The "tables and brackets UI works" milestone slips (the frontend has only just started) — in line with risk #4.
>
> **Progress (17 Aug):** "React + Tailwind basics + the first table" done (calendar Session 9, log `sessions/session-09.md`) — `useState`/`useEffect`, `LeagueTable` with fetching + TS types, loading/error states, Tailwind v4, split into files + prettier, team crests. The league table works (PL 2024/25). Next: routing and navigation across the 6 leagues.
>
> **Progress (17 Aug, Session 10):** "Routing and navigation" done (calendar Session 10, log `sessions/session-10.md`) — React Router v7, the `Home`/`League` pages, `useParams` (one `LeagueTable` for all 6 leagues), `Link` + a layout with a header, the API base URL in `.env` (`import.meta.env`). Navigation across the 6 leagues works (clickable cards ⇄ league table). Next: TanStack Query (proper data fetching).
>
> **Progress (18 Aug, Session 11):** "Proper data fetching" done (calendar Session 11, log `sessions/session-11.md`) — TanStack Query (`QueryClientProvider`, `useQuery`: cache/`isLoading`/`isError`), the `src/api/standings.ts` API layer (`getStandings` + types), `LeagueTable` refactored (manual `useState`+`useEffect` → a single `useQuery`, ~20 lines fewer). Plus polish: league cards (a responsive grid + hover) and the header. A new UX vision noted — see "Target UX vision". Next: cup brackets (UI).
>
> **Progress (19 Aug, Session 12):** "Cup brackets (UI)" done (log `sessions/session-12.md`) — the whole bracket path (`api/bracket.ts` + `useQuery` + `Bracket` + `BracketPage`, the `/bracket/:id` route), rebuilt into a **tournament tree** (the stepped layout through `items-stretch`+`justify-around`, grouping two-legged ties, `1/2/Σ` headers + the aggregate, narrower width). Backend: the **Europa League + Conference League** imported (13→15 competitions) + a latent import bug fixed (`seen_team_ids` per import). **Navigation**: HomePage as a country accordion (`<details>`) + the European cups — all of Phase 1 is clickable. Next: a league-phase table (CL/EL/Conference) / Phase 1 polish.
>
> **Progress (20 Aug, Session 13):** "Season selector (tables)" + dates/times in the bracket done
> (log `sessions/session-13.md`). Backend: the `GET /leagues/{id}/seasons` endpoint (`DISTINCT`) +
> standings for **2022/2023** imported on the free plan. Frontend: `getStandings`+`season` / the new
> `getSeasons`, **`season` in the `queryKey`**, a controlled `<select>` in `LeaguePage` (useState = the
> UI choice, useQuery = the season list). **Phase 2 data-source decision: moving to API-Football
> premium** (ids consistent with our database + the current season + cups; risk #1 closed). Next: a
> selector for brackets + the real start of Phase 2 once premium is in place.
>
> **Progress (31 Aug, Session 14):** "Season selector (brackets)" done (log `session-14.md`).
> Backend: `GET /leagues/{id}/seasons` reworked onto a **`UNION`** — one endpoint for leagues
> (from `standings`) and cups (from `fixtures`). Frontend: the whole season path in the bracket
> (`getBracket(season)` → `Bracket` with `season` in the `queryKey` → a `<select>` on
> `BracketPage`, the same `getSeasons` as `LeaguePage`). **API-Football premium (the Pro plan)
> activated and verified** (7500 requests/day, access up to the live 2026/27 season); standings +
> fixtures imported for **2025 and 2026** — the live season is now in the database (teams 1959,
> standings 572, fixtures 5893). Risk #1 closed in practice. Next: the `/seasons` test debt
> + **the real start of Phase 2** (team results/schedule + search) on live data.

### Session 7 — [x] Frontend kick-off — DONE on the calendar in Session 8 (log `sessions/session-08.md`)
- [x] Node.js in WSL (through `nvm`, v20.20.2 LTS), npm 10.8.2; the JS ecosystem taught by analogy with Python
- [x] `npm create vite@latest frontend -- --template react-ts` → React 19 + TypeScript + Vite 8 + oxlint; a tour of the files
- [x] Dev server started (`npm run dev`, :5173, HMR), the first hand-written component `LeagueCard` (props + reused 5×)
- [x] **CORS** in FastAPI (`CORSMiddleware`, origin 5173) — verified with curl (preflight + an allowed and a foreign origin)
- [x] (debt from S6/7) the `knockout_only` filter in `GET /leagues/{id}/bracket` + the `KNOCKOUT_ROUNDS` constant + 2 tests

**Concepts covered:** the JS ecosystem (node/npm/Vite), what an SPA is, how the frontend talks to the backend, CORS.

### Session 8 — [x] React + Tailwind basics + the first table — DONE on the calendar in Session 9 (log `sessions/session-09.md`)
- [x] React foundations: components, props, `useState`, `useEffect`
- [x] Tailwind CSS — installation (v4, the `@tailwindcss/vite` plugin) and the utility-first philosophy
- [x] The `LeagueTable` component: fetching `GET /leagues/{id}/standings` + TS types for the API response
- [x] (extra) loading/error states (`res.ok`), split into `src/components/` + prettier, team crests

**Concepts covered:** the core of React, typing API responses in TypeScript, Tailwind.

### Session 9 — [x] Routing and navigation — DONE on the calendar in Session 10 (log `sessions/session-10.md`)
- [x] React Router (v7): a home page (the list of 6 leagues), `/leagues/:id`, a layout with a header
- [x] Navigation: clickable league cards (`<Link>`) + the header as a way back to `/` *(league logos — optional, later)*
- [x] (extra) `useParams` — one `LeagueTable` for every league; the API base URL in `.env` (`src/api/config.ts`)

**Concepts covered:** routing in an SPA, URL parameters, layout composition.

### Session 10 — [x] Proper data fetching — DONE on the calendar in Session 11 (log `sessions/session-11.md`)
- [x] **TanStack Query**: `QueryClientProvider` + `useQuery` (cache, `isLoading`/`isError`, background refetch)
- [x] `LeagueTable` refactored: manual `useState`+`useEffect`+`try/catch` → a single `useQuery`
- [x] A shared API client (`frontend/src/api/standings.ts` — `getStandings` + the `Team`/`Standing` types)
- [x] (extra) Phase 1 polish: league cards (a responsive `grid` + `hover`/shadow) and the header (`border-b`, hover)

**Concepts covered:** professional data-fetching patterns (the same thing companies do).

### Session 11 — [x] Cup brackets (UI) — DONE on the calendar in Session 12 (log `sessions/session-12.md`)
- [x] The `Bracket` component — rounds as columns, rebuilt into a **tournament tree** (stepped layout + two-legged ties + aggregates)
- [x] Pages for the domestic cups + the Champions League (the `/bracket/:id` route, `BracketPage`)
- [x] (extra) the **Europa League + Conference League** imported (+ an import bug fix); **navigation** — a country accordion on HomePage

**Concepts covered:** building a custom, complex UI component.

### Session 12 — [ ] Phase 1 polish ✦ MILESTONE (10 Aug)
- [ ] Responsiveness (mobile), error states, loading skeletons
- [ ] A review of the whole thing, housekeeping, README update

---

## BLOCK 3 — Phase 2: favourite teams (weeks 7–8: 11–24 Aug)
> The 2026/27 season is just starting — live data is arriving!
>
> **Progress (1 Sep, Session 15):** "Backend: team results and schedule" **done**
> (log `session-15.md`) — on live 2026 data. **League** fixtures imported (extending
> `import-fixtures` to leagues through `TARGET_LEAGUE_IDS`; +2087 fixtures, the fixtures
> table going 5893→7980). A new router `app/routers/teams.py` with three endpoints:
> `GET /teams/{id}/past-matches` (played, `or_`+`FINISHED_STATUSES`+`desc`),
> `GET /teams/{id}/future-matches` (scheduled, `NS`+`asc`), `GET /teams?search=`
> (`ilike`). The `/seasons` test debt from S14 was cleared too (pytest 8/8). Next:
> the Phase 2 frontend (search + favourites in `localStorage`) + tests for the new endpoints.
>
> **Progress (4 Sep, Session 16):** "Phase 2 frontend" **done** (log `session-16.md`), but in a
> **narrowed scope**: "favourites" were dropped (`localStorage`, `useFavorites`, the
> dashboard). The feature is **team search + a view of their matches**.
> Done: tests for 3 endpoints (pytest 8→12), `api/teams.ts`, the `useDebounce` hook,
> `SearchPage` (debounce + `useQuery`), `TeamPage` (two columns past/future + `MatchupCard`
> reused), clickable results (`Link`) + an entry point on HomePage. Bonus: **a forced dark
> theme** for everyone. Next: the Phase 2 close-out (dark polish + default season) → Phase 3.
>
> **Progress (12 Sep, Session 17):** the Phase 2 close-out **finished** + **Phase 3 STARTED
> — the Poisson backend is COMPLETE** (log `session-17.md`). Phase 2: dark polish
> (`LeagueTable`, `MatchupCard` hover), the shared `useSeasonSelector` hook (default season =
> newest, the derived-state pattern), empty states (`Bracket`, `SearchPage`).
> Phase 3: the whole Poisson theory + `app/prediction/poisson.py` (pure maths) +
> `strength.py` (λ from `standings`) + the `GET /predict` endpoint + tests (pytest 12→19).
> **Decisions**: a plan of **3 models** (baseline Poisson → improved Dixon-Coles → ML), the
> **standings** data source, a **within-league** predictor, `GET` instead of `POST`. **A NEW
> GOAL/schedule**: a beta with the predictor by 13 Sep (UI), **a public deployment + README
> + CV after the trip, ~26 Sep** — the MVP-to-deployment priority comes BEFORE Phases 4/5
> ("ship early, improve in public"). Next (S18): **the predictor UI** (a sprint).

### Session 13 — [x] Backend: team results and schedule — DONE in Session 15 (log `sessions/session-15.md`)
- [x] League fixtures imported (past + future rounds) — `POST /import-fixtures` extended (leagues + cups + European)
- [x] `GET /teams/{id}/past-matches?last=5`, `GET /teams/{id}/future-matches?next=5` (renamed from `results`/`fixtures` — avoiding a collision with `get_league_fixtures`)
- [x] `GET /teams?search=...` (search, `ilike` — contains the phrase, case-insensitive)

**Concepts covered:** query parameters, filtering and sorting in SQLAlchemy, indexes.

### Session 14 — [x] Frontend: search + match view — DONE in Session 16 (log `session-16.md`)
> **Scope narrowed (S16):** no "favourites" (`localStorage`/`useFavorites`/dashboard) —
> a deliberate scope decision. The feature = team search + a view of their matches.
- [x] Team search (`SearchPage`: a controlled input + **debounce** + `useQuery`)
- [x] A clickable result → the team page `/teams/:id` (`TeamPage`: past/future in two columns)
- [~] ~~Favourites + `localStorage`~~ — **cut from scope** (replaced by the "Find team" entry on HomePage)

**Concepts covered:** controlled forms, a custom hook (`useDebounce`), debouncing, `Link`, component reuse.

### Session 15 — [~] "My teams" ✦ MILESTONE (24 Aug) — REPLACED by the team view (S16)
> The favourites dashboard was **cut** (there are no "favourites"). `TeamPage` plays its role: after
> searching for a team you see its latest results + upcoming matches. The core of Phase 2 is ready;
> the **close-out** (dark polish of the components + default season = newest) happened in Session 17.
- [x] The view: a team's latest results + upcoming matches (`TeamPage`)
- [x] Close-out (S17): dark polish of the components + the UX debt (default season `seasons[0]`, the `useSeasonSelector` hook) + empty states (`Bracket`, `SearchPage`)

---

## BLOCK 4 — Phase 3: the predictor (weeks 9–10: 25 Aug – 7 Sep)

> **Progress (13 Sep, Session 18):** Phase 3 is **COMPLETE** — the predictor UI is ready
> (log `session-18.md`). The whole path: `api/predictions.ts` (`getPrediction`) →
> `PredictPage` (pick a league → 2 teams, `useQuery`+`enabled`) → `PredictionResult`
> (1/X/2 bars + top scores). The predictor is **within-league** and runs live locally.
> **Decisions**: the prediction season is a constant (the last **full** season — the current
> one in September is too thin, ~5 rounds → noisy strengths), no season selector.
> **A model #2 (Dixon-Coles) feature**: blending several seasons (a weighted average of the
> last and the current one = time weights) — an idea worth doing, parked behind the baseline
> ("baseline first, then MEASURED improvements").
> **New priority (S17)**: next (S19, after the trip ~26 Sep) = **a public deployment
> + README (CV) BEFORE Phases 4/5** — "ship early, improve in public".

### Session 16 — [x] The Poisson model (the heart of the project!) — DONE in Session 17 (log `sessions/session-17.md`)
- [x] Theory (step by step): attack/defence strength (relative to the league baseline) → λ → the Poisson distribution → the matrix (np.outer) → the triangles = P(1/X/2)
- [x] Implemented in plain Python/numpy: `app/prediction/poisson.py` (the maths) + `strength.py` (λ from `standings`, independent of the API)
- [x] (beyond plan) **3 models planned**: #1 baseline Poisson (this one) → #2 improved (Dixon-Coles) → #3 ML; a **within-league** predictor

**Concepts covered:** how a real statistical bookmaker model works, numpy, separating business logic from the API layer.

### Session 17 — [x] The prediction endpoint + tests — DONE in Session 17 (log `sessions/session-17.md`)
- [x] `GET /predict` (two teams within one league) → { P(1), P(X), P(2), top 5 scores } — GET, not POST (a pure read/computation)
- [x] Tests: `tests/test_poisson.py` (5, known values: λ 1.96/0.95 → 61/21/18) + 2 tests for `/predict` (pytest 12→19)

### Session 18 — [x] The predictor UI ✦ MILESTONE (7 Sep) — DONE on 13 Sep (log `sessions/session-18.md`)
- [x] Pick a league → 2 teams from it (controlled `<select>`s, within-league; teams from `getStandings`)
- [x] Visualisation: 1/X/2 percentage bars + the most likely scores (`components/PredictionResult.tsx`, `OutcomeBar`)
- [x] (extra) the `api/predictions.ts` API layer (`getPrediction`), the `/predict` route + an entry from HomePage; the season as a constant (the last full season), no selector

### Session 19 — [x] Deployment + README (the CV sprint) ✦ MILESTONE — DONE 28–30 Sep (log `sessions/session-19.md`)
> This session took the Session 19 slot ahead of Phase 4, per the priority set in S17
> ("ship early, improve in public"). Monte Carlo therefore moves to Session 20+.
>
> **The project is live:** frontend https://football-predictor-adimilo190.vercel.app,
> API https://football-predictor-ac40.onrender.com (+ `/docs`).
- [x] Backend prepared for production: CORS origins from an env variable, the `POST /import-*` endpoints guarded by an `X-Import-Token` secret (`app/security.py`), a `Procfile` (`alembic upgrade head` + uvicorn on `$PORT`), `.python-version`, a `postgres://` → `postgresql://` validator, `pool_pre_ping`/`pool_recycle` against a database that suspends when idle
- [x] Documentation pass for external readers: a header comment in every source file, comments on the non-obvious decisions, English everywhere (code, `.gitignore`, `.env.example`, `CLAUDE.md`, the project docs in `instructions/`), the dead `App.css` removed
- [x] Backend deployed on **Render** (Frankfurt, free plan) + PostgreSQL on **Neon** (Frankfurt) — chosen over Render's own free Postgres, which is deleted 30 days after creation; Alembic created the schema on the first deploy
- [x] Data moved to production with `pg_dump --data-only` in two passes (parents before children, because of the foreign keys) instead of re-importing through the API
- [x] Frontend deployed on **Vercel** (`Root Directory = frontend`), `VITE_API_URL` pointed at the backend, the Vercel domain added to `ALLOWED_ORIGINS`; two externally-visible bugs fixed: Vercel Authentication (every path redirected to a login screen) and 404s on deep links (SPA rewrite in `frontend/vercel.json`)
- [x] **UptimeRobot** pinging `/` every 5 minutes, so the free instance never sleeps (and it emails when the demo goes down)
- [x] Production data refreshed on the last day of the API-Football subscription (+233 matches, 3145 updated)
- [x] A professional README (demo links, feature list, how the Poisson model works, known limitations, architecture diagram, stack rationale, endpoint table, local setup)

**Concepts covered:** what deployment actually involves (a process vs static files vs a database), configuration through environment variables, protecting admin endpoints, production migrations, moving data between databases with `pg_dump`, and why testing from the outside catches what testing in your own browser cannot.

---

## BLOCK 5 — Phase 4: the simulator (week 11: 8–14 Sep)

### Session 20 — [ ] Monte Carlo
- [ ] Simulating a match = drawing a result from the Poisson distributions
- [ ] Simulating a league: the remaining matches × 1000 iterations from the current table → each team's chance of the title / top 4 / relegation

**Concepts covered:** the Monte Carlo method, thinking about performance (numpy vectorisation).

### Session 21 — [ ] The simulator UI ✦ MILESTONE
- [ ] A "Simulate the season" button + a colour-coded probability table
- [ ] (optional) simulating a cup bracket

---

## BLOCK 6 — Phase 5: Machine Learning (weeks 12–13: 15–28 Sep)

### Session 22 — [ ] Dataset and feature engineering
- [ ] Historical data: **football-data.co.uk** (free CSVs, many seasons back, no limits — ideal for training)
- [ ] pandas: loading, cleaning, features (form over the last 5 matches, goal averages, home/away, H2H)
- [ ] Train/test split (chronological — not random!)

**Concepts covered:** pandas, feature engineering, why time-series data is split chronologically.

### Session 23 — [ ] Training and evaluating models
- [ ] scikit-learn: logistic regression + Random Forest
- [ ] Metrics: accuracy, log-loss, confusion matrix
- [ ] **Comparison: the ML model vs Poisson vs "always pick the home team"** (the baseline)

**Concepts covered:** the full ML cycle: data → training → evaluation → conclusions; why a baseline matters.

### Session 24 — [ ] Integrating ML into the app
- [ ] Saving the trained model (`joblib`), `POST /predict-ml`
- [ ] UI: both models' predictions side by side

### Session 25 — [ ] THE FINISH ✦ project ready for the CV (by 30 Sep)
- [ ] A professional README: description, screenshots, an architecture diagram, setup instructions, the conclusions of the model comparison
- [ ] GitHub Actions: CI running ruff + pytest on every push
- [ ] Final code housekeeping

---

## Stretch goals (if there is time / October)
- User accounts (JWT) instead of localStorage
- Docker + docker-compose (backend + frontend + Postgres with one command)
- Deeper ML analytics (xG, probability calibration)

---

## Target UX vision (ideas to be scheduled into sessions)

> Noted in Session 11 (2026-08-18). The target shape of the navigation and features;
> delivery spread across the coming sessions. It replaces the current "flat" list of 6
> leagues on HomePage.

**HomePage — navigation by country (an expandable list):**
- A list of **countries** (England, Spain, Italy, Germany, France, Portugal) and next to them —
  at the same level — the **European cups** as separate entries: Champions League,
  Europa League, Conference League (they are supranational, so they do not "sit" under any country).
- Clicking a country **expands** (accordion) the competitions belonging to it: the **league** + the **domestic cup**.
- Clicking a specific competition → its **table** (league) or **bracket** (cup).
- A separate **predictors tab** on HomePage — *a later stage* (only once the model exists, Phase 3+).

**Competition page — choosing a season:**
- On the table/bracket view, a **year selector** over the available seasons, to browse different editions.

**⚠️ Implications to consider when planning (not blockers, but they need handling):**
- *Choosing a year* requires multi-season data. API-Football (free) gives **2022/23–2024/25** —
  importing further seasons = extra requests (the 100/day limit) + rows in the database. To be planned.
- *European cups:* the database currently holds only the **Champions League**; the **Europa League** and
  **Conference League** are new competitions to import (`TARGET_LEAGUE_IDS` + `POST /import-fixtures`).
- *The accordion + year selector* are new UI components — they fit naturally into Block 2 (Phase 1 polish)
  and Phase 2; we will map them onto specific sessions at the next end-of-session ritual.

---

## Risks and contingency plans

1. **API-Football limits — VERIFIED 2026-07-02 (tested with our own key).**
   - Plan: **Free**, active until 2027-03, **100 requests/day**.
   - **Season access: ONLY 2022/23, 2023/24, 2024/25.** No access to 2025/26 (finished) or 2026/27 (upcoming). The newest available = **2024/25**.
   - **Decision:** Phases 1, 3 and 4 are built on season **2024/25** (complete, real data — perfectly fine for a portfolio). Phase 5 (ML) is independent — data from football-data.co.uk CSVs.
   - **Phase 2 (favourites: upcoming matches)** is the only phase that needs live data. The source decision is taken when it starts (~24 Aug, once the 2026/27 season is under way).
   - **Requirement (settled 2026-07-02):** the app needs **the current season AND history from several previous ones**. The "demo on 2024/25 only" option is OUT. Two complete routes to choose from:
     - **A) A free hybrid:** [football-data.co.uk](https://www.football-data.co.uk) (CSVs: 20+ seasons of history + the current season, results → we compute the tables ourselves) + [football-data.org](https://www.football-data.org) (free API: schedule + live tables for the 6 leagues + CL). Zero cost, more work, no domestic cups. **← the recommendation for a CV.**
     - **B) API-Football premium:** one source, everything (current + history + cups + logos), ~19 €/month.
     - Choice: **deferred** (Session 3 / the start of Phase 2).
   - **UPDATE (Session 14, 31 Aug):** option **B** chosen — the **Pro plan** is running (7500 requests/day, seasons up to the live 2026/27, valid until 2026-10-01). Risk closed.
2. **The football calendar:** July is the gap between seasons — we build on the finished 2025/26 season, and live data arrives naturally in August (the 2026/27 kick-off) — just in time for Phase 2.
3. **Holidays / less time:** a buffer in week 8 and at the end; if we slip, we cut cup simulation (S20) and some UI polish — we never cut tests or the README.
4. **Sessions that swell:** if a session does not fit in 2–4h, the leftovers move to the next one and the ROADMAP is updated — the plan serves us, not the other way round.
