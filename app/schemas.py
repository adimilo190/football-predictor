# app/schemas.py
# Schemas describe the SHAPE of the data our API accepts and returns.
# This is a "contract" with the frontend: a promise that the response has exactly
# these fields and types.
#
# Note the difference between layers:
#   - models.py  -> describes the TABLE in the database (SQLAlchemy)
#   - schemas.py -> describes WHAT GOES OUT through the API (Pydantic)
# Keeping them separate means a database change won't accidentally leak new,
# internal fields to the outside world.

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LeagueResponse(BaseModel):
    """Shape of a single league returned by the API."""

    id: int
    name: str
    country: str
    # "str | None" means: text OR nothing (None). A logo may not exist,
    # so we allow it to be missing. "= None" sets the default value.
    logo_url: str | None = None

    # from_attributes=True lets Pydantic build this schema straight from a
    # SQLAlchemy object (reading league.id, league.name, ...), not only from a
    # plain dict. Without it, FastAPI could not turn a database object into this
    # response.
    model_config = ConfigDict(from_attributes=True)


class TeamResponse(BaseModel):
    """Shape of a single team returned by the API."""

    id: int
    name: str
    country: str | None = None
    logo_url: str | None = None

    # Same trick as LeagueResponse: build this straight from a SQLAlchemy Team.
    model_config = ConfigDict(from_attributes=True)


class StandingResponse(BaseModel):
    """One row of a league table, ready for the frontend to render.

    Instead of a bare team_id number, we NEST the whole team (name + logo), so
    the frontend can draw a full table row from a single response — it never has
    to ask again "who is team 50?". Pydantic follows the Standing.team
    relationship and turns that Team object into a TeamResponse for us.
    """

    rank: int
    team: TeamResponse
    played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    points: int
    # Recent form (e.g. "WWDLW") can be missing, so allow None.
    form: str | None = None

    model_config = ConfigDict(from_attributes=True)


class FixtureResponse(BaseModel):
    """A single match, ready for the frontend (both teams nested)."""

    id: int
    round: str | None = None
    date: datetime
    status: str | None = None
    home_goals: int | None = None
    away_goals: int | None = None
    home_team: TeamResponse
    away_team: TeamResponse

    model_config = ConfigDict(from_attributes=True)


class BracketRound(BaseModel):
    """One round of a cup with its matches — a single column in the bracket UI."""

    round: str
    fixtures: list[FixtureResponse]


class ScoreLine(BaseModel):
    """A single scoreline (e.g. 2:1) and how likely it is."""

    home_goals: int
    away_goals: int
    probability: float


class PredictionResponse(BaseModel):
    """A model's prediction for a match: 1/X/2 plus the most likely scorelines.

    Which model produced it is the caller's choice, so nothing here is specific
    to Poisson. These are computed values (not read from a table), so no
    from_attributes.
    """

    home_win: float
    draw: float
    away_win: float
    top_scores: list[ScoreLine]


class ModelInfo(BaseModel):
    """One prediction model, as the model picker in the UI needs it."""

    name: str
    label: str
    description: str
    supports_cross_league: bool


class TeamSimulationOutcome(BaseModel):
    """One team's simulated season: where it is likely to finish."""

    team: TeamResponse
    average_points: float
    # Index 0 is first place: position_probabilities[0] is the title, the last
    # three summed are relegation. The frontend slices it instead of asking for
    # separate fields.
    position_probabilities: list[float]


class SimulationResponse(BaseModel):
    """Result of a Monte Carlo run over one league's remaining fixtures.

    model and iterations are echoed back so a stored or shared response says how
    it was produced - the numbers mean nothing without them.
    """

    model: str
    iterations: int
    matches_simulated: int
    teams: list[TeamSimulationOutcome]
