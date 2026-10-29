# app/routers/predictions.py
# Prediction endpoints. /predict answers "how will this match go" with 1/X/2
# probabilities and the most likely scorelines; /leagues/{id}/simulate runs the
# Monte Carlo season simulation and reports each team's odds of every final
# place; /models lists the prediction models the project offers, so the frontend
# can let the user choose one. All three only read stored data and compute —
# nothing is written, so all three are GETs.

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.prediction import registry
from app.prediction.simulation import TeamStart, simulate_season

router = APIRouter(tags=["predictions"])


@router.get("/predict", response_model=schemas.PredictionResponse)
def predict_match(
    home_id: int,
    away_id: int,
    league_id: int,
    season: int,
    model: str = registry.DEFAULT_MODEL,
    db: Session = Depends(get_db),
):
    """1/X/2 probabilities and the most likely scorelines for a single match."""
    # Both teams need a standings row in this league/season, or the strength
    # calculation has no data. Guard with a clear 404 before computing.
    for team_id in (home_id, away_id):
        standing = (
            db.query(models.Standing)
            .filter(
                models.Standing.team_id == team_id,
                models.Standing.league_id == league_id,
                models.Standing.season == season,
            )
            .first()
        )
        if standing is None:
            raise HTTPException(
                status_code=404,
                detail=f"Team {team_id} not in league {league_id}, season {season}.",
            )

    try:
        prediction_model = registry.build_model(model, db, league_id, season)
    except registry.UnknownModelError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    home_win, draw, away_win = prediction_model.probabilities(home_id, away_id)
    scorelines = prediction_model.top_scorelines(home_id, away_id)

    top_scores = []
    for home_goals, away_goals, probability in scorelines:
        top_scores.append(
            schemas.ScoreLine(
                home_goals=home_goals,
                away_goals=away_goals,
                probability=probability,
            )
        )

    return schemas.PredictionResponse(
        home_win=home_win,
        draw=draw,
        away_win=away_win,
        top_scores=top_scores,
    )


@router.get("/leagues/{league_id}/simulate", response_model=schemas.SimulationResponse)
def simulate_league(
    league_id: int,
    season: int,
    model: str = registry.DEFAULT_MODEL,
    iterations: int = Query(1000, ge=1, le=10000),
    strength_season: int | None = None,
    seed: int | None = None,
    db: Session = Depends(get_db),
):
    """Play the league's remaining fixtures many times and count the outcomes.

    The bounds on iterations are what let simulate_season assume a sane number:
    ge=1 rules out the division by zero, le=10000 rules out a request that would
    hold the server for half a minute.
    """
    rows = (
        db.query(models.Standing)
        .filter(
            models.Standing.league_id == league_id,
            models.Standing.season == season,
        )
        .order_by(models.Standing.rank)
        .all()
    )
    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No standings for league {league_id}, season {season}.",
        )

    start = []
    team_by_id = {}
    for row in rows:
        start.append(
            TeamStart(
                team_id=row.team_id,
                points=row.points,
                goals_for=row.goals_for,
                goals_against=row.goals_against,
            )
        )
        # Standing.team is already a relationship, so the names and logos the
        # response needs cost no extra query.
        team_by_id[row.team_id] = row.team

    # ORDER BY is not cosmetic here. A match's position in this list decides
    # which lambda draws its goals, and PostgreSQL promises no order without it.
    # An order that shifts between runs would make the same seed return
    # different tables, which would make seed meaningless.
    fixtures = (
        db.query(models.Fixture)
        .filter(
            models.Fixture.league_id == league_id,
            models.Fixture.season == season,
            models.Fixture.status == "NS",
        )
        .order_by(models.Fixture.date, models.Fixture.id)
        .all()
    )
    pairs = []
    for fixture in fixtures:
        pairs.append((fixture.home_team_id, fixture.away_team_id))

    # Strength is measured in a different season from the table on purpose. Two
    # rounds into a season, a team that has not scored yet gets an attack of 0
    # and could never score in a thousand simulations, so the default source is
    # the previous, completed season. Late in a season the current one becomes
    # the better source - that is what strength_season is for.
    if strength_season is None:
        strength_season = season - 1

    try:
        prediction_model = registry.build_model(model, db, league_id, strength_season)
    except registry.UnknownModelError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    # Deliberately outside the try above: simulate_season raises ValueError when
    # a fixture names a team the table does not hold, which is broken data on
    # our side rather than a bad request. That belongs in the logs as a 500, not
    # dressed up as a 404 blaming the caller.
    outcomes = simulate_season(
        prediction_model, pairs, start, np.random.default_rng(seed), iterations
    )

    teams = []
    for outcome in outcomes:
        teams.append(
            schemas.TeamSimulationOutcome(
                team=team_by_id[outcome.team_id],
                average_points=outcome.average_points,
                position_probabilities=outcome.position_probabilities,
            )
        )

    return schemas.SimulationResponse(
        model=prediction_model.name,
        iterations=iterations,
        matches_simulated=len(pairs),
        teams=teams,
    )


@router.get("/models", response_model=list[schemas.ModelInfo])
def list_prediction_models():
    """Every prediction model the project offers, for the model picker."""
    return registry.list_models()
