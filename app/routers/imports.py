# app/routers/imports.py
# Write endpoints (POST) that pull data from API-Football into our database,
# together with the ETL helpers they rely on. Grouped in their own APIRouter and
# attached to the app in main.py via include_router().

from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.constants import (
    DEFAULT_SEASON,
    DOMESTIC_CUP_IDS,
    DOMESTIC_LEAGUE_IDS,
    EUROPEAN_COMPETITION_IDS,
    TARGET_LEAGUE_IDS,
)
from app.database import get_db

# tags=[...] groups these endpoints under one heading in the Swagger UI (/docs).
router = APIRouter(tags=["imports"])

# --- API CONFIGURATION ---
API_KEY = settings.API_FOOTBALL_KEY
HEADERS = {"x-apisports-key": API_KEY}


# --- API-FOOTBALL HELPERS ---


async def fetch_league_standings(
    client: httpx.AsyncClient, league_id: int, season: int
) -> list[dict]:
    """Fetch one league's standings from API-Football (the Extract step of ETL).

    Returns the raw standing rows (dicts) exactly as the API sends them —
    turning them into our database models is a separate (Transform) step.
    """
    try:
        # params builds the query string (?league=39&season=2024) and handles
        # the encoding for us. timeout: give up instead of hanging forever.
        response = await client.get(
            f"{settings.API_FOOTBALL_BASE_URL}/standings",
            headers=HEADERS,
            params={"league": league_id, "season": season},
            timeout=15.0,
        )
        # Turn any 4xx/5xx answer into an exception instead of reading garbage.
        response.raise_for_status()
    except httpx.HTTPError as exc:
        # Covers bad statuses AND transport problems (timeout, DNS, refused
        # connection). 502 = "our upstream data source failed", not our fault.
        raise HTTPException(
            status_code=502,
            detail=f"API-Football request failed for league {league_id}: {exc}",
        ) from exc

    data = response.json()

    # API-Football quirk: it can answer 200 OK and still report problems
    # (e.g. exceeded daily limit) inside an "errors" field of the body.
    if data.get("errors"):
        raise HTTPException(
            status_code=502,
            detail=f"API-Football error for league {league_id}: {data['errors']}",
        )

    # Empty response = season not available on the free plan (a legitimate gap),
    # so return no rows instead of failing. Real failures were caught above.
    api_response = data.get("response", [])
    if not api_response:
        return []

    # The table rows sit deep in the payload: response[0].league.standings
    # is a LIST OF LISTS (groups). A regular league has exactly one group,
    # but we flatten defensively so group formats won't surprise us later.
    groups = api_response[0]["league"]["standings"]

    rows: list[dict] = []
    for group in groups:
        rows.extend(group)  # extend adds every element of `group`, one by one
    return rows


def upsert_league_standings(
    db: Session, league_id: int, season: int, rows: list[dict]
) -> dict[str, int]:
    """Save raw standing rows into teams/standings (the Transform + Load steps).

    "Upsert" = UPDATE the row if it already exists, INSERT it otherwise.
    Done row by row through the ORM: plenty fast for 6 leagues x ~20 teams
    and much easier to read than raw SQL (Postgres INSERT ... ON CONFLICT).
    """
    league = db.query(models.League).filter(models.League.id == league_id).first()
    if league is None:
        raise HTTPException(
            status_code=404,
            detail=f"League {league_id} not in database — run /import-leagues first",
        )

    stats = {"teams_added": 0, "standings_added": 0, "standings_updated": 0}

    for row in rows:
        team_info = row["team"]

        # -- Team upsert --
        team = db.query(models.Team).filter(models.Team.id == team_info["id"]).first()
        if team is None:
            team = models.Team(
                id=team_info["id"],
                name=team_info["name"],
                # The standings payload has no team country, but every team
                # in a domestic league shares the league's country.
                country=league.country,
                logo_url=team_info["logo"],
            )
            db.add(team)
            stats["teams_added"] += 1
        else:
            # Refresh fields that can change over time (rebrands, new logo).
            team.name = team_info["name"]
            team.logo_url = team_info["logo"]

        # -- Standing upsert --
        standing = (
            db.query(models.Standing)
            .filter(
                models.Standing.league_id == league_id,
                models.Standing.team_id == team_info["id"],
                models.Standing.season == season,
            )
            .first()
        )
        if standing is None:
            standing = models.Standing(
                league_id=league_id, team_id=team_info["id"], season=season
            )
            db.add(standing)
            stats["standings_added"] += 1
        else:
            stats["standings_updated"] += 1

        # Copy the statistics — same code for a new and an existing row.
        # SQLAlchemy tracks attribute changes and emits UPDATEs on commit.
        standing.rank = row["rank"]
        standing.points = row["points"]
        standing.played = row["all"]["played"]
        standing.wins = row["all"]["win"]
        standing.draws = row["all"]["draw"]
        standing.losses = row["all"]["lose"]
        standing.goals_for = row["all"]["goals"]["for"]
        standing.goals_against = row["all"]["goals"]["against"]
        standing.form = row["form"]

    # NOTE: no db.commit() here on purpose — the caller decides when to commit,
    # so importing 6 leagues can be one all-or-nothing transaction.
    return stats


