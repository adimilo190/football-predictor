# Tests for the API endpoints, run with pytest.
# The `client` and `db_session` fixtures come from conftest.py: `client` sends
# in-process HTTP requests to the app, `db_session` seeds data into the isolated
# in-memory test database. Each test starts from an EMPTY DB (see reset_database),
# so every test that reads data must first arrange the data it expects.
from datetime import datetime

from app import models


def test_read_root(client):
    """GET / returns 200 and the welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Witaj w Football Predictor API! Serwer i baza działają."
    }


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
