from fastapi import FastAPI, Depends, HTTPException
import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app import models, schemas
from app.constants import DEFAULT_SEASON, DOMESTIC_LEAGUE_IDS, TARGET_LEAGUE_IDS
from app.database import SessionLocal

# NOTE: tables are no longer created here. The database schema is managed
# exclusively by Alembic migrations — run: alembic upgrade head
app = FastAPI(title="Football Predictor API")

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

    # Unknown league/season combinations come back as an empty "response".
    api_response = data.get("response", [])
    if not api_response:
        raise HTTPException(
            status_code=502,
            detail=f"No standings for league {league_id}, season {season}",
        )

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


# --- DATABASE HELPER ---
# Opens a database session for the duration of a request and closes it afterwards.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"message": "Witaj w Football Predictor API! Serwer i baza działają."}


# --- 1. ENDPOINT: FETCH FROM THE API AND SAVE TO THE DATABASE ---
# POST, not GET: this endpoint changes the database, and GET requests
# are expected to be "safe" (read-only) by REST conventions.
@app.post("/import-leagues")
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


# --- 2. ENDPOINT: IMPORT LEAGUE TABLES (THE FULL ETL PIPELINE) ---
# Costs one API request per league (6 total) out of the 100/day free budget,
# so refreshing the data is a conscious, manual action — not automatic.
@app.post("/import-standings")
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


# --- 3. ENDPOINT: SHOW YOUR OWN DATABASE ---
# response_model=list[...] tells FastAPI: "this endpoint returns a LIST of leagues,
# each in the LeagueResponse shape". FastAPI filters out anything outside the schema.
@app.get("/my-leagues", response_model=list[schemas.LeagueResponse])
def get_my_leagues(db: Session = Depends(get_db)):
    # Plain Python query; SQLAlchemy translates it into: SELECT * FROM leagues;
    leagues = db.query(models.League).all()
    return leagues
