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


def test_get_bracket(client, db_session):
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
            round="Semi-finals",
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
    assert data[0]["round"] == "Semi-finals"
    assert data[1]["round"] == "Final"
