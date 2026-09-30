# Football Predictor

League tables, cup brackets and statistical match predictions for Europe's top six
leagues — a full-stack project built with FastAPI, React and PostgreSQL.

**[Live demo](https://football-predictor-adimilo190.vercel.app)** ·
**[API documentation](https://football-predictor-ac40.onrender.com/docs)**

> The backend runs on a free hosting tier. It is kept warm by an uptime monitor, but if
> it has been idle the very first request can take up to a minute while the service
> wakes up.

<!-- Screenshots: add the images to docs/screenshots/ and uncomment this block.
## Screenshots

| League table | Cup bracket | Predictor |
|---|---|---|
| ![League table](docs/screenshots/table.png) | ![Cup bracket](docs/screenshots/bracket.png) | ![Predictor](docs/screenshots/predict.png) |
-->

## What it does

- **League tables** for the Premier League, La Liga, Serie A, Bundesliga, Ligue 1 and
  Primeira Liga, with a season selector covering 2022–2026.
- **Cup brackets** rendered as tournament trees for six domestic cups and the three UEFA
  competitions, with two-legged ties folded into a single node and aggregate scores.
- **Team pages** — search any of ~2,000 teams and see its latest results and upcoming
  fixtures across every competition it plays in.
- **Match predictor** — pick two teams from the same league and get the probability of a
  home win, draw or away win, plus the five most likely scorelines.

The database holds 15 competitions, ~2,000 teams, league tables for seasons 2022–2026 and
~8,200 matches for seasons 2024–2026, all imported from
[API-Football](https://www.api-football.com/) and stored locally rather than proxied, so
the app never depends on a third-party API at request time.

## How the prediction works

The predictor is a **Poisson model**, the same starting point bookmakers use. Goals are
rare, independent events spread over 90 minutes, which is exactly what the Poisson
distribution describes.

1. **League baseline** — the average number of goals a team scores per match in that
   league and season.
2. **Attack and defence strength** — each team's goals scored and conceded per match,
   expressed relative to that baseline. An attack of `1.2` means "20% better than an
   average team in this league".
3. **Expected goals (λ)** — `baseline × own attack × opponent's defence`, with a flat
   1.3× home-advantage multiplier applied to the home side.
4. **Score matrix** — the outer product of both teams' goal distributions gives the
   probability of every scoreline; summing its lower triangle, diagonal and upper
   triangle yields P(home win), P(draw) and P(away win).

The maths lives in [`app/prediction/poisson.py`](app/prediction/poisson.py) with no
database or framework dependencies, which is what makes it testable against
hand-computed values in [`tests/test_poisson.py`](tests/test_poisson.py).

**Known limitations (v1).** Strength is measured relative to a single league, so the
model cannot compare teams across leagues. It reads a single season's table, so it has no
sense of recent form, and the home advantage is a constant rather than something derived
from the data. Predictions for the current season use the last completed one, because
five rounds of data produce noisy strengths.

**Planned.** A Dixon-Coles style model with time-weighted blending of several seasons and
a low-score correction, then a machine-learning model trained on historical data, with
the three compared head to head on log-loss and accuracy.

## Architecture

```
Browser
   │
   ▼
Vercel ─────────────► Render ─────────────► Neon
static React bundle   FastAPI (Python)      PostgreSQL
                             │
                             └──► API-Football (imports only, never at request time)
```

Three separate services, because they are three different kinds of thing: the frontend is
a set of static files, the backend is a long-running process, and the database is state
that must not be lost. All three run in or near Frankfurt to keep round trips short.

## Tech stack

**Backend** — FastAPI (async, typed, generates its own OpenAPI docs), SQLAlchemy 2.0 ORM,
PostgreSQL, Alembic for versioned schema migrations, httpx for the async ETL, numpy for
the model, pytest for tests, Ruff for linting and formatting.

**Frontend** — React 19 with TypeScript, Vite, Tailwind CSS v4, React Router for
client-side routing, TanStack Query for server state (caching, loading and error states),
oxlint and Prettier.

**Infrastructure** — Vercel (frontend), Render (backend), Neon (serverless Postgres),
UptimeRobot (monitoring).

A few decisions worth calling out:

- **Data is imported, not proxied.** API-Football allows a limited number of requests, so
  the app owns its data and refreshes it on demand through explicit import endpoints.
- **Writes are separated from reads.** The `POST /import-*` endpoints spend the API quota
  and write to the database, so they require a shared secret in an `X-Import-Token`
  header; everything else is public.
- **The schema is owned by Alembic.** No `create_all`, no manual DDL — migrations run
  automatically on every deploy.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/leagues` | Every tracked competition |
| `GET` | `/leagues/{id}/standings?season=` | League table for a season |
| `GET` | `/leagues/{id}/fixtures?season=` | Flat list of matches |
| `GET` | `/leagues/{id}/bracket?season=&knockout_only=` | Matches grouped by round |
| `GET` | `/leagues/{id}/seasons` | Seasons available for that competition |
| `GET` | `/teams?search=` | Team search by name |
| `GET` | `/teams/{id}/past-matches?last=` | Latest finished matches |
| `GET` | `/teams/{id}/future-matches?next=` | Upcoming fixtures |
| `GET` | `/predict?home_id=&away_id=&league_id=&season=` | Poisson prediction |
| `POST` | `/import-leagues`, `/import-standings`, `/import-fixtures` | ETL from API-Football (requires `X-Import-Token`) |

Interactive documentation is at [`/docs`](https://football-predictor-ac40.onrender.com/docs).

## Running it locally

Requires Python 3.10, Node.js 20+ and PostgreSQL.

```bash
git clone https://github.com/adimilo190/football-predictor.git
cd football-predictor
```

**Backend**

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
cp .env.example .env          # then fill in the values
createdb football_db
venv/bin/alembic upgrade head
venv/bin/uvicorn app.main:app --reload
```

`.env` needs a `DATABASE_URL`, an `API_FOOTBALL_KEY` (free tier is enough to try it out),
an `IMPORT_TOKEN` you generate yourself and `ALLOWED_ORIGINS`. The template explains each
one.

With the server running, populate the database — the imports must run in this order,
because standings and fixtures reference the competitions:

```bash
curl -X POST localhost:8000/import-leagues -H "X-Import-Token: $IMPORT_TOKEN"
curl -X POST "localhost:8000/import-standings?season=2025" -H "X-Import-Token: $IMPORT_TOKEN"
curl -X POST "localhost:8000/import-fixtures?season=2025" -H "X-Import-Token: $IMPORT_TOKEN"
```

**Frontend**

```bash
cd frontend
npm install
cp .env.example .env          # VITE_API_URL=http://localhost:8000
npm run dev
```

**Tests and checks**

```bash
venv/bin/pytest               # 19 tests: API endpoints + the Poisson maths
venv/bin/ruff check app/
cd frontend && npm run lint && npx tsc -b
```

## Project status

Phases 1–3 are complete and deployed: tables and brackets, team search and match views,
and the Poisson predictor. Next up are a Monte Carlo season simulator and the machine
learning model, followed by a comparison of all three prediction models.

The plan lives in [`instructions/ROADMAP.md`](instructions/ROADMAP.md), the architecture
in [`instructions/project-structure.md`](instructions/project-structure.md), and a
condensed history of every working session in
[`instructions/progres.md`](instructions/progres.md).

This is a learning project built while picking up the stack, so the `instructions/`
folder documents the reasoning behind each decision rather than only the outcome.
