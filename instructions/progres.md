# Completed Work and Current State of the Project

## Architecture and environment
* [x] Project initialised, `football-predictor` folder created.
* [x] Python virtual environment (`venv`) created and activated.
* [x] PostgreSQL migrated and configured from Windows into the WSL (Linux VM)
  environment, to get rid of network errors ("Connection refused", "Timeout").
* [x] Database browsing set up directly in VS Code through the SQLTools extension
  (working around pgAdmin4 problems at the Windows-WSL boundary).

## Backend (FastAPI + database)
* [x] Core packages installed: `fastapi`, `uvicorn`, `httpx`, `sqlalchemy`,
  `psycopg2-binary`.
* [x] PostgreSQL connection configured (`database.py` using `sessionmaker` and
  `create_engine`).
* [x] First SQLAlchemy model created (`models.py` -> class `League` holding id, name,
  country, logo_url).
* [x] Missing tables created automatically on server start
  (`models.Base.metadata.create_all`).

## API-Football integration (ETL)
* [x] Authentication against the external API configured (headers, API key).
* [x] Import endpoint created (`/import-leagues`):
  * asynchronous request to API-Football for the league list;
  * processing of the returned JSON;
  * duplicate check (by ID against our own database);
  * new records saved into PostgreSQL through a SQLAlchemy session.
* [x] Read endpoint created (`/my-leagues`):
  * queries our own PostgreSQL database and returns every stored league to the client.
* **Result:** success. Our own database is correctly populated with the first data
  (46 British leagues imported for testing purposes).

## Session 1 (2026-07-02) — Security, organisation, plan
* [x] Full project audit + stack review (verdict: the stack is a good fit, minor
  additions described in `tools.md`).
* [x] Secrets (API key, DB password) moved out of the code into `.env`
  (`python-dotenv`); template in `.env.example`.
* [x] `.gitignore` (venv, `__pycache__`, `.env`, node_modules) — repo ready to publish
  with no leaks.
* [x] `requirements.txt` — reproducible environment.
* [x] Smoke test: the app starts and connects to the database through `.env`.
* [x] `instructions/ROADMAP.md` — a plan of 24 sessions up to 30 September (milestones +
  risks).
* [x] `CLAUDE.md` — working agreement and end-of-session ritual; session logs in
  `instructions/sessions/`.
* [x] Git: `main` branch, first commit.
* [x] Pushed to GitHub — the repo existed from an earlier attempt; a new token was
  generated and the push went through.

## Session 2 (2026-07-05) — Backend structure, configuration, schemas, Ruff
* [x] Restructuring: code moved into the `app/` package (`__init__.py` + package imports
  `from app...`).
* [x] `app/config.py` — pydantic-settings (`Settings`) as the single source of
  configuration; `os.getenv`/`load_dotenv` and the dead `if not DATABASE_URL` removed.
* [x] `app/schemas.py` — `LeagueResponse` + `response_model` on `/my-leagues`; the models
  layer (database) separated from the schemas layer (API).
* [x] API address moved into configuration (`settings.API_FOOTBALL_BASE_URL`).
* [x] Ruff (lint + format) configured; the code passes with no complaints;
  `requirements.txt` updated.
* [x] Language in the code switched to English (comments/docstrings); the rule written
  down in `CLAUDE.md` and in Claude's memory.
* [x] `.claude/settings.local.json` — general permission rules (less clicking "allow");
  `tools.md` — a note about WSL/Bash.
* [x] Smoke test (`import app.main`) after every change — always OK.

## Session 3 (2026-07-08) — Alembic migrations, Team/Standing models, target competitions
* [x] Alembic: init + configuration (`env.py`: database URL from `settings`,
  `target_metadata`, models imported); the database address never lands in a file tracked
  by git.
* [x] Baseline "clean start" migration: DROP of the test `leagues` table → migration
  `create leagues table` → `upgrade head`; the database can be rebuilt from scratch with
  one command.
* [x] `create_all` removed from `main.py` — the schema is managed exclusively by Alembic.
* [x] Models `Team` (no league_id — the many-to-many link goes through standings) and
  `Standing` (FKs to leagues/teams, season, statistics,
  `UniqueConstraint(league_id, team_id, season)`); second migration applied.
* [x] `app/constants.py` — `TARGET_LEAGUE_IDS`: 13 tracked competitions (6 leagues + 6
  domestic cups + Champions League).
* [x] `/import-leagues`: `GET`→`POST` (REST), one request for the full league list plus a
  local filter (100/day limit), response listing the imported names.
* [x] Import performed: 13/13 competitions in the database, verified through `TestClient`
  and `/my-leagues`.
* [x] `FastAPI(title="Football Predictor API")`; Ruff clean; `requirements.txt` updated
  (alembic).
* [x] New rule in `CLAUDE.md`: one step of the plan at a time + ask for approval before
  the next one.
* **Result:** the data foundation is ready — a versioned schema (2 migrations), with the
  `teams`/`standings` tables waiting for the standings import in Session 4.

## Session 4 (2026-07-09) — League table import (the full ETL pipeline)
* [x] New rule in `CLAUDE.md`: after every session, homework (documentation for the next
  session) in the session log.
* [x] `app/constants.py`: competitions split into groups (`DOMESTIC_LEAGUE_IDS` /
  `DOMESTIC_CUP_IDS` / `EUROPEAN_COMPETITION_IDS`), `TARGET_LEAGUE_IDS` = merged with
  `**`; constant `DEFAULT_SEASON = 2024`.
* [x] Extract: `fetch_league_standings` — httpx with `params`/`timeout`,
  `raise_for_status`, handling of the "200 OK with an error in the body" trap and of an
  empty `response` → `HTTPException(502)`.
* [x] Transform + Load: `upsert_league_standings` — upsert of teams and table rows through
  the ORM (unit of work), 404 guard clause, no commit (the caller owns the transaction),
  counters reported back.
* [x] `POST /import-standings`: loop over the 6 leagues on a single `AsyncClient`, `season`
  query param, one commit (all-or-nothing), response with a per-league report.
