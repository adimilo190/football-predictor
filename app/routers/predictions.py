# app/routers/predictions.py
# Prediction endpoint: given two teams in a league/season, return the Poisson
# model's 1/X/2 probabilities plus the most likely scorelines. It only reads
# stored standings and computes — nothing is written, so it is a GET.

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.prediction.poisson import (
    match_outcome_probabilities,
    score_matrix,
    top_scorelines,
)
from app.prediction.strength import match_lambdas

router = APIRouter(tags=["predictions"])

# Cap goals for the score matrix; P(more than 10) is negligible.
MAX_GOALS = 10


@router.get("/predict", response_model=schemas.PredictionResponse)
def predict_match(
    home_id: int,
    away_id: int,
    league_id: int,
    season: int,
    db: Session = Depends(get_db),
):
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

    lam_home, lam_away = match_lambdas(db, home_id, away_id, league_id, season)
    matrix = score_matrix(lam_home, lam_away, MAX_GOALS)
    home_win, draw, away_win = match_outcome_probabilities(matrix)

    top_scores = []
    for home_goals, away_goals, probability in top_scorelines(matrix, 5):
        top_scores.append(
            schemas.ScoreLine(
                home_goals=home_goals,
                away_goals=away_goals,
                probability=probability,
            )
        )

    # float() converts numpy's float64 to plain floats so FastAPI serializes
    # them cleanly to JSON.
    return schemas.PredictionResponse(
        home_win=float(home_win),
        draw=float(draw),
        away_win=float(away_win),
        top_scores=top_scores,
    )
