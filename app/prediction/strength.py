# app/prediction/strength.py
# Turns stored data into the two numbers the maths in poisson.py needs: how many
# goals we expect each side to score (lambda). The only file in this package that
# touches the database - its source of truth is the standings table (goals scored
# and conceded per season), not live API calls.
#
# Strength is always measured RELATIVE to one league's average: an attack of 1.2
# means "20% better than a typical team in THIS league". That is why the predictor
# is within-league only - comparing two teams from different leagues would compare
# numbers built on two different baselines, which says nothing.

from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models
from app.constants import HOME_ADVANTAGE


def league_baseline(db: Session, league_id: int, season: int) -> float:
    """Average goals scored per team per match in a league/season.

    The model's baseline: what an average team scores. Attack and defence
    strengths are expressed relative to this number.
    """
    total_goals = (
        db.query(func.sum(models.Standing.goals_for))
        .filter(
            models.Standing.league_id == league_id, models.Standing.season == season
        )
        .scalar()
    )
    total_matches = (
        db.query(func.sum(models.Standing.played))
        .filter(
            models.Standing.league_id == league_id, models.Standing.season == season
        )
        .scalar()
    )
    if total_matches:  # False for None and 0
        return total_goals / total_matches
    return 0


def team_attack_defence(
    db: Session, team_id: int, league_id: int, season: int, base: float
) -> tuple[float, float]:
    """Attack and defence strength of a team, relative to the league baseline.

    attack  > 1  -> scores more than an average team;  < 1 -> fewer.
    defence < 1  -> concedes fewer than average (good); > 1 -> worse.
    """
    standing = (
        db.query(models.Standing)
        .filter(
            models.Standing.team_id == team_id,
            models.Standing.league_id == league_id,
            models.Standing.season == season,
        )
        .first()
    )
    scored_per_game = standing.goals_for / standing.played
    conceded_per_game = standing.goals_against / standing.played
    attack = scored_per_game / base
    defence = conceded_per_game / base
    return (attack, defence)


def match_lambdas(
    db: Session, home_id: int, away_id: int, league_id: int, season: int
) -> tuple[float, float]:
    """Expected goals (lambda) for the home and away team in a league match."""
    base = league_baseline(db, league_id, season)
    home_attack, home_defence = team_attack_defence(
        db, home_id, league_id, season, base
    )
    away_attack, away_defence = team_attack_defence(
        db, away_id, league_id, season, base
    )
    # Expected goals = the league's average, scaled twice: by how good this
    # attack is and by how leaky the opponent's defence is. A strong attack facing
    # a weak defence multiplies up; two solid defences pull the number down.
    # HOME_ADVANTAGE multiplies the home side only - standings do not split home
    # from away goals, so a flat boost is the best this data source allows.
    lam_home = base * home_attack * away_defence * HOME_ADVANTAGE
    lam_away = base * away_attack * home_defence
    return (lam_home, lam_away)
