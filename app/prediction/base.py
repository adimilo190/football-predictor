# app/prediction/base.py
# The contract every prediction model has to honour. It exists so that nothing
# outside a model needs to know HOW that model works: the season simulator, the
# prediction endpoint and the model comparison planned for Phase 5 all talk to
# this interface, never to Poisson, Dixon-Coles or a trained classifier
# directly. Adding a model means writing one subclass and registering it - the
# simulator and the endpoints stay untouched.
#
# Two kinds of methods live here, and the difference is the point of the file:
#   - @abstractmethod ones have no body. Python refuses to create an object of
#     a subclass that leaves one out, so an unfinished model fails loudly at
#     construction instead of quietly returning nonsense.
#   - plain ones carry a default implementation a model MAY override when it can
#     do better. A goal-based model knows its likely scorelines and can draw
#     thousands of matches in a single numpy call; a classifier that only
#     outputs 1/X/2 can do neither, and inherits the honest fallback.
#
# Unlike poisson.py (pure maths, no database), a model is allowed to read the
# database: that is where the numbers describing teams come from.

from abc import ABC, abstractmethod

import numpy as np
from sqlalchemy.orm import Session


class PredictionModel(ABC):
    """Base class for every prediction model in the project."""

    # Metadata the API exposes, so the frontend can build a model picker from
    # the response instead of hard-coding a list. Every subclass overrides these.
    name: str = "base"
    label: str = "Base model"
    description: str = "Abstract model - not usable on its own."

    # Attack and defence strength is measured relative to one league's average,
    # which makes a cross-league comparison meaningless unless a model calibrates
    # the leagues against each other first. A model that can do it sets True.
    supports_cross_league: bool = False

    def __init__(self, db: Session, league_id: int, season: int):
        # A model is built for one league and one season: those three values
        # decide which rows it may learn from. Holding them here, instead of
        # passing them to every call, is also what will later make room for a
        # "use only matches before this date" cut-off - without it, Phase 5
        # would score a model on matches it already learned from.
        self.db = db
        self.league_id = league_id
        self.season = season

    @abstractmethod
    def probabilities(self, home_id: int, away_id: int) -> tuple[float, float, float]:
        """Chance of (home win, draw, away win); the three add up to 1.

        Model comparison runs on this method: log-loss and the Brier score need
        probabilities, not a single predicted outcome.
        """

    @abstractmethod
    def sample(
        self, home_id: int, away_id: int, rng: np.random.Generator
    ) -> tuple[int, int]:
        """Draw one plausible result, as (home goals, away goals).

        The random generator arrives as a parameter and is never created inside
        a model: one seeded generator drives an entire simulation, which is what
        makes its numbers reproducible between calls.
        """

    def top_scorelines(
        self, home_id: int, away_id: int, n: int = 5
    ) -> list[tuple[int, int, float]]:
        """The n most likely exact scores, as (home goals, away goals, probability).

        Empty by default: a model that predicts only 1/X/2 has nothing to say
        about exact scores, and the UI skips the section when the list is empty.
        """
        return []

    def sample_many(
        self,
        pairs: list[tuple[int, int]],
        rng: np.random.Generator,
        size: int,
    ) -> np.ndarray:
        """Draw `size` independent results for each match in `pairs`.

        Returns an array shaped (size, len(pairs), 2): one layer per simulated
        season, one row per match, two columns of goals.

        The season simulator calls this and never sample() in a loop, so a model
        able to draw everything at once can do so by overriding this method. The
        default below is the slow but always-correct version: it just calls
        sample() for every match of every simulation.
        """
        # int16 instead of the default int64: goals are tiny numbers, and a
        # Premier League simulation holds 1000 x 380 x 2 of them.
        results = np.empty((size, len(pairs), 2), dtype=np.int16)
        for simulation in range(size):
            for match, (home_id, away_id) in enumerate(pairs):
                home_goals, away_goals = self.sample(home_id, away_id, rng)
                results[simulation, match, 0] = home_goals
                results[simulation, match, 1] = away_goals
        return results
