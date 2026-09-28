# app/routers/teams.py
# Read endpoints about a single team: its latest results, its upcoming matches and
# the name search that powers the frontend's team lookup. Attached to the app in
# main.py via include_router().
#
# Matches here are deliberately CROSS-COMPETITION (league, domestic cup and Europe
# mixed together, sorted by date): a team's form is its form regardless of which
# trophy the match belonged to. That is the difference from competitions.py, which
# always answers "within this one competition".

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app import models, schemas
from app.database import get_db
from app.constants import FINISHED_STATUSES

router = APIRouter(tags=["teams"])


# GET /teams/{team_id}/past-matches returns the last N finished matches for a team.
@router.get(
    "/teams/{team_id}/past-matches", response_model=list[schemas.FixtureResponse]
)
def get_team_past_matches(team_id: int, last: int = 5, db: Session = Depends(get_db)):
    """Return a team's last N finished matches, newest first."""
    # 1. Guard: does the team exist? 404 if not (same pattern as standings).
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if team is None:
        raise HTTPException(
            status_code=404,
            detail=f"Team {team_id} not found in database.",
        )

    # 2. The team's finished matches, newest first, capped at `last`.
    results = (
        db.query(models.Fixture)
        .options(
            joinedload(models.Fixture.home_team),
            joinedload(models.Fixture.away_team),
        )
        .filter(
            or_(
                models.Fixture.home_team_id == team_id,
                models.Fixture.away_team_id == team_id,
            ),
            models.Fixture.status.in_(FINISHED_STATUSES),
        )
        .order_by(models.Fixture.date.desc())
        .limit(last)
        .all()
    )
    return results


# GET /teams/{team_id}/future-matches returns the next N scheduled matches for a team.
@router.get(
    "/teams/{team_id}/future-matches", response_model=list[schemas.FixtureResponse]
)
def get_team_future_matches(team_id: int, next: int = 5, db: Session = Depends(get_db)):
    """Return a team's next N scheduled matches, soonest first."""
    # 1. Guard: does the team exist? 404 if not (same pattern as standings).
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if team is None:
        raise HTTPException(
            status_code=404,
            detail=f"Team {team_id} not found in database.",
        )

    # 2. The team's upcoming matches, soonest first, capped at `next`.
    matches = (
        db.query(models.Fixture)
        .options(
            joinedload(models.Fixture.home_team),
            joinedload(models.Fixture.away_team),
        )
        .filter(
            or_(
                models.Fixture.home_team_id == team_id,
                models.Fixture.away_team_id == team_id,
            ),
            models.Fixture.status == "NS",  # Not Started
        )
        .order_by(models.Fixture.date.asc())
        .limit(next)
        .all()
    )
    return matches


# GET /teams?search=... returns teams whose name contains the search phrase.
@router.get("/teams", response_model=list[schemas.TeamResponse])
def search_teams(search: str, db: Session = Depends(get_db)):
    """Return teams whose name contains the search phrase (case-insensitive)."""
    teams = (
        db.query(models.Team)
        .filter(models.Team.name.ilike(f"%{search}%"))
        .order_by(models.Team.name)
        .limit(20)
        .all()
    )
    return teams
