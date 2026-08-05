# app/routers/competitions.py
# Read endpoints that serve our own database to the frontend: league list,
# standings tables, fixtures and cup brackets. They live in their own APIRouter
# and get attached to the app in main.py via include_router().

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app import models, schemas
from app.constants import DEFAULT_SEASON
from app.database import get_db

# tags=[...] groups these endpoints under one heading in the Swagger UI (/docs).
router = APIRouter(tags=["competitions"])


def query_fixtures(db: Session, league_id: int, season: int) -> list[models.Fixture]:
    """Shared read helper for the fixtures and bracket endpoints.

    Guards that the league exists (404 if not), then returns its fixtures for the
    given season — date-sorted, with both teams eagerly loaded (one JOIN instead
    of N+1 per-team lookups). Both endpoints below build on this, so the query
    lives in exactly one place (DRY).
    """
    league = db.query(models.League).filter(models.League.id == league_id).first()
    if league is None:
        raise HTTPException(
            status_code=404,
            detail=f"League {league_id} not found in database.",
        )

    return (
        db.query(models.Fixture)
        .options(
            joinedload(models.Fixture.home_team),
            joinedload(models.Fixture.away_team),
        )
        .filter(models.Fixture.league_id == league_id, models.Fixture.season == season)
        .order_by(models.Fixture.date)
        .all()
    )


@router.get("/leagues", response_model=list[schemas.LeagueResponse])
def get_leagues(db: Session = Depends(get_db)):
    # Plain Python query; SQLAlchemy translates it into: SELECT * FROM leagues;
    leagues = db.query(models.League).all()
    return leagues


@router.get(
    "/leagues/{league_id}/standings", response_model=list[schemas.StandingResponse]
)
def get_league_standings(
    league_id: int, season: int = DEFAULT_SEASON, db: Session = Depends(get_db)
):
    # Check if the league exists first; if not, return 404.
    league = db.query(models.League).filter(models.League.id == league_id).first()
    if league is None:
        raise HTTPException(
            status_code=404,
            detail=f"League {league_id} not found in database.",
        )

    # Fetch all standings for this league, ordered by rank.
    standings = (
        db.query(models.Standing)
        .options(joinedload(models.Standing.team))
        .filter(
            models.Standing.league_id == league_id, models.Standing.season == season
        )
        .order_by(models.Standing.rank)
        .all()
    )
    return standings


@router.get(
    "/leagues/{league_id}/fixtures",
    response_model=list[schemas.FixtureResponse],
)
def get_league_fixtures(
    league_id: int, season: int = DEFAULT_SEASON, db: Session = Depends(get_db)
):
    # The whole job (guard + query) is shared with the bracket endpoint below.
    return query_fixtures(db, league_id, season)


@router.get("/leagues/{league_id}/bracket", response_model=list[schemas.BracketRound])
def get_league_bracket(
    league_id: int, season: int = DEFAULT_SEASON, db: Session = Depends(get_db)
):
    fixtures = query_fixtures(db, league_id, season)

    # Group matches by round. Fixtures are already date-sorted, so the FIRST time
    # a round appears fixes its position — and a Python dict preserves insertion
    # order, so rounds come out chronologically (qualifiers -> final).
    rounds: dict[str, list] = {}
    for fx in fixtures:
        if fx.round not in rounds:
            rounds[fx.round] = []
        rounds[fx.round].append(fx)

    result = []
    for round_name, matches in rounds.items():
        result.append(schemas.BracketRound(round=round_name, fixtures=matches))
    return result
