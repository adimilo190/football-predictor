# Unit tests for the season simulator. No database needed: simulate_season takes
# a model OBJECT, so a stand-in that ignores the database satisfies it just as
# well as PoissonModel does. That is the practical payoff of the contract in
# base.py - the simulator can be tested without a single table.
#
# Both stand-ins below leave sample_many to the base class on purpose, so these
# tests also cover the default implementation that every future model inherits.

import numpy as np
import pytest

from app.prediction.base import PredictionModel
from app.prediction.simulation import TeamStart, final_table, simulate_season


class AlwaysHomeWinsModel(PredictionModel):
    """Every match ends 1:0 for the home side - no randomness at all."""

    def __init__(self):
        pass

    def probabilities(self, home_id: int, away_id: int) -> tuple[float, float, float]:
        return (1.0, 0.0, 0.0)

    def sample(
        self, home_id: int, away_id: int, rng: np.random.Generator
    ) -> tuple[int, int]:
        return (1, 0)


class RandomGoalsModel(PredictionModel):
    """Zero to three goals a side, drawn from the generator it is handed."""

    def __init__(self):
        pass

    def probabilities(self, home_id: int, away_id: int) -> tuple[float, float, float]:
        # The simulator never asks for these, and inventing numbers here would
        # make a future bug look like a passing test.
        raise NotImplementedError

    def sample(
        self, home_id: int, away_id: int, rng: np.random.Generator
    ) -> tuple[int, int]:
        return (int(rng.integers(0, 4)), int(rng.integers(0, 4)))


def three_teams() -> list[TeamStart]:
    """A three-team table whose order deliberately differs from its team ids.

    Team 3 leads, team 1 is second, team 2 is last. That cycle matters: with a
    table already sorted by team id the counting matrix comes out symmetric, and
    a transposed matrix - rank_counts[place][team] instead of the other way
    round - would pass every row and column check there is.
    """
    return [
        TeamStart(team_id=1, points=6, goals_for=8, goals_against=6),
        TeamStart(team_id=2, points=3, goals_for=5, goals_against=9),
        TeamStart(team_id=3, points=9, goals_for=10, goals_against=4),
    ]


ALL_PAIRS = [(1, 2), (2, 3), (3, 1), (2, 1), (3, 2), (1, 3)]


def test_position_probabilities_sum_to_one():
    """Every team ends somewhere, so its row of the matrix sums to 1."""
    outcomes = simulate_season(
        RandomGoalsModel(),
        ALL_PAIRS,
        three_teams(),
        np.random.default_rng(42),
        iterations=200,
    )

    assert len(outcomes) == 3
    for outcome in outcomes:
        assert sum(outcome.position_probabilities) == pytest.approx(1.0, abs=1e-9)


def test_every_place_is_taken_exactly_once():
    """Each position goes to one team per simulation, so columns sum to 1 too.

    This catches a place counted twice or not at all. It cannot catch a
    transposed matrix - both sums survive transposition - which is what the
    cyclic table in three_teams() and the no-fixtures test below are for.
    """
    outcomes = simulate_season(
        RandomGoalsModel(),
        ALL_PAIRS,
        three_teams(),
        np.random.default_rng(42),
        iterations=200,
    )

    for place in range(3):
        column = 0.0
        for outcome in outcomes:
            column += outcome.position_probabilities[place]
        assert column == pytest.approx(1.0, abs=1e-9)


def test_same_seed_gives_the_same_result():
    """A seeded generator makes the whole simulation reproducible."""
    first = simulate_season(
        RandomGoalsModel(),
        ALL_PAIRS,
        three_teams(),
        np.random.default_rng(42),
        iterations=100,
    )
    second = simulate_season(
        RandomGoalsModel(),
        ALL_PAIRS,
        three_teams(),
        np.random.default_rng(42),
        iterations=100,
    )

    for one, other in zip(first, second):
        assert one.team_id == other.team_id
        assert one.average_points == other.average_points
        assert one.position_probabilities == other.position_probabilities


def test_starting_table_is_not_modified():
    """The simulation adds points to a copy, never to the table it was given.

    This is the safety net for dropping frozen=True: nothing else stops the
    loop from writing results into the caller's objects. A copy accidentally
    hoisted out of the simulation loop is a different bug and leaves start
    untouched too - the average_points assertion in the title test catches
    that one.
    """
    start = three_teams()
    before = []
    for team in start:
        before.append((team.team_id, team.points, team.goals_for, team.goals_against))

    simulate_season(
        RandomGoalsModel(),
        ALL_PAIRS,
        start,
        np.random.default_rng(42),
        iterations=50,
    )

    after = []
    for team in start:
        after.append((team.team_id, team.points, team.goals_for, team.goals_against))
    assert after == before


def test_team_that_wins_every_match_takes_the_title():
    """A side that is always at home against a model that always wins at home."""
    start = [
        TeamStart(team_id=1, points=0, goals_for=0, goals_against=0),
        TeamStart(team_id=2, points=0, goals_for=0, goals_against=0),
        TeamStart(team_id=3, points=0, goals_for=0, goals_against=0),
    ]
    pairs = [(1, 2), (1, 3)]

    outcomes = simulate_season(
        AlwaysHomeWinsModel(), pairs, start, np.random.default_rng(42), iterations=10
    )

    assert outcomes[0].team_id == 1
    assert outcomes[0].position_probabilities[0] == 1.0
    # Two wins and nothing else. This is also what fails if the copy of the
    # starting table is hoisted out of the simulation loop: the points would
    # pile up across simulations instead of restarting from zero each time.
    assert outcomes[0].average_points == 6.0
    # Nobody else ever finishes first.
    for outcome in outcomes[1:]:
        assert outcome.position_probabilities[0] == 0.0


def test_no_fixtures_left_returns_the_current_table():
    """With nothing to play, the table is already final and certain.

    Covers both ends of a season: a league that has not kicked off has no
    standings to add to, and one that is over has no fixtures left.
    """
    outcomes = simulate_season(
        RandomGoalsModel(), [], three_teams(), np.random.default_rng(42), iterations=10
    )

    # Sorted by average points, which here is the starting table: 3, 1, 2.
    assert [outcome.team_id for outcome in outcomes] == [3, 1, 2]
    assert outcomes[0].average_points == 9.0
    # Every team is certain of its own place and of no other. Because the table
    # order differs from the team order, this also pins down which way round
    # rank_counts is indexed.
    for place, outcome in enumerate(outcomes):
        for other in range(3):
            expected = 1.0 if other == place else 0.0
            assert outcome.position_probabilities[other] == expected


def test_fixture_with_unknown_team_raises():
    """Fixtures and standings come from different queries, so they can disagree."""
    with pytest.raises(ValueError):
        simulate_season(
            RandomGoalsModel(),
            [(1, 99)],
            three_teams(),
            np.random.default_rng(42),
            iterations=10,
        )


def test_final_table_breaks_a_points_tie_on_goal_difference():
    """Equal points: the better goal difference finishes above."""
    order = final_table(points=[10, 10], goals_for=[5, 3], goals_against=[4, 0])
    assert order == [1, 0]


def test_final_table_breaks_a_goal_difference_tie_on_goals_scored():
    """Equal points and equal difference: more goals scored finishes above."""
    order = final_table(points=[10, 10], goals_for=[5, 3], goals_against=[2, 0])
    assert order == [0, 1]