* [x] Import verified (TestClient): 114 teams / 114 rows; team counts per league correct
  (20/20/20/18/18/18); 2024/25 champions correct; upsert idempotency confirmed (second
  run: 0 inserts, updates only).
* [x] Ruff clean; API usage: 8/100 requests; no new migrations (data-only changes).
* **Result:** the backend holds the complete 2024/25 tables for all 6 leagues — ready for
  public endpoints and tests (Session 5).

## Session 5 (2026-08-03) — Public read endpoints + first tests (pytest)
* [x] `app/schemas.py`: `TeamResponse` (twin of `LeagueResponse`) and `StandingResponse`
  with a **nested** `team: TeamResponse` (the `Standing.team` relationship +
  `from_attributes` → one request from the frontend instead of two).
* [x] `GET /leagues` — the old `/my-leagues` renamed to the REST convention
  (`get_leagues`); grep confirmed no dangling references in the code.
* [x] `GET /leagues/{league_id}/standings` — path param, `season` as a query param with
  `DEFAULT_SEASON`, `404` when the league is missing, sorted by `rank`,
  `response_model=list[StandingResponse]`.
* [x] `joinedload(models.Standing.team)` against N+1 — demonstrated on the live database:
  without it **21** queries (1 + 20 for teams), with it **1** (a JOIN). Endpoint verified:
  Liverpool → Arsenal → City (PL 2024/25).
* [x] `pytest 9.1.1` installed (`requirements.txt` frozen); `tests/` folder
  (`__init__.py` + `test_main.py`), 4 tests through `TestClient` (root, `/leagues`,
  standings with `rank==1` and a nested team, wrong id → 404) — 4/4 green; Ruff clean
  (`app/` + `tests/`).
* **Change of working mode:** the owner writes the code himself, Claude guides and
  reviews (it does not type the code for him); exceptions only on an explicit request.
* **Result:** the API has clean read endpoints for the frontend and a first safety net of
  tests. `app/routers/` postponed to Session 6.

## Session 6 (2026-08-05) — Cups and brackets (Fixture model, ETL, bracket endpoints)
* [x] `Fixture` model: two foreign keys into `teams` (`home_team_id`/`away_team_id`) +
  `foreign_keys=` on the relationships; `id` reused from the API; `date` as `DateTime`;
  goals nullable. Alembic migration **no. 3** (`03d5cc4db1d2`) — autogenerated, reviewed,
  applied.
* [x] Full match-import ETL: `fetch_fixtures` (Extract, generic — works for any
  competition), `upsert_team` (helper, `country=None` for cup teams), `upsert_fixtures`
  (Transform+Load: guard, team dedup, ISO date parsing, upsert by `id`),
  `POST /import-fixtures` (loop over 7 cups, one commit).
