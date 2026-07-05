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
