import math
import numpy as np


def poisson_pmf(lam: float, k: int) -> float:
    """Probability of exactly `k` goals when the expected number is `lam`.

    Poisson PMF(Probability Mass Function):  P(k) = lam^k * e^(-lam) / k!
    """
    probability = pow(lam, k) * pow(math.e, -lam) / math.factorial(k)

    return probability


def goal_distribution(lam: float, max_goals: int) -> np.ndarray:
    """Vector of goal probabilities [P(0), P(1), ..., P(max_goals)] for `lam`."""
    probabilities = []
    for k in range(max_goals + 1):
        probabilities.append(poisson_pmf(lam, k))
    probabilities = np.array(probabilities)
    return probabilities


def score_matrix(lam_home: float, lam_away: float, max_goals: int) -> np.ndarray:
    """Matrix M[i, j] = P(home scores i AND away scores j), assuming independence."""
    home_probs = goal_distribution(lam_home, max_goals)
    away_probs = goal_distribution(lam_away, max_goals)

    matrix = np.outer(home_probs, away_probs)
    # Truncating at max_goals drops a tiny tail, so the raw matrix sums to a bit
    # under 1. Normalise (divide by the total) so the outcome probabilities add
    # up to exactly 1 — matters for the 1/X/2 bars in the UI.
    return matrix / matrix.sum()


def match_outcome_probabilities(matrix: np.ndarray) -> tuple[float, float, float]:
    """From a score matrix, return (P home win, P draw, P away win).

    Row i = home goals, column j = away goals.
    """

    home_win = np.tril(matrix, -1).sum()
    draw = np.trace(matrix)
    away_win = np.triu(matrix, 1).sum()
    return (home_win, draw, away_win)


def top_scorelines(matrix: np.ndarray, n: int = 5) -> list[tuple[int, int, float]]:
    """The n most likely scorelines as (home_goals, away_goals, probability).

    Row i = home goals, column j = away goals. We flatten the matrix into a list
    of (i, j, prob), sort by probability descending, and keep the top n.
    """
    scorelines = []
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            scorelines.append((i, j, float(matrix[i, j])))
    scorelines.sort(key=lambda line: line[2], reverse=True)
    return scorelines[:n]
