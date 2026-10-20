# app/prediction/registry.py
# The list of prediction models the application knows about, and the only way
# anything outside this package gets hold of one. Routers ask for a model by the
# name that arrived in the URL; they never import a model class themselves, so
# adding a model is one line in MODELS below and nothing else.
#
# The registry is a plain dictionary rather than automatic discovery of
# PredictionModel's subclasses: it reads like a table of contents, the order and
# the names are ours to choose, and an unfinished model in the folder cannot
# appear in the API by accident.
#
# Note what is NOT here: no FastAPI, no HTTPException. A bad model name raises
# UnknownModelError, and turning that into an HTTP status is the router's job -
# which is what lets tests and scripts use this module without a web server.

from sqlalchemy.orm import Session

from app.prediction.base import PredictionModel
from app.prediction.poisson_model import PoissonModel

# Name used in URLs and API responses -> the class implementing it.
MODELS: dict[str, type[PredictionModel]] = {"poisson": PoissonModel}

# The model used when a request does not name one, so existing clients (and the
# current frontend, which knows nothing about models yet) keep working.
DEFAULT_MODEL = "poisson"


class UnknownModelError(Exception):
    """Raised when a caller asks for a model name that is not registered."""

    def __init__(self, name: str):
        # Kept as an attribute, not just inside the message, so the router can
        # put the offending name in its response without parsing text.
        self.name = name
        available = ", ".join(sorted(MODELS))
        super().__init__(f"Unknown model '{name}'. Available: {available}")


def get_model_class(name: str) -> type[PredictionModel]:
    """The model class registered under `name`, or UnknownModelError."""
    if name not in MODELS:
        raise UnknownModelError(name)
    return MODELS[name]


def build_model(name: str, db: Session, league_id: int, season: int) -> PredictionModel:
    """Create a ready-to-use model for one league and season."""
    model_class = get_model_class(name)
    return model_class(db, league_id, season)


def list_models() -> list[dict[str, str | bool]]:
    """Every registered model described for the UI's model picker.

    Reads the metadata straight off the classes, so listing the models needs no
    database session and builds no model: a class knows its own name long before
    anybody picks a league to run it on.
    """
    described = []
    for model_class in MODELS.values():
        described.append(
            {
                "name": model_class.name,
                "label": model_class.label,
                "description": model_class.description,
                "supports_cross_league": model_class.supports_cross_league,
            }
        )
    return described
