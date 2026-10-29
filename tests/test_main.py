# Tests for the API endpoints, run with pytest.
# The `client` and `db_session` fixtures come from conftest.py: `client` sends
# in-process HTTP requests to the app, `db_session` seeds data into the isolated
# in-memory test database. Each test starts from an EMPTY DB (see reset_database),
# so every test that reads data must first arrange the data it expects.
from datetime import datetime

import pytest

from app import models


def test_read_root(client):
    """GET / returns 200 and the welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Football Predictor API is running"}


def test_get_leagues(client, db_session):
    """GET /leagues returns the leagues we seeded into the test DB."""
    # Arrange: the test DB starts empty, so insert one league ourselves.
    db_session.add(models.League(id=39, name="Premier League", country="England"))
    db_session.commit()

    # Act: call the endpoint.
    response = client.get("/leagues")

    # Assert: exactly the league we seeded comes back, in the API's shape.
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 39
    assert data[0]["name"] == "Premier League"


def test_get_standings(client, db_session):
    """GET /leagues/{id}/standings returns the table sorted by rank.

    A standing nests a team, so we seed three linked rows: a league, a team,
    and the standing row that ties them together.
    """
    # Arrange
    db_session.add(models.League(id=39, name="Premier League", country="England"))
    db_session.add(models.Team(id=50, name="Manchester City", country="England"))
    db_session.add(
        models.Standing(
            league_id=39,
            team_id=50,
            season=2024,
            rank=1,
            points=90,
            played=38,
            wins=28,
            draws=6,
            losses=4,
            goals_for=90,
            goals_against=30,
            form="WWWWW",
        )
    )
    db_session.commit()

    # Act
    response = client.get("/leagues/39/standings")

    # Assert: one row, at position 1, carrying the nested team object.
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["rank"] == 1
    assert data[0]["team"]["name"] == "Manchester City"


def test_standings_unknown_league_returns_404(client):
    """An id absent from the database yields a clean 404, not a crash."""
    response = client.get("/leagues/999999/standings")
    assert response.status_code == 404


def test_get_fixtures(client, db_session):
    """GET /leagues/{id}/fixtures returns the fixtures for the specified league."""

    # Arrange
    db_session.add(models.League(id=2, name="Ekstra Klasa", country="Poland"))
    db_session.add(models.Team(id=100, name="Radomiak Radom", country="Poland"))
    db_session.add(models.Team(id=3, name="Legia Warszawa", country="Poland"))
    db_session.add(
        models.Fixture(
            id=1,
            league_id=2,
            season=2024,
            round="1",
            date=datetime(2024, 8, 1, 18, 0),
            home_team_id=100,
            away_team_id=3,
            status="F",
        )
    )
    db_session.commit()

    # Act
    response = client.get("/leagues/2/fixtures")

    # Assert: one row, at position 1, carrying the nested team object.
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 1
    assert data[0]["home_team"]["name"] == "Radomiak Radom"
    assert data[0]["away_team"]["name"] == "Legia Warszawa"


def test_get_bracket_all_stages(client, db_session):
    """GET /leagues/{id}/bracket returns the fixtures for the specified league."""

    # Arrange
    db_session.add(models.League(id=5, name="Puchar Polski", country="Poland"))
    db_session.add(models.Team(id=200, name="Lech Poznań", country="Poland"))
    db_session.add(models.Team(id=201, name="Raków Częstochowa", country="Poland"))
    db_session.add(
        models.Fixture(
            id=10,
            league_id=5,
            season=2024,
            round="Final",
            date=datetime(2024, 6, 1, 20, 0),
            home_team_id=200,
            away_team_id=201,
            status="F",
        )
    )
    db_session.add(
        models.Fixture(
            id=11,
            league_id=5,
            season=2024,
            round="Group Stage",
            date=datetime(2024, 5, 1, 20, 0),
            home_team_id=200,
            away_team_id=201,
            status="F",
        )
    )
    db_session.commit()

    # Act
    response = client.get("/leagues/5/bracket")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["round"] == "Group Stage"
    assert data[1]["round"] == "Final"


def test_get_bracket_with_knockout_only(client, db_session):
    """GET /leagues/{id}/bracket returns only knockout rounds when requested."""

    # Arrange
    db_session.add(models.League(id=6, name="Puchar Niemiec", country="Germany"))
    db_session.add(models.Team(id=300, name="Bayern Munich", country="Germany"))
    db_session.add(models.Team(id=301, name="Borussia Dortmund", country="Germany"))
    db_session.add(
        models.Fixture(
            id=20,
            league_id=6,
            season=2024,
            round="Final",
            date=datetime(2024, 6, 1, 20, 0),
            home_team_id=300,
            away_team_id=301,
            status="F",
        )
    )
    db_session.add(
        models.Fixture(
            id=21,
            league_id=6,
            season=2024,
            round="Group Stage",
            date=datetime(2024, 5, 1, 20, 0),
            home_team_id=300,
            away_team_id=301,
            status="F",
        )
    )
    db_session.commit()

    # Act
    response = client.get("/leagues/6/bracket?knockout_only=true")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["round"] == "Final"


def test_get_seasons_merges_standings_and_fixtures(client, db_session):
    """GET /leagues/{id}/seasons returns the union of seasons from standings and fixtures."""

    # Arrange
    db_session.add(models.League(id=1, name="Test League", country="Testland"))
    db_session.add(models.Team(id=50, name="Team A", country="Testland"))
    db_session.add(models.Team(id=51, name="Team B", country="Testland"))
    # Seasons in standings: 2023, 2024
    db_session.add(
        models.Standing(
            league_id=1,
            team_id=50,
            season=2023,
        )
    )
    db_session.add(
        models.Standing(
            league_id=1,
            team_id=51,
            season=2024,
        )
    )
    # Seasons in fixtures: 2024, 2025
    db_session.add(
        models.Fixture(
            id=30,
            league_id=1,
            season=2024,
            round="1",
            date=datetime(2024, 8, 1, 18, 0),
            home_team_id=50,
            away_team_id=51,
        )
    )
    db_session.add(
        models.Fixture(
            id=31,
            league_id=1,
            season=2025,
            round="1",
            date=datetime(2025, 8, 1, 18, 0),
            home_team_id=50,
            away_team_id=51,
        )
    )
    db_session.commit()

    # Act
    response = client.get("/leagues/1/seasons")

    # Assert: should return the union of seasons: [2025, 2024, 2023]
    assert response.status_code == 200
    data = response.json()
    assert data == [2025, 2024, 2023]


def test_get_team_past_matches(client, db_session):
    """GET /teams/{id}/past-matches returns the last N finished matches for a team."""

    # Arrange
    db_session.add(models.Team(id=1, name="Team A", country="Testland"))
    db_session.add(models.Team(id=2, name="Team B", country="Testland"))
    db_session.add(models.Team(id=3, name="Team C", country="Testland"))
    db_session.add(models.League(id=1, name="Test League", country="Testland"))
    db_session.add(
        models.Fixture(
            id=1,
            league_id=1,
            season=2024,
            home_team_id=1,
            away_team_id=2,
            date=datetime(2024, 8, 1, 18, 0),
            status="FT",  # Finished
            home_goals=2,
            away_goals=1,
        )
    )
    db_session.add(
        models.Fixture(
            id=2,
            league_id=1,
            season=2024,
            home_team_id=2,
            away_team_id=1,
            date=datetime(2024, 8, 10, 18, 0),
            status="FT",  # Finished
            home_goals=0,
            away_goals=3,
        )
    )
    db_session.add(
        models.Fixture(
            id=3,
            league_id=1,
            season=2024,
            home_team_id=1,
            away_team_id=3,
            date=datetime(2024, 8, 20, 18, 0),
            status="NS",  # Not started yet
        )
    )
    db_session.add(
        models.Fixture(
            id=4,
            league_id=1,
            season=2024,
            home_team_id=2,
            away_team_id=3,
            date=datetime(2024, 8, 15, 18, 0),
            status="FT",  # Finished
            home_goals=1,
            away_goals=1,
        )
    )
    db_session.commit()

    # Act
    response = client.get("/teams/1/past-matches")

    # Assert: should return the last 2 finished matches for Team A
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == 2
    assert data[1]["id"] == 1
    assert data[0]["away_team"]["name"] == "Team A"
    assert data[1]["home_team"]["name"] == "Team A"


def test_get_team_future_matches(client, db_session):
    """GET /teams/{id}/future-matches returns the next N future matches for a team."""

    # Arrange
    db_session.add(models.Team(id=1, name="Team A", country="Testland"))
    db_session.add(models.Team(id=2, name="Team B", country="Testland"))
    db_session.add(models.Team(id=3, name="Team C", country="Testland"))
    db_session.add(models.League(id=1, name="Test League", country="Testland"))
    db_session.add(
        models.Fixture(
            id=1,
            league_id=1,
            season=2024,
            home_team_id=1,
            away_team_id=2,
            date=datetime(2024, 8, 1, 18, 0),
            status="NS",  # Not started yet
        )
    )
    db_session.add(
        models.Fixture(
            id=2,
            league_id=1,
            season=2024,
            home_team_id=2,
            away_team_id=1,
            date=datetime(2024, 8, 10, 18, 0),
            status="NS",  # Not started yet
        )
    )
    db_session.add(
        models.Fixture(
            id=3,
            league_id=1,
            season=2024,
            home_team_id=1,
            away_team_id=3,
            date=datetime(2024, 8, 20, 18, 0),
            status="FT",  # Finished
            home_goals=1,
            away_goals=1,
        )
    )
    db_session.add(
        models.Fixture(
            id=4,
            league_id=1,
            season=2024,
            home_team_id=2,
            away_team_id=3,
            date=datetime(2024, 8, 15, 18, 0),
            status="NS",  # Not started yet
        )
    )
    db_session.commit()

    # Act
    response = client.get("/teams/1/future-matches")

    # Assert: should return the next 2 future matches for Team A
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == 1
    assert data[1]["id"] == 2
    assert data[0]["home_team"]["name"] == "Team A"
    assert data[1]["away_team"]["name"] == "Team A"


def test_search_teams(client, db_session):
    """GET /teams?search=... returns teams whose name contains the search phrase."""

    # Arrange
    db_session.add(models.Team(id=1, name="Manchester United", country="England"))
    db_session.add(models.Team(id=2, name="Manchester City", country="England"))
    db_session.add(models.Team(id=3, name="Liverpool", country="England"))
    db_session.commit()

    # Act: search for "ester" (case-insensitive)
    response = client.get("/teams?search=eSTEr")

    # Assert: should return the two Manchester teams
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Manchester City"
    assert data[1]["name"] == "Manchester United"

    # Act: search for "Bayern" (not in DB)
    response = client.get("/teams?search=Bayern")

    # Assert: should return an empty list
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


def test_team_not_found(client):
    """Both team-match endpoints return 404 for a non-existent team."""
    response = client.get("/teams/999999/past-matches")
    assert response.status_code == 404
    # future-matches: same guard, second function
    response = client.get("/teams/999999/future-matches")
    assert response.status_code == 404


def test_predict_returns_probabilities(client, db_session):
    """GET /predict returns 1/X/2 (summing to ~1) plus the top scorelines."""
    # Arrange: a league with two teams and their standings (the strength source).
    # Strong FC scores a lot and concedes little; Weak FC is the opposite.
    db_session.add(models.League(id=1, name="Test League", country="Testland"))
    db_session.add(models.Team(id=10, name="Strong FC", country="Testland"))
    db_session.add(models.Team(id=20, name="Weak FC", country="Testland"))
    db_session.add(
        models.Standing(
            league_id=1,
            team_id=10,
            season=2024,
            played=20,
            goals_for=40,
            goals_against=20,
        )
    )
    db_session.add(
        models.Standing(
            league_id=1,
            team_id=20,
            season=2024,
            played=20,
            goals_for=20,
            goals_against=40,
        )
    )
    db_session.commit()

    # Act
    response = client.get(
        "/predict",
        params={"home_id": 10, "away_id": 20, "league_id": 1, "season": 2024},
    )

    # Assert: valid probability split, strong home team favoured, five scorelines.
    assert response.status_code == 200
    data = response.json()
    total = data["home_win"] + data["draw"] + data["away_win"]
    assert total == pytest.approx(1.0, abs=1e-4)
    assert data["home_win"] > data["away_win"]
    assert len(data["top_scores"]) == 5
    assert "home_goals" in data["top_scores"][0]
    assert "probability" in data["top_scores"][0]


def test_predict_unknown_team_returns_404(client, db_session):
    """A team without standings in the league/season yields 404, not a crash."""
    db_session.add(models.League(id=1, name="Test League", country="Testland"))
    db_session.add(models.Team(id=10, name="Strong FC", country="Testland"))
    db_session.add(
        models.Standing(
            league_id=1,
            team_id=10,
            season=2024,
            played=20,
            goals_for=40,
            goals_against=20,
        )
    )
    db_session.commit()

    response = client.get(
        "/predict",
        params={"home_id": 10, "away_id": 99999, "league_id": 1, "season": 2024},
    )
    assert response.status_code == 404


# --- GET /leagues/{id}/simulate -------------------------------------------
# Three helpers, because every simulation test needs the same league, and the
# interesting part of each test is what it leaves OUT: a missing strength
# season, a missing fixture list, an impossible iteration count.


def add_simulation_league(db_session):
    """League 1 with three teams, shared by the simulation tests below."""
    db_session.add(models.League(id=1, name="Test League", country="Testland"))
    db_session.add(models.Team(id=10, name="Strong FC", country="Testland"))
    db_session.add(models.Team(id=20, name="Mid FC", country="Testland"))
    db_session.add(models.Team(id=30, name="Weak FC", country="Testland"))


def add_standing(db_session, team_id, season, rank, points, goals_for, goals_against):
    """One standings row; points are set explicitly because the simulator adds to them."""
    db_session.add(
        models.Standing(
            league_id=1,
            team_id=team_id,
            season=season,
            rank=rank,
            played=20,
            points=points,
            goals_for=goals_for,
            goals_against=goals_against,
        )
    )


def add_fixture(db_session, fixture_id, home_id, away_id, season, day):
    """A scheduled match - status NS is what the simulator picks up."""
    db_session.add(
        models.Fixture(
            id=fixture_id,
            league_id=1,
            season=season,
            round="Regular Season - 1",
            date=datetime(season, 8, day, 15, 0),
            home_team_id=home_id,
            away_team_id=away_id,
            status="NS",
        )
    )


def add_full_round(db_session, season):
    """Each pair home and away once, so home advantage favours nobody."""
    pairs = [(10, 20), (20, 10), (20, 30), (30, 20), (10, 30), (30, 10)]
    for index, (home_id, away_id) in enumerate(pairs):
        add_fixture(db_session, 100 + index, home_id, away_id, season, index + 1)


def test_simulate_returns_a_probability_for_every_place(client, db_session):
    """Each team gets one probability per position, and they sum to 1."""
    add_simulation_league(db_session)
    add_standing(db_session, 10, 2024, 1, 40, 50, 20)
    add_standing(db_session, 20, 2024, 2, 30, 35, 35)
    add_standing(db_session, 30, 2024, 3, 20, 20, 50)
    add_full_round(db_session, 2024)
    db_session.commit()

    response = client.get(
        "/leagues/1/simulate",
        params={"season": 2024, "strength_season": 2024, "iterations": 200, "seed": 42},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "poisson"
    assert data["iterations"] == 200
    assert data["matches_simulated"] == 6
    assert len(data["teams"]) == 3
    for team in data["teams"]:
        assert len(team["position_probabilities"]) == 3
        assert sum(team["position_probabilities"]) == pytest.approx(1.0, abs=1e-9)
        # The nested team object is what lets the frontend draw a table row.
        assert team["team"]["name"] in {"Strong FC", "Mid FC", "Weak FC"}


def test_simulate_takes_strength_from_the_previous_season(client, db_session):
    """Without strength_season, strengths come from season - 1, not the table's own season.

    The 2024 table is deliberately flat, so if the endpoint measured strength
    there, no team could pull ahead. The gap can only come from 2023.
    """
    add_simulation_league(db_session)
    for team_id in (10, 20, 30):
        add_standing(db_session, team_id, 2024, 1, 10, 10, 10)
    add_standing(db_session, 10, 2023, 1, 60, 60, 10)
    add_standing(db_session, 20, 2023, 2, 30, 30, 30)
    add_standing(db_session, 30, 2023, 3, 10, 10, 60)
    add_full_round(db_session, 2024)
    db_session.commit()

    response = client.get(
        "/leagues/1/simulate",
        params={"season": 2024, "iterations": 300, "seed": 42},
    )

    assert response.status_code == 200
    by_name = {team["team"]["name"]: team for team in response.json()["teams"]}
    assert by_name["Strong FC"]["average_points"] > by_name["Weak FC"]["average_points"]
    assert by_name["Strong FC"]["position_probabilities"][0] > 0.5


def test_simulate_without_a_strength_season_in_the_database_returns_404(
    client, db_session
):
    """Season 2023 holds nothing, so there is no average to measure teams against."""
    add_simulation_league(db_session)
    for team_id in (10, 20, 30):
        add_standing(db_session, team_id, 2024, 1, 10, 10, 10)
    add_full_round(db_session, 2024)
    db_session.commit()

    response = client.get("/leagues/1/simulate", params={"season": 2024})

    assert response.status_code == 404
    assert "2023" in response.json()["detail"]


def test_simulate_with_no_fixtures_left_returns_the_current_table(client, db_session):
    """A finished season has nothing to draw, so the table is already certain."""
    add_simulation_league(db_session)
    add_standing(db_session, 10, 2024, 1, 40, 50, 20)
    add_standing(db_session, 20, 2024, 2, 30, 35, 35)
    add_standing(db_session, 30, 2024, 3, 20, 20, 50)
    db_session.commit()

    response = client.get(
        "/leagues/1/simulate",
        params={"season": 2024, "strength_season": 2024, "iterations": 10},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["matches_simulated"] == 0
    assert data["teams"][0]["team"]["name"] == "Strong FC"
    assert data["teams"][0]["position_probabilities"] == [1.0, 0.0, 0.0]


def test_simulate_same_seed_returns_the_same_table(client, db_session):
    """The seed parameter is wired through, so a run can be reproduced exactly."""
    add_simulation_league(db_session)
    add_standing(db_session, 10, 2024, 1, 40, 50, 20)
    add_standing(db_session, 20, 2024, 2, 30, 35, 35)
    add_standing(db_session, 30, 2024, 3, 20, 20, 50)
    add_full_round(db_session, 2024)
    db_session.commit()

    params = {"season": 2024, "strength_season": 2024, "iterations": 100, "seed": 7}
    first = client.get("/leagues/1/simulate", params=params).json()
    second = client.get("/leagues/1/simulate", params=params).json()

    assert first == second


def test_simulate_unknown_league_returns_404(client):
    """No standings at all means nothing to simulate.

    The message is asserted, not just the status: without the guard on an empty
    table this request still ends in a 404, but from LeagueStrength further
    down, which would hide the fact that the guard had gone.
    """
    response = client.get("/leagues/999/simulate", params={"season": 2024})

    assert response.status_code == 404
    assert "999" in response.json()["detail"]
    assert "standings" in response.json()["detail"].lower()


def test_simulate_with_standings_only_in_the_strength_season_returns_404(
    client, db_session
):
    """Strengths are there, but the season being simulated has no table at all.

    This is the case the empty-table guard exists for: strengths resolve fine
    from 2023, so without it the endpoint answers 200 with an empty team list -
    a success that tells the caller nothing.
    """
    add_simulation_league(db_session)
    add_standing(db_session, 10, 2023, 1, 40, 50, 20)
    add_standing(db_session, 20, 2023, 2, 30, 35, 35)
    add_standing(db_session, 30, 2023, 3, 20, 20, 50)
    db_session.commit()

    response = client.get("/leagues/1/simulate", params={"season": 2024})

    assert response.status_code == 404
    assert "standings" in response.json()["detail"].lower()


def test_simulate_unknown_model_returns_400(client, db_session):
    """A model name outside the registry is a bad request, not a missing resource."""
    add_simulation_league(db_session)
    add_standing(db_session, 10, 2024, 1, 40, 50, 20)
    add_standing(db_session, 20, 2024, 2, 30, 35, 35)
    add_standing(db_session, 30, 2024, 3, 20, 20, 50)
    db_session.commit()

    response = client.get(
        "/leagues/1/simulate",
        params={"season": 2024, "strength_season": 2024, "model": "xgboost"},
    )

    assert response.status_code == 400
    assert "xgboost" in response.json()["detail"]


def test_simulate_rejects_an_impossible_iteration_count(client):
    """The bounds on iterations are what let the simulator assume a sane number."""
    for iterations in (0, 999999):
        response = client.get(
            "/leagues/1/simulate", params={"season": 2024, "iterations": iterations}
        )
        assert response.status_code == 422