* [x] ETL resilience to data gaps (owner's decision): an empty `response` → `[]`
  (tolerate), API failures (`errors`/HTTP) still → `502`. Applied in BOTH fetches.
* [x] Import verified live: **1733 matches / 1267 teams / 7 competitions**, season 2024. A
  `duplicate key` bug (caused by `autoflush=False` plus teams playing several rounds)
  solved by in-memory deduplication.
* [x] Schemas: `FixtureResponse` (two nested teams, nullable goals), `BracketRound` (no
  `from_attributes` — built by hand); `TeamResponse.country` → `str | None`.
* [x] `GET /leagues/{id}/fixtures` (flat list, double `joinedload`, sorted by date) +
  `GET /leagues/{id}/bracket` (grouped by round, `dict` insertion order = tournament
  order). The 2024/25 Champions League bracket verified: 17 rounds in order, final PSG
  5-0 Inter.
* [x] Housekeeping: endpoint section comments (numbering → WRITE/READ groups, PL → EN).
* **Result:** Phase 1 backend **complete** — leagues and cups in the database and in the
  API. For Session 7: split `main.py` into routers (+ the `query_fixtures` helper) and
  pytest tests.

## Session 7 (2026-08-05) — Backend housekeeping: pytest tests + routers
* [x] **Test infrastructure** (`tests/conftest.py`): isolated **in-memory** SQLite
  database (`StaticPool` + `check_same_thread=False`), `get_db` swapped through
  `app.dependency_overrides`, autouse fixture `reset_database` (a clean database per
  test), fixtures `client` and `db_session`.
* [x] **6 tests** of the read endpoints (Arrange–Act–Assert, each seeding its own data):
  `/leagues`, `/standings`, `/fixtures`, `/bracket` (proving rounds are sorted by date) +
  root + 404. The `/fixtures` and `/bracket` tests were written by the owner (Claude:
  guidance + review).
* [x] **`main.py` refactored from 522 to 23 lines** into routers: `get_db` →
  `database.py` (avoiding an import cycle), `app/routers/competitions.py` (reads + the
  `query_fixtures` helper, DRY), `app/routers/imports.py` (writes + ETL). Done step by
  step with `pytest` after each step.
* [x] Verification: 6/6 tests green throughout the refactor, Ruff clean, smoke
  `import app.main` → 12 routes. Zero API-Football requests, no new migrations.
* **Result:** the Phase 1 backend is finished and tidy (routers + tests). Ready for the
  frontend to start (Session 8).

## Session 8 (2026-08-10) — Frontend kick-off (Vite + React + TS), CORS, bracket filter
* [x] **Frontend from scratch:** Node.js v20.20.2 (nvm, inside WSL) + npm 10.8.2;
  `npm create vite@latest frontend -- --template react-ts` (React 19 + Vite 8 + oxlint) +
  `npm install` (27 packages). Foundations taught by analogy Python→JS
  (node/npm/package.json/node_modules).
* [x] **First component** (written by the owner): `LeagueCard` (typed props
  `{name, country}`, destructuring, JSX) reused 5× in `App`; fragment `<>` +
  `export default`. Dev server `npm run dev` (:5173, HMR), rendering verified.
* [x] **CORS** (`CORSMiddleware` in `app/main.py`, origin `http://localhost:5173`,
  credentials): verified with curl — preflight `OPTIONS` + `GET` from an allowed and from
  a foreign origin. Lesson: CORS is browser-side protection, not server authorisation.
* [x] **Debt repaid — the `knockout_only` filter** in `GET /leagues/{id}/bracket`: opt-in
  query param (default `False`) + the `KNOCKOUT_ROUNDS` constant in `constants.py`.
  Diagnostics of the real round names (CL 17, FA Cup 20). Fixed after review: default
  `True`→`False` (backwards compatibility + opt-in semantics).
* [x] **2 bracket tests:** `test_get_bracket_all_stages` (default = everything, plus proof
  of date sorting), `test_get_bracket_with_knockout_only` (the filter). pytest **7/7**,
  Ruff (`app/` + `tests/`) clean.
* **Result:** the frontend is up (a working component + CORS ready for fetching in
  Session 9). The Phase 1 backend gained a clean knockout filter. 0 API-Football requests.

## Session 9 (2026-08-17) — Interactive React + the first table on live data
* [x] **`useState` + `useEffect`** (warm-up `Counter`): state = memory + a re-render
  trigger; effects driven by the dependency array (`[]` = once after mounting), not on
  every render. Avoided the `onClick={() => ...}` trap (a function, not a call).
* [x] **`LeagueTable` with fetch**: TS types `Team`/`Standing` mirroring `schemas.py`
  (snake_case, `string | null`, nested `team`); the async-inside-`useEffect` idiom, two
  `await`s, `.map` + `key`. `GET /leagues/39/standings` → 20 rows; **CORS worked live**.
* [x] **Loading/error states**: `try/catch/finally`, the `res.ok` trap (`fetch` does not
  throw on 404 → a manual `throw` = the frontend's `raise_for_status`), generic
  `useState<string | null>`.
* [x] **Tailwind CSS v4** (set up by Claude, method verified with WebFetch):
  `@tailwindcss/vite` + `@import "tailwindcss"` (NOT the old v3 way). Utility-first,
  `hover:`/`odd:` variants, `text-align` inheritance; table styling (by the owner).
* [x] **Housekeeping**: split into `src/components/LeagueCard.tsx` +
  `LeagueTable.tsx` (`import`/`export default`), `App.tsx` as the skeleton, `Counter`
  removed; **prettier** added (`npm run format` script, the equivalent of `ruff format`).
* [x] **Team crests**: `<img>` + conditional render `{logo_url && …}` + flex; column fix
  after review (9 cells = 9 headers).
* **Quality:** oxlint 0/0, build (tsc + vite) green, formatting clean. Backend unchanged
  (7/7 tests), 0 API-Football requests.
* **Result:** the first league table works on live data (PL 2024/25), handles errors and
  is styled. For Session 10: routing (React Router) — navigation across the 6 leagues,
  `useParams` instead of the hardcoded `39`.

## Session 10 (2026-08-17) — Routing and navigation (React Router, useParams, Link, layout, env)
* [x] **React Router v7** (`react-router-dom ^7.18.2`): `<BrowserRouter>` in `main.tsx`;
  SPA theory (URL → component with no reload, the History API).
* [x] **Pages vs components**: new `src/pages/` folder (`HomePage`, `LeaguePage`);
  `src/data/leagues.ts` (6 leagues, the first named `export`); `<Routes>`/`<Route>` in
  `App.tsx` (`/` → `HomePage`, `/leagues/:id` → `LeaguePage`).
* [x] **`useParams`**: `LeaguePage` reads `:id` (always a string; the `if (!id)` guard =
  type narrowing) and passes `leagueId` to `LeagueTable`; fetch on a template literal;
  **deps `[leagueId]`** (refetch when the league changes). One component serves all 6
  leagues (verified live: PL/La Liga/Bundesliga). Caught a quotes-instead-of-backticks
  bug (the compiler does not catch it).
* [x] **`<Link>` + layout**: clickable cards (`to={`/leagues/${id}`}`, `key` on the
  `Link`), a shared `<header>` (banner landmark) with the title linking to `/` above
  `<Routes>`; the duplicated `<h1>` removed from the pages.
* [x] **API base URL in `.env`**: `frontend/.env` + `.env.example` (`VITE_API_URL`),
  `src/api/config.ts` (`import.meta.env` + `??` fallback, a single source of truth);
  `LeagueTable` uses `API_BASE_URL`. The hardcoded `http://localhost:8000` is gone from
  the code. Lesson: `VITE_` variables are not secret.
* **Quality:** `npm run build` (tsc+vite) green, `npm run lint` (oxlint) 0/0,
  `npm run format` (prettier) clean. The backend was only started for live verification;
  **0** API-Football requests.
* **Result:** navigation across the 6 leagues works (clickable cards ⇄ league table, no
  reloads), the API URL is configured through `.env`. For Session 11: **TanStack Query** —
  proper data fetching (cache, `isLoading`/`isError`), refactoring the manual fetch and a
  shared API client.

## Session 11 (2026-08-18) — Proper data fetching (TanStack Query) + Phase 1 polish
* [x] **TanStack Query** (`@tanstack/react-query ^5.101.4`): `QueryClient` +
  `QueryClientProvider` wrapped around `<App/>` in `main.tsx` (the same way as
  `BrowserRouter`) — the cache "brain" for the whole app. Theory: server state (cache,
  deduplication, refetch) vs manual `useState`+`useEffect`.
* [x] **API layer** `src/api/standings.ts` (written together): types `Team`/`Standing`
  moved out of the component (they model server data), `getStandings(leagueId):
  Promise<Standing[]>` — `fetch` + `if (!res.ok) throw` (the bridge to `isError`, since
  `fetch` does not throw on 4xx/5xx) + `return res.json()`. No `useState`/`try/catch`.
* [x] **`LeagueTable` refactored onto `useQuery`** (the core, by the owner):
  `queryKey: ["standings", leagueId]` (cache per league, replacing the `[leagueId]` deps),
  `queryFn: () => getStandings(leagueId)` (an arrow function — not an immediate call);
  3× `useState` + `useEffect` + `try/catch` → a single `useQuery`. Guard
  `if (!data) return null` (narrowing `Standing[] | undefined`); the type of `data` is
  **inferred** from `getStandings` (no `Standing` import).
* [x] **Phase 1 polish** (Tailwind, `LeagueCard`/`HomePage`/`App`): league cards —
  `border`, `rounded-lg`, `p-4`, `shadow-sm`+`hover:shadow-md`, `transition`,
  `cursor-pointer`; grid `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4` (the first
  **responsive prefixes**, mobile-first); header `border-b` + `hover:opacity-80`. The dead
  `league-card` class removed. Discovery: **Tailwind preflight** resets the default styles
  of `<a>` and headings.
* [x] **New UX vision** noted in the ROADMAP: HomePage as an expandable list of countries
  plus the European cups (CL/EL/Conference), accordion → league/domestic cup, click →
  table/bracket, a year selector, a predictor tab (later stage).
* **Quality:** `npm run build` (tsc+vite) green, oxlint 0/0, prettier clean. Backend
  unchanged, **0** API-Football requests. A practical lesson: a file written "from
  underneath" (by a tool) vs an open VS Code buffer → on reload choose **Don't Save**.
* **Result:** data fetching now follows a professional pattern (cache for free) and the
  home page looks serious. For Session 12: **cup brackets (UI)** — a `Bracket` component
  (rounds as columns) + `useQuery` for `GET /leagues/{id}/bracket`; possibly starting the
  navigation rebuild along the new vision.

## Session 12 (2026-08-19) — Cup brackets (tournament tree) + navigation + EL/Conference import
* [x] **Backend — importing the Europa League (3) and Conference League (848)**:
  `constants.py` +2 ids in `EUROPEAN_COMPETITION_IDS` (thanks to the `**` merge, one edit
  propagates everywhere). Import: **13→15 competitions**, **+678 matches** (EL 269 /
  Conference 409), **+137 teams**.
* [x] **Backend — a latent import bug fixed**: `duplicate key teams_pkey` for teams playing
  in several European cups. Cause: `seen_team_ids` per competition + `autoflush=False` (a
  `pending` object is invisible to `db.query`) → a double `db.add`. Fix: **one shared
  `seen_team_ids` for the whole import** (a parameter of `upsert_fixtures`). Tests 7/7,
  Ruff clean. Lesson: "it works" ≠ "it is correct" — a hidden assumption broken by new
  data.
* [x] **Frontend — the bracket path**: `api/bracket.ts` (types `Fixture`/`BracketRound` +
  `getBracket` with `knockout_only=true`), `components/Bracket.tsx`
  (`useQuery(["bracket", id])` + guards), `pages/BracketPage.tsx` + the `/bracket/:id`
  route. Named `BracketPage` (not `CupPage`) — after the view, because some "cups" have a
  league phase. The pattern is 1:1 with standings.
* [x] **Frontend — the tournament tree**: a stepped layout (`items-stretch` +
  `justify-around` = pixel-perfect centring, no connecting lines, `overflow-x-auto`).
  `groupIntoMatchups` — grouping two-legged ties by the unordered pair of teams (mapping
  goals despite the home/away swap). `MatchupCard` — crests + per-leg scores in boxes; for
  a two-legged tie, `1/2/Σ` headers + the **aggregate**. Robust against mixed rounds (Copa
  del Rey: single matches and two-legged ties). Width narrowed 1152→910px.
* [x] **Frontend — navigation by country**: the `COUNTRIES` model (country → league + cup)
  + `EUROPEAN_COMPETITIONS` in `data/leagues.ts` (the old `LEAGUES` removed); `HomePage` as
  7 expandable sections built on the native **`<details>`** element (6 countries +
  "European Competitions"), links league→`/leagues/:id`, cup/European→`/bracket/:id`. The
  dead `LeagueCard.tsx` removed.
* [x] **Learning**: a React component is not `async` (it draws the current state,
  `useQuery` triggers the redraw); a tree through flexbox; `?? "-"` vs `|| "-"` (0 is
  valid); `key` on the element inside `.map`, wrapper outside; error vs warning; where to
  learn flexbox (Froggy/CSS-Tricks/Tailwind docs/DevTools); WSL: `npm run dev` needs an
  explicit `. ~/.nvm/nvm.sh` (the system node v12 breaks Vite).
* **Quality:** `npm run build` (tsc+vite) green, oxlint **0/0**, prettier clean; pytest
  **7/7**, Ruff clean. API-Football usage: ~19 requests (the import + a retry after the
  bug).
* **Result:** **Phase 1 is finished** — every table and bracket is reachable by clicking
  from HomePage; brackets render as tournament trees. For Session 13 (to be decided at the
  start): a league-phase table (CL/EL/Conference) / Phase 1 polish (responsiveness,
  skeletons) / bracket cosmetics.

## Session 13 (2026-08-20) — Season selector (tables) + dates in the bracket + Phase 2 data-source decision
* [x] **Direction and data source decided**: start Phase 2 (core), but first the dates in
  the bracket and the season selector. The Phase 2 blocker (the free API only serves
  2022–2024, no live season) resolved by a decision: **the owner buys API-Football
  premium** — ids consistent with our database (no mapping), cups, the current season plus
  history from one source. Risk #1 closed.
* [x] **Step 1 — dates/times in the bracket** (frontend only; the backend already sent
  `date`): `api/bracket.ts` — `date` carried through `groupIntoMatchups` into `legs` (it is
  per-match data, like goals); `components/MatchupCard.tsx` — the `formatDate` helper
  (`toLocaleString("pl-PL", {dateStyle, timeStyle: "short"})`, automatic UTC→local zone) +
  a date row `legs.map(...).join(" / ")`. Format `12.03.2025, 21:00`.
* [x] **Step 2 — backend endpoint `GET /leagues/{id}/seasons`** (written by the owner):
  `query(Standing.season).filter(league_id).distinct().order_by(desc())`, unwrapping the
  tuples in a loop (`row[0]`), `response_model=list[int]`. It asks the database for the
  truth instead of hardcoding a list.
* [x] **Step 2 — data**: standings for **2022 and 2023** imported through the existing
  `POST /import-standings?season=` (the endpoint was already parameterised — zero new
  code). `seasons` returns `[2024, 2023, 2022]`. ~12 API requests.
* [x] **Step 2 — frontend**: `api/standings.ts` — `getStandings(leagueId, season)`
  (+`?season=`) and the new `getSeasons(): number[]`; `LeagueTable` — a `season` prop +
  **`season` in the `queryKey`** (a separate cache per season); `LeaguePage` — `useState`
  for the chosen season (UI state) + `useQuery(getSeasons)` (server data) + a controlled
  `<select>` (`Number(e.target.value)`), the rules of hooks (guard below the hooks),
  `enabled: !!id`.
* [x] **Selector fix**: position (the native `<select>` popup covered the table → `flex
  justify-end`, then the owner moved it left); **review bug**: `justify-begin` does not
  exist in Tailwind (it worked by accident — flex defaults to start) → `justify-start`.
* **Learning**: front↔backend communicate only through the URL (a function parameter is
  not server data); path param (by position) vs query param (by name); a parameter with a
  default is optional, without one it is required; a single-column query returns a list of
  **tuples** `(2024,)`, `DISTINCT`; **server state (useQuery) vs UI state (useState)** —
  the Session 11 refactor only concerned server data; the `queryKey` must include
  `season`; the rules of hooks; `toLocaleString` and automatic time zones.
* **Quality**: build green, oxlint 0/0, prettier clean; Ruff clean, pytest **7/7** (debt:
  no test for `seasons`). ~12 API-Football requests.
* **Result**: league tables are **multi-season** (2022–2024, switched with the selector)
  and brackets show match dates. For Session 14: a selector for brackets + (after
  premium) Phase 2 proper (team results/schedule).

## Session 14 (2026-08-31) — Season selector (brackets) on `UNION` + premium Pro + 2025/2026 import
* [x] **Decisions**: premium bought (**Pro plan**); start with the bracket selector (Phase
  2 moves to S15). Architecture of the season list — **option B (`UNION`)** instead of a
  separate endpoint (DRY; the frontend keeps a single `getSeasons`).
* [x] **Step 1 — backend `/leagues/{id}/seasons` on `UNION`** (written by the owner): the
  problem — cups have no rows in `standings`, so the old endpoint returned `[]` for
  brackets. Solution: two sub-queries (`Standing.season` + `Fixture.season`) joined with
  `.union()`, then `.all()`, unwrapping `row[0]`, `sort(reverse=True)`. Bugs from the
  review: `.all()` on the sub-queries (materialising `Query`→`list`, so `.union()` was
  missing → `AttributeError`); redundant `.distinct()/.order_by()` (UNION already
  deduplicates); `sort()`→`sort(reverse=True)`. Verified with curl: FA Cup `[2024]`, PL
  `[2024,2023,2022]`.
* [x] **Step 2 — `getBracket(leagueId, season)`** (`api/bracket.ts`): `season` as the
  second, required argument **before** the optional `knockoutOnly` (a TS rule); `&season=`
  in the URL.
* [x] **Step 3 — `Bracket`** (`components/Bracket.tsx`): a `season` prop,
  `queryKey: ["bracket", leagueId, season]` (cache per season),
  `getBracket(leagueId, season)`. The pattern is 1:1 with `LeagueTable`.
* [x] **Step 4 — the selector on `BracketPage`**: `useState` for the season +
  `useQuery(getSeasons)` (the same as `LeaguePage`) + a controlled `<select>`, guard below
  the hooks. Review bug: `useState(2026)`→`2024` (there were no 2026 fixtures then → an
  empty bracket + a controlled-select mismatch). UX debt: default should be the newest
  season from the list instead of a hardcoded value.
* [x] **Step 5 — data (premium)**: `/status` → Pro, 7500/day, valid to 2026-10-01. Access
  to seasons 2025 and 2026 verified (standings + fixtures; the free plan only gave
  2022–2024). Imported: standings 2025/2026 (2×114), fixtures 2025 (**2430** matches) +
  2026 (**1052**). Copa del Rey/Coupe de France 2026 = 0 (those cups had not started — the
  ETL tolerates it). `/seasons` verified: Copa del Rey `[2025,2024]` (no 2026 — the truth
  from our own database).
* **Learning**: `UNION` (dedup, the same column on both sides); `Query` (lazy, `.union()`)
  vs `.all()` (materialising into a `list`); the anatomy of a URL (path `/` = resource,
  query `?`/`&` = options); the order of function arguments (positional) ≠ query params in
  a URL (named); a controlled `<select>` with a value outside its options desynchronises;
  **WSL: `bash -ic` (nvm→Node v20) vs `bash -lc` (system v12, which breaks `tsc` on
  `??`)**.
* **Quality**: `npm run build` (tsc+vite) green; Ruff clean; pytest **7/7** (debt: no test
  for `seasons`). Database after the import: **leagues 15, teams 1959, standings 572,
  fixtures 5893**. API-Football (Pro): ~30 import requests plus a few diagnostic ones.
* **Result**: brackets are **multi-season** (FA Cup/CL: 2024–2026) and the database holds
  **live 2026/27 data** — the gate to Phase 2 is open. For Session 15: the `/seasons` test
  debt + the start of Phase 2 (team results/schedule + search) on live data.

## Session 15 (2026-09-01) — Phase 2 starts (backend): team matches + search
* [x] **Debt from S14 — test for `GET /leagues/{id}/seasons`** (written by the owner): an
  **airtight** scenario — a season only in `standings` (2023), only in `fixtures` (2025),
  in both (2024→dedup); each case defends a different part of the `UNION`. Review bug:
  `sorted(data) == [...]` (ascending vs a descending list — the test would have failed and
  papered over the sorting) → `assert data == [2025,2024,2023]` (content + dedup + order at
  once). pytest **7/7 → 8/8**.
* [x] **B1 — importing league fixtures** (extending `POST /import-fixtures`, option A):
  the `fetch_fixtures`/`upsert_fixtures` helpers are **generic**, so
  `competitions = TARGET_LEAGUE_IDS` (15 competitions) was enough. Renamed
  `cups_report`→`competitions_report`. An F401 after the refactor (`TARGET_LEAGUE_IDS`
  orphaned `DOMESTIC_CUP_IDS`/`EUROPEAN_COMPETITION_IDS` — removed; `DOMESTIC_LEAGUE_IDS`
  stays for `import_standings`).
* [x] **2026 import (live)**: leagues = all INSERTs (PL/La Liga/Serie A **380** each,
  Bundesliga/Ligue 1/Primeira **306** each — matching the league sizes; **2058** in total);
  cups/European = **1052 UPDATEs** (the ones from S14 → proof of idempotency, 0
  duplicates). `fixtures`: 5893 → **7980**, teams 1959 → **1962**.
* [x] **B2 — `GET /teams/{id}/past-matches`** (new router `app/routers/teams.py` + wired
  into `main.py`): the `FINISHED_STATUSES = {FT,AET,PEN}` constant; 404 guard,
  `or_(home==id, away==id)` (**our first OR**), `status.in_(...)`,
  `order_by(date.desc())`, `limit(last)`, `joinedload`. Verified live (Man City): 5× `FT`,
  descending, home and away.
* [x] **B3 — `GET /teams/{id}/future-matches`**: the twin with `status == "NS"`,
  `order_by(date.asc())`, `next: int = 5`. Verified: 5× `NS`, ascending, goals `null`;
  today's date (1 Sep) separates past (up to 28 Aug) from future (from 5 Sep).
* [x] **B4 — `GET /teams?search=...`**: `Team.name.ilike(f"%{search}%")` +
  `order_by(name)` + `limit(20)`, reusing `TeamResponse`. Verified: `?search=real`
  (matches Villarreal/Montreal — the "contains" pattern), `?search=MANCHESTER`
  (case-insensitive).
* **Decisions**: importing leagues = extending the existing endpoint (DRY, the machinery
  is generic); "played" determined by `status`, not by date; the names
  `past-matches`/`future-matches` (`fixtures` collided with `get_league_fixtures`;
  `games`→`matches`); a URL ends with a noun.
* **Learning**: what makes a test airtight; `ruff check` (F401, lint) ≠ `ruff format`
  (style); leagues and cups share the `leagues` table; `APIRouter` + `include_router`
  (not wired = 404); path/query/dependency params; `or_`/`.in_`/`.desc()`/`.asc()`/
  `.limit()`; `ilike`+`%` (a bind param, so no SQL injection); statuses `FT/AET/PEN` vs
  `NS`; `next` shadows a builtin; a function name is not the URL; a trailing `\n` (POSIX).
* **Quality**: Ruff clean, pytest **8/8**. API-Football (Pro): ~15 import requests.
* **Result**: **the Phase 2 backend is complete** — league import plus 3 team endpoints,
  verified on live 2026 data. For Session 16: tests for the new endpoints (a warm-up) +
  **the Phase 2 frontend** (search with debounce + favourites in `localStorage`, a
  `useFavorites` hook) + the UX debt (default season `seasons[0]`).

## Session 16 (2026-09-04) — Phase 2 frontend (search + match view) + dark theme
* [x] **Phase 2 scope changed**: the owner drops "favourites"
  (`localStorage`/`useFavorites`/dashboard). The feature is **team search + a view of
  their matches** (a deliberate MVP narrowing).
* [x] **Warm-up — tests for the 3 endpoints from S15** (written by the owner):
  `past-matches` (airtight scenario A/B/C/D), `future-matches` (a mirror with `NS`+`asc`;
  data consistent with the domain — `NS` has no goals), `search_teams` ("green ≠
  airtight": the phrase `eSTEr` is a substring in the middle, and assertions **by index**
  defend `ilike`/`order_by`; plus an empty result), `team_not_found` (404 on past+future).
  pytest **8 → 12**. Lessons: a seed must satisfy `NOT NULL`; `"""..."""` in the middle of
  a function is not a comment but a dead string.
* [x] **`api/teams.ts`**: `searchTeams`/`getPastMatches`/`getFutureMatches` (the
  `standings.ts` pattern, types reused through `import type`, `encodeURIComponent`).
  Decision: do NOT duplicate the default `5` on the frontend (the backend rules —
  DRY/YAGNI); `teamId: string`.
* [x] **`hooks/useDebounce.ts`** (a custom hook, new `hooks/` folder): `useState` +
  `useEffect` + `setTimeout` with a `clearTimeout` cleanup (every keystroke cancels the old
  timer → only a pause ≥ delay gets through). Verified live: "barca" (5 quick keystrokes) →
  **1 request**, not 5.
* [x] **`SearchPage.tsx`** (+ the `/teams` route): a controlled `<input>` →
  `useDebounce(300)` → `useQuery` (`queryKey` holding the phrase, `enabled: length>0`);
  states rendered through **a variable + `if`** (the input must stay on screen — no early
  return). "real" → 12 teams (substring: Montreal/Villarreal).
* [x] **`TeamPage.tsx`** (+ the `/teams/:id` route): two `useQuery` calls (guards **AFTER**
  the hooks — the rules of hooks; `if (!past||!future) return null` = **type narrowing** →
  no more `?.` in the render); the `fixtureToMatchup` adapter locally; **`MatchupCard`
  reused** (a single match = "a two-legged tie with one leg"); a header (crest + name taken
  from the first match) + **two columns** past/future (`flex gap-8`, `flex-1`). Verified:
  "real" → click Real Madrid → `/teams/541` → matches (cross-competition).
* [x] **Clickable results** (`Link to={/teams/:id}`) + a "Find team" card on HomePage. The
  full loop (search → click → see matches) verified end to end.
* [x] **Dark theme forced for everyone**: `index.css` — dark values in `:root` +
  `color-scheme: dark` + the `@media (prefers-color-scheme)` gate removed. `MatchupCard`
  lightened for dark (`bg-gray-800`/`700`). **Postponed**: dark polish for the remaining
  components (league table, hovers).
* [x] `.vscode/settings.json` (local, outside git) — format-on-save with Ruff/Prettier per
  language.
* **Learning (React from the ground up, a lot of it)**: hooks (definition + rules + custom
  hooks); `useEffect` (a callback after the render + cleanup + the dependency array);
  `() =>` as a callback; `setTimeout`; `A && B` / ternary / `if` + a variable in JSX;
  `??`/`?.` vs an explicit `if`; `let` vs `const`; **a render is a snapshot** (new `const`s
  every render, memory lives in `useState`); **`import type` vs a value import** (types are
  erased in JS → a runtime "does not provide an export"); **type narrowing**
  `if(!x)return`; **Tailwind v4 CSS layers** (non-layered CSS beats utilities → the global
  `h1` from the `index.css` template was overriding `mb-4`/`text-2xl`); **flexbox's two
  axes** (`items-*` = vertical, `justify-*` = horizontal); `text-*` is overloaded (size vs
  colour); prettier will NOT format code with a syntax error; WSL/Vite — the watcher is
  blind to writes coming from Windows (restart the dev server).
* **Quality**: pytest **12/12** + Ruff clean; frontend `tsc` + oxlint **0/0** + prettier
  clean. Database unchanged (leagues 15, teams 1962, standings 572, fixtures 7980).
  API-Football: only verification reads (uvicorn running locally).
* **Result**: **the core of Phase 2 is ready** — search + a match view, clickable, reachable
  from HomePage, on a dark theme. For Session 17: a short **Phase 2 close-out** (dark polish
  + default season = newest) → **START of Phase 3 (the Poisson model)**.

## Session 17 (2026-09-12) — Phase 2 close-out + Phase 3 backend (the Poisson model)
* [x] **Phase 2 close-out**: dark polish for `LeagueTable` (header/hover/borders — fixed
  Tailwind colours do not react to the theme), hover for `MatchupCard`
  (`group`/`group-hover:`/`transition-colors` — white text and border, yellow aggregate),
  empty states for `Bracket` + `SearchPage` (lesson: `!data` vs `.length===0` — an empty
  array is truthy).
* [x] **The `useSeasonSelector` hook** (DRY across `LeaguePage` + `BracketPage`): the
  default season is the newest one through **derived state**
  `selectedSeason ?? seasons?.[0]` (never copy server state into `useState`). Review bug:
  the type is `number|null`, not `string` (an HTML value is a string, but we convert with
  `Number`).
* [x] **Poisson theory** (step by step): λ → the distribution P(k); attack/defence strength
  relative to the league baseline; `λ = baseline × attack × defence`; the matrix
  (`np.outer`) → triangles → P(1/X/2). The baseline accounts for the opponent and keeps the
  scale.
* [x] **numpy 2.2.6** + the new `app/prediction/` package. **`poisson.py`** (5 functions:
  pmf/distribution/score_matrix with normalisation/outcome/top_scorelines).
  **`strength.py`** (3 functions: `league_baseline` with `func.sum`/`.scalar()`,
  `team_attack_defence`, `match_lambdas` + `HOME_ADVANTAGE=1.3`). Verified: λ 1.96/0.95 →
  61/21/18; Barcelona attack 1.86 / defence 0.70; Bundesliga baseline 1.618 (the
  goal-heavy league — realistic).
* [x] **The `GET /predict` endpoint** (`routers/predictions.py` + registration): 404
  validation (both teams must be in standings), the pipeline, the `float()` fix; the
  `PredictionResponse`/`ScoreLine` schemas. Barcelona vs Oviedo → 92.7/5.3/1.8%, most
  likely 3:0.
* [x] **Tests**: `tests/test_poisson.py` (5, known values) + 2 tests for `/predict`
  (**pytest 12→19**). A test caught a real problem (the sum came to 0.999 at high λ → the
  **matrix normalisation**).
* **Decisions**: **3 models** (baseline Poisson → improved Dixon-Coles → ML); the data
  source is **standings** (league fixtures are too thin); the predictor is
  **within-league** (strength is relative to a league); `GET`, not `POST`. **New
  goal/schedule**: a beta with the predictor by 13 Sep (UI), **deployment + README + CV
  after the trip, ~26 Sep** — the MVP-to-deployment priority comes BEFORE Phases 4/5.
* **Learning**: Poisson/λ; the strength model (the baseline as a reference, accounting for
  the opponent); numpy (`outer`/`tril`/`triu`/`trace`, normalisation); `func.sum` +
  `.scalar()` vs `.all()`; `list` (the class) vs `[]`; derived state; `!data` vs
  `.length===0`; `group-hover`; separating maths from the database from the API; GET for
  reads.
* **Quality**: pytest **19/19**, Ruff clean; frontend `tsc` + oxlint **0/0**. Database
  unchanged (leagues 15, teams 1962, standings 572, fixtures 7980). API-Football: **0
  requests**.
* **Result**: **Phase 2 finished + the Phase 3 backend (Poisson predictor) COMPLETE**. For
  Session 18 (a sprint to 13 Sep): **the predictor UI** (pick a league → 2 teams → 1/X/2
  bars + most likely scores).

## Session 18 (2026-09-13) — The predictor UI (Phase 3 frontend, a sprint) — Phase 3 COMPLETE
* [x] **API layer `frontend/src/api/predictions.ts`** (written by the owner): types
  `ScoreLine`/`Prediction` (mirroring `PredictionResponse`) +
  `getPrediction(homeId, awayId, leagueId, season)`. The review caught a real bug: the
  query keys in the URL were camelCase (`homeId`) while the backend expects `home_id`
  (a guaranteed 422); fixed to snake_case, `getPredictions`→`getPrediction`.
* [x] **Page + routing**: `pages/PredictPage.tsx` (new), the `/predict` route in `App.tsx`,
  a "🔮 Predict match" link on `HomePage` (classes reused from "Find team"). The component
  is `PredictPage` — PascalCase (a JSX requirement).
* [x] **Picking a league**: `leagues = COUNTRIES.map(c => c.league)` (module level, reusing
  HomePage's data; leagues only — they are the ones with `standings`),
  `useState<number|null>` + a controlled `<select>` with a placeholder (the `LeaguePage`
  pattern).
* [x] **Picking 2 teams**: `useQuery(["standings", leagueId, PREDICTION_SEASON])` with
  **`enabled: leagueId!==null`** (reusing `getStandings`),
  `teams = standings?.map(s => s.team) ?? []`, two "Home vs Away" selects, and a **reset**
  of `homeId`/`awayId` when the league changes.
* [x] **Calling `/predict`**: `useQuery(["prediction", ...])` with
  **`enabled: homeId!==null && awayId!==null && homeId!==awayId`** (blocking "a team cannot
  play itself"), the `!` non-null assertion, `isLoading`/`isError`, and the message "Pick
  two different teams".
* [x] **Visualisation — `components/PredictionResult.tsx`** (new): three 1/X/2 bars + the
  most likely scores. An internal `OutcomeBar` (DRY, used 3× with props); a `bg-gray-700`
  track + a fill whose width in `%` comes from an **inline style**; dark-theme colours
  (emerald/amber/sky, the `MatchupCard` palette); team names on the labels (`teams.find` →
  props). State/data (`PredictPage`) separated from presentation (`PredictionResult`).
* **Decisions**: URL keys in snake_case / JS variables in camelCase (an audit of `api/*.ts`
  — only `predictions.ts` had the bug); **the prediction season is the constant
  `PREDICTION_SEASON=2025`** (the last completed season → stable data; the current one in
  September is too thin); **blending seasons is a model #2 feature** (Dixon-Coles), not
  baseline work (baseline first); the predictor is **within-league**.
* **Learning**: path param (by position) vs query param (the name in the URL must match);
  Python `snake_case` vs TS `camelCase`/`PascalCase`/`UPPER_SNAKE` conventions (and why;
  PascalCase for components is a JSX requirement); `enabled` in `useQuery` (a dependent
  query); resetting dependent state; the non-null `!`; components + props + DRY
  (`OutcomeBar`); Tailwind — a dynamic width goes in an inline style, classes must be
  complete literals; team strength comes from one season's table (a small sample → noise);
  lint/tsc in WSL need nvm loaded explicitly.
* **Quality**: frontend oxlint **0/0**, `tsc` clean; backend untouched (pytest **19/19**,
  Ruff clean). Database unchanged (leagues 15, teams 1962, standings 572, fixtures 7980).
  API-Football: **0 requests**.
* **Debt**: `TeamSelect` (duplicated selects), `index.css`/`App.css` (Vite template
  leftovers), a loading state for the team lists (deliberately skipped), blending seasons →
  model #2.
* **Result**: **Phase 3 COMPLETE** — the Poisson predictor works end to end locally (beta).
  For Session 19 (after the trip, ~26 Sep): **DEPLOYMENT** (backend + PostgreSQL on
  Railway/Render, frontend on Vercel + CORS) + **a professional README** for the CV — the
  priority BEFORE Phases 4/5.

## Session 19 (2026-09-28 – 09-30) — Public deployment + repo prepared for external readers
* [x] **The project is live**: frontend https://football-predictor-adimilo190.vercel.app,
  API https://football-predictor-ac40.onrender.com (+ `/docs`).
* [x] **Backend prepared for production**: CORS origins read from `ALLOWED_ORIGINS`
  (a comma-separated string split by a property in `Settings`, because env variables are
  always text); a `postgres://` → `postgresql://` validator; `Procfile`
  (`alembic upgrade head && uvicorn … --host 0.0.0.0 --port ${PORT:-8000}`);
  `.python-version`; `pool_pre_ping=True` + `pool_recycle=300` in `create_engine`
  (a managed database suspends when idle, so pooled connections die server-side — a class
  of bug that cannot appear against a local PostgreSQL).
* [x] **Admin endpoints protected**: new `app/security.py` with the `require_import_token`
  dependency (`X-Import-Token` header, `secrets.compare_digest`, 401), attached to the
  whole imports router so every future import endpoint is covered by default. Verified in
  production: no token → 401, old token after rotation → 401.
* [x] **Hosting chosen after checking the current terms**: Render (backend, free) + Neon
  (Postgres, free, no expiry) + Vercel (frontend). Render's own free Postgres was rejected
  — it is deleted 30 days after creation, which would have killed the CV demo mid-October.
  Railway, Fly.io and Koyeb no longer offer a permanent free tier. Everything runs in
  Frankfurt so the backend and database are not separated by an ocean.
* [x] **Data moved with `pg_dump --data-only` in two passes** (leagues + teams first, then
  standings + fixtures): `pg_dump` orders tables alphabetically, which would put `fixtures`
  before its parents and break the foreign keys. Plus a `setval` on the `standings.id`
  sequence — the only id the database generates itself.
* [x] **Two bugs caught only by testing from the outside**: Vercel Authentication (every
  path returned a 302 to a Vercel login screen — invisible to the logged-in owner, fatal
  for a recruiter) and 404s on deep links (`/predict`, `/leagues/39`), fixed with an SPA
  rewrite in `frontend/vercel.json`. Also the page title, still `frontend` from the Vite
  template.
* [x] **UptimeRobot** pings `/` every 5 minutes so the free instance never sleeps — and
  the health endpoint deliberately does not touch the database, so Neon keeps sleeping and
  its 100 compute-hours are not burned.
* [x] **Documentation pass over the whole repo**: a "what is in this file and why" header
  in 18 files that lacked one, comments on 11 non-obvious decisions, the dead `App.css`
  removed, a stale comment fixed, and English everywhere — code, `.gitignore`, both
  `.env.example` files, `CLAUDE.md` and the five project docs in `instructions/` (1220
  lines). Session logs stay in Polish as the owner's learning journal, with an English
  `sessions/README.md` explaining that.
* [x] **Production data refreshed** on the last day of the API-Football subscription:
  +233 matches, 3145 updated, +15 teams (leagues 15, teams 1977, standings 572, fixtures
  8213).
* [x] **README for the CV** (186 lines): demo links, features, how the Poisson model works
  step by step, an honest "Known limitations" section, an architecture diagram, the stack
  with reasoning, an endpoint table and local setup instructions.
* **Quality**: pytest **19/19**, Ruff clean, oxlint **0/0**, `tsc` clean, `npm run build`
  green. API-Football: ~21 requests (the refresh).
* **Result**: the September goal is met — a **publicly available app** with the predictor,
  a README a stranger can read, and a repo documented for external readers. Phases 4
  (Monte Carlo) and 5 (ML) continue in October on the live project.