async def fetch_fixtures(
    client: httpx.AsyncClient, league_id: int, season: int
) -> list[dict]:
    """Fetch one competition's fixtures from API-Football (the Extract step of ETL).

    Works for any competition id (league or cup) — API-Football treats them
    the same. Returns the raw match rows (dicts) exactly as the API sends them;
    turning them into our database models is a separate (Transform) step.
    """
    try:
        # params builds the query string (?league=39&season=2024) and handles
        # the encoding for us. timeout: give up instead of hanging forever.
        response = await client.get(
            f"{settings.API_FOOTBALL_BASE_URL}/fixtures",
            headers=HEADERS,
            params={"league": league_id, "season": season},
            timeout=15.0,
        )
        # Turn any 4xx/5xx answer into an exception instead of reading garbage.
        response.raise_for_status()
    except httpx.HTTPError as exc:
        # Covers bad statuses AND transport problems (timeout, DNS, refused
        # connection). 502 = "our upstream data source failed", not our fault.
        raise HTTPException(
            status_code=502,
            detail=f"API-Football request failed for fixtures {league_id}: {exc}",
        ) from exc

    data = response.json()

    # API-Football quirk: it can answer 200 OK and still report problems
    # (e.g. exceeded daily limit) inside an "errors" field of the body.
    if data.get("errors"):
        raise HTTPException(
            status_code=502,
            detail=f"API-Football error for fixtures {league_id}: {data['errors']}",
        )

    # Empty response is a legitimate gap (free plan), so return no matches.
    # Real failures were already caught above (HTTP error / "errors" field).
    return data.get("response", [])


def upsert_team(db: Session, team_info: dict) -> bool:
    """Insert a team if new, else refresh its mutable fields.

    The fixtures payload has no country, so a brand-new team gets country=None;
    an existing team keeps whatever country it already has (e.g. set by the
    standings import). Returns True when a new team was inserted.
    """
    # 1. Look for the team by its API id. .first() returns the object or None.
    team = db.query(models.Team).filter(models.Team.id == team_info["id"]).first()

    # 2. Not found: create it. Often a lower-league or foreign side that is not
    #    in our standings. A fixtures payload has no country, so leave it empty.
    if team is None:
        team = models.Team(
            id=team_info["id"],
            name=team_info["name"],
            country=None,
            logo_url=team_info["logo"],
        )
        db.add(team)
        return True

    # 3. Already exists: refresh only what can change (name, logo). We do NOT
    #    touch country — it may already be set correctly by the standings import.
    team.name = team_info["name"]
    team.logo_url = team_info["logo"]
    return False


def upsert_fixtures(
    db: Session,
    league_id: int,
    season: int,
    fixtures: list[dict],
    seen_team_ids: set[int],
) -> dict[str, int]:
    """Save raw fixtures into teams/fixtures (the Transform + Load steps).

    "Upsert" = UPDATE the row if it already exists, INSERT it otherwise.
    Both teams of every match are upserted first (cups include sides from
    lower leagues that our standings import never saw), then the fixture
    itself. No db.commit() here — the caller decides when to commit.

    seen_team_ids is shared across the WHOLE import (passed in by the caller):
    a club can play in several competitions in one run — a side knocked out of
    one European cup drops into a lower one. With autoflush=False a team added
    but not yet committed stays invisible to the next query, so a per-competition
    guard would add it twice and duplicate its primary key. One shared set makes
    every team id handled exactly once across all competitions.
    """
    league = db.query(models.League).filter(models.League.id == league_id).first()
    if league is None:
        raise HTTPException(
            404,
            detail=f"League {league_id} not in database — run /import-leagues first",
        )

    stats = {"teams_added": 0, "fixtures_added": 0, "fixtures_updated": 0}

    for fx in fixtures:
        home_team = fx["teams"]["home"]
        away_team = fx["teams"]["away"]
        # -- Team upsert (once per team within this transaction) --
        for team in (home_team, away_team):
            if team["id"] not in seen_team_ids:
                if upsert_team(db, team):
                    stats["teams_added"] += 1
                seen_team_ids.add(team["id"])
        # -- Fixture upsert --
        fixture = (
            db.query(models.Fixture)
            .filter(models.Fixture.id == fx["fixture"]["id"])
            .first()
        )
        if fixture is None:
            fixture = models.Fixture(
                id=fx["fixture"]["id"],
                league_id=league_id,
                home_team_id=home_team["id"],
                away_team_id=away_team["id"],
                season=season,
            )
            db.add(fixture)
            stats["fixtures_added"] += 1
        else:
            stats["fixtures_updated"] += 1

        # Copy the statistics — same code for a new and an existing row.
        # SQLAlchemy tracks attribute changes and emits UPDATEs on commit.
        fixture.round = fx["league"]["round"]
        fixture.date = datetime.fromisoformat(fx["fixture"]["date"])
        fixture.status = fx["fixture"]["status"]["short"]
        fixture.home_goals = fx["goals"]["home"]
        fixture.away_goals = fx["goals"]["away"]

    # NOTE: no db.commit() here on purpose — the caller decides when to commit,
    # so importing 6 leagues can be one all-or-nothing transaction.
    return stats


