# Tests for the API endpoints, run with pytest.
# TestClient calls the FastAPI app in-process — no running server needed.
from fastapi.testclient import TestClient

from app.main import app

# One client wrapping our app; every test reuses it to "call" endpoints.
client = TestClient(app)


def test_read_root():
    """GET / returns 200 and the welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Witaj w Football Predictor API! Serwer i baza działają."
    }


def test_get_leagues():
    """GET /leagues returns 200 and a non-empty list of leagues."""
    response = client.get("/leagues")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # Every league carries the fields the frontend relies on.
    assert "id" in data[0]
    assert "name" in data[0]


def test_get_standings():
    """GET /leagues/{id}/standings returns the table sorted by rank."""
    # 39 = Premier League (imported in session 4); season defaults to 2024.
    response = client.get("/leagues/39/standings")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # The table must start at position 1 and carry the nested team object.
    assert data[0]["rank"] == 1
    assert "team" in data[0]
    assert "name" in data[0]["team"]


def test_standings_unknown_league_returns_404():
    """An id absent from the database yields a clean 404, not a crash."""
    response = client.get("/leagues/999999/standings")
    assert response.status_code == 404
