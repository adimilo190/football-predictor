# app/prediction/poisson_model.py
# Model #1 of the three planned: the baseline Poisson predictor, wrapped in the
# PredictionModel contract from base.py. It owns no maths of its own - the
# formulas live in poisson.py and the per-team numbers come from strength.py.
# This file only connects the two and makes them behave the way every model in
# the project is expected to behave, so the simulator and the endpoints never
# have to know which model they are holding.
#
# Scope: one league, one season. A team's strength is measured against its own
# league's average, which is why supports_cross_league stays False - the number
# "1.2 attack" means nothing once the two teams come from different baselines.

import numpy as np

from app.prediction import poisson
from app.prediction.base import PredictionModel
from app.prediction.strength import match_lambdas


class PoissonModel(PredictionModel):
    """Baseline predictor: both sides' goals as independent Poisson draws."""

    name: str = "poisson"
    label: str = "Poisson Model"
    description: str = (
        "Baseline model: each team's attack and defence strength relative to "
        "its league turns into expected goals, which the Poisson distribution "
        "turns into the probability of every scoreline."
    )
    supports_cross_league: bool = False

    # Where the probability matrix stops. P(a side scores more than 10) is
    # negligible, and the matrix has to be finite. Drawing a result has no such
    # ceiling - see sample().
    MAX_GOALS: int = 10

    def _lambdas(self, home_id: int, away_id: int) -> tuple[float, float]:
        """Expected goals for both sides - the only input this model needs."""
        return match_lambdas(self.db, home_id, away_id, self.league_id, self.season)

    def _matrix(self, home_id: int, away_id: int) -> np.ndarray:
        """Probability of every scoreline up to MAX_GOALS, as a matrix."""
        lam_home, lam_away = self._lambdas(home_id, away_id)
        return poisson.score_matrix(lam_home, lam_away, self.MAX_GOALS)

    def probabilities(self, home_id: int, away_id: int) -> tuple[float, float, float]:
        home_win, draw, away_win = poisson.match_outcome_probabilities(
            self._matrix(home_id, away_id)
        )
        # float() strips numpy's float64: the contract promises plain Python
        # numbers, so nobody downstream has to clean up after this model.
        return (float(home_win), float(draw), float(away_win))

    def top_scorelines(
        self, home_id: int, away_id: int, n: int = 5
    ) -> list[tuple[int, int, float]]:
        return poisson.top_scorelines(self._matrix(home_id, away_id), n)

    def sample(
        self, home_id: int, away_id: int, rng: np.random.Generator
    ) -> tuple[int, int]:
        lam_home, lam_away = self._lambdas(home_id, away_id)
        # int() strips numpy's int64, for the same reason float() is used above.
        return (int(rng.poisson(lam_home)), int(rng.poisson(lam_away)))

    def sample_many(
        self,
        pairs: list[tuple[int, int]],
        rng: np.random.Generator,
        size: int,
    ) -> np.ndarray:
        # The lambdas are computed once per match, before any drawing happens.
        # That is the whole reason this method overrides the base version: there,
        # every single simulation would recompute them from the database.
        home_lambdas = []
        away_lambdas = []
        for home_id, away_id in pairs:
            lam_home, lam_away = self._lambdas(home_id, away_id)
            home_lambdas.append(lam_home)
            away_lambdas.append(lam_away)

        # Handed a vector of lambdas and a shape whose last dimension matches
        # it, numpy draws every column from its own lambda. Two calls replace
        # hundreds of thousands of trips through the Python interpreter.
        shape = (size, len(pairs))
        home_goals = rng.poisson(np.array(home_lambdas), size=shape)
        away_goals = rng.poisson(np.array(away_lambdas), size=shape)

        # The layout base.py promises: (simulations, matches, 2), and int16
        # because goals are small numbers and these arrays are large.
        return np.stack((home_goals, away_goals), axis=-1).astype(np.int16)