# --- WRITE ENDPOINTS (POST): pull data from API-Football into our database ---
# POST, not GET: these change the database, while GET stays "safe" (read-only)
# by REST convention. Each import is manual and deliberate — the free plan
# allows only 100 API requests/day.
# import-leagues: one call for the full league list, filtered locally to the
# ids we track (TARGET_LEAGUE_IDS) — cheaper than one request per competition.
@router.post("/import-leagues")
async def import_leagues(db: Session = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        # One request for the full league list (~1200 items), filtered locally.
        # Cheaper than 13 per-id requests on the free plan (100 requests/day).
        response = await client.get(
            f"{settings.API_FOOTBALL_BASE_URL}/leagues",
            headers=HEADERS,
        )
        data = response.json()

    # API-Football keeps the actual data under the "response" key.
    leagues_data = data.get("response", [])

    added = []

    for item in leagues_data:
        league_info = item["league"]
        country_info = item["country"]

        # Keep only the competitions this project tracks.
        if league_info["id"] not in TARGET_LEAGUE_IDS:
            continue

        # Skip leagues we already have (avoid duplicates) by checking the ID.
        existing_league = (
            db.query(models.League)
            .filter(models.League.id == league_info["id"])
            .first()
        )

        if not existing_league:
            # If it does not exist yet, build a new object from our model.
            new_league = models.League(
                id=league_info["id"],
                name=league_info["name"],
                country=country_info["name"],
                logo_url=league_info["logo"],
            )
            db.add(new_league)  # Stage it for saving.
            added.append(f"{league_info['name']} ({country_info['name']})")

    db.commit()  # Persist all staged changes to the database.

    return {
        "message": f"Sukces! Zapisano {len(added)} nowych rozgrywek.",
        "imported": added,
    }


# import-standings: full ETL for the 6 league tables — one API call per
# division. Extract (fetch_league_standings) then Transform+Load (upsert_...).
@router.post("/import-standings")
async def import_standings(season: int = DEFAULT_SEASON, db: Session = Depends(get_db)):
    # Per-league stats for the response + running totals across all leagues.
    leagues_report: dict[str, dict[str, int]] = {}
    totals = {"teams_added": 0, "standings_added": 0, "standings_updated": 0}

    # One shared client keeps a single connection open for all 6 requests
    # (faster than opening and closing a connection per league).
    async with httpx.AsyncClient() as client:
        for league_id, league_name in DOMESTIC_LEAGUE_IDS.items():
            rows = await fetch_league_standings(client, league_id, season)
            stats = upsert_league_standings(db, league_id, season, rows)

            leagues_report[league_name] = stats
            for key in totals:
                totals[key] += stats[key]

    # ONE commit for all leagues = one transaction. If any league fails above,
    # the exception skips this line and nothing is saved (all-or-nothing).
    db.commit()

    return {
        "message": f"Imported standings for {len(leagues_report)} leagues.",
        "season": season,
        "totals": totals,
        "leagues": leagues_report,
    }


# import-fixtures: full ETL for cup matches — one API call per competition
# (6 domestic cups + UCL). Empty competitions are tolerated (fetch returns []),
# so a gap in one does not abort the whole import.
@router.post("/import-fixtures")
async def import_fixtures(season: int = DEFAULT_SEASON, db: Session = Depends(get_db)):
    cups_report = {}
    totals = {"teams_added": 0, "fixtures_added": 0, "fixtures_updated": 0}
    competitions = {
        **DOMESTIC_CUP_IDS,
        **EUROPEAN_COMPETITION_IDS,
    }  # 6 cups + 3 European
    # One shared set for the whole import: a club can appear in several
    # competitions (a team knocked out of one European cup drops into a lower
    # one), and with autoflush=False a pending team is invisible to the next
    # query — so a per-competition guard would insert it twice (duplicate PK).
    seen_team_ids: set[int] = set()
    async with httpx.AsyncClient() as client:
        for league_id, name in competitions.items():
            fixtures = await fetch_fixtures(client, league_id, season)
            stats = upsert_fixtures(db, league_id, season, fixtures, seen_team_ids)
            cups_report[name] = stats
            for key in totals:
                totals[key] += stats[key]
    db.commit()  # one commit = one all-or-nothing transaction
    return {
        "message": f"Imported fixtures for {len(cups_report)} competitions.",
        "season": season,
        "totals": totals,
        "cups": cups_report,
    }
