from fastapi import FastAPI, Depends
import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app import models, schemas
from app.constants import TARGET_LEAGUE_IDS
from app.database import SessionLocal

# NOTE: tables are no longer created here. The database schema is managed
# exclusively by Alembic migrations — run: alembic upgrade head
app = FastAPI(title="Football Predictor API")

# --- API CONFIGURATION ---
API_KEY = settings.API_FOOTBALL_KEY
HEADERS = {"x-apisports-key": API_KEY}


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


# --- 2. ENDPOINT: SHOW YOUR OWN DATABASE ---
# response_model=list[...] tells FastAPI: "this endpoint returns a LIST of leagues,
# each in the LeagueResponse shape". FastAPI filters out anything outside the schema.
@app.get("/my-leagues", response_model=list[schemas.LeagueResponse])
def get_my_leagues(db: Session = Depends(get_db)):
    # Plain Python query; SQLAlchemy translates it into: SELECT * FROM leagues;
    leagues = db.query(models.League).all()
    return leagues
