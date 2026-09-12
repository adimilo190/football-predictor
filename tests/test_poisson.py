# Unit tests for the pure Poisson math. No database needed — these functions
# take numbers and return numbers, so we assert against hand-computed values
# (the same ones we verified by hand while building the model).
import pytest

from app.prediction.poisson import (
    goal_distribution,
    match_outcome_probabilities,
    poisson_pmf,
    score_matrix,
    top_scorelines,
)


def test_poisson_pmf_matches_known_values():
    """PMF for lambda=1.4 matches hand-computed probabilities."""
    assert poisson_pmf(1.4, 0) == pytest.approx(0.2466, abs=1e-3)
    assert poisson_pmf(1.4, 1) == pytest.approx(0.3452, abs=1e-3)
    assert poisson_pmf(1.4, 2) == pytest.approx(0.2417, abs=1e-3)


def test_goal_distribution_sums_to_one():
    """A distribution is a probability vector, so with a high cap it sums to ~1."""
    dist = goal_distribution(1.4, 10)
    assert len(dist) == 11  # goals 0..10 inclusive
    assert dist.sum() == pytest.approx(1.0, abs=1e-4)


def test_score_matrix_shape_and_cell():
    """Matrix is (max+1)x(max+1), sums to ~1, and cell [1,0] is the 1:0 chance."""
    matrix = score_matrix(1.96, 0.95, 10)
    assert matrix.shape == (11, 11)
    assert matrix.sum() == pytest.approx(1.0, abs=1e-4)
    assert matrix[1, 0] == pytest.approx(0.107, abs=1e-3)


def test_match_outcome_probabilities_split_and_sum():
    """1/X/2 sum to ~1 and match the theory (61/21/18) for lambdas 1.96 vs 0.95."""
    home, draw, away = match_outcome_probabilities(score_matrix(1.96, 0.95, 10))
    assert home + draw + away == pytest.approx(1.0, abs=1e-4)
    assert home == pytest.approx(0.61, abs=0.01)
    assert draw == pytest.approx(0.21, abs=0.01)
    assert away == pytest.approx(0.18, abs=0.01)


def test_top_scorelines_sorted_and_capped():
    """Returns exactly n scorelines, ordered by probability descending."""
    top = top_scorelines(score_matrix(1.96, 0.95, 10), 5)
    assert len(top) == 5
    probs = [probability for _, _, probability in top]
    assert probs == sorted(probs, reverse=True)
