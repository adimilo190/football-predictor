# tests/conftest.py
# Shared pytest configuration and test-only database wiring.
# pytest auto-discovers this file, so anything defined here is available to
# every test in the tests/ folder without importing it explicitly.

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Importing models has a SIDE EFFECT: it registers every model class on
# Base.metadata. create_all() below relies on that registry to know which
# tables to build — without this import the metadata is empty and create_all()
# would silently create nothing. The import looks unused, hence the noqa.
from app import models  # noqa: F401
from app.database import Base
from app.main import app, get_db

# 1. TEST ENGINE — a throwaway SQLite database that lives entirely in RAM.
#    Completely separate from the real PostgreSQL engine in app/database.py,
#    so the tests never read from or write to the development data.
engine = create_engine(
    "sqlite:///:memory:",
    # SQLite refuses to use a connection from a different thread than the one
    # that opened it. TestClient serves each request on a separate thread, so
    # we relax that check — safe within a single-process test run.
    connect_args={"check_same_thread": False},
    # Each new connection to ":memory:" gets its OWN fresh, empty database.
    # A normal pool opens several connections, so the test and the endpoint
    # would end up looking at different empty databases. StaticPool keeps ONE
    # shared connection for the whole run, so everyone sees the data we insert.
    poolclass=StaticPool,
)

# 2. TEST SESSION FACTORY — identical settings to SessionLocal in
#    app/database.py, but bound to the in-memory test engine instead of
#    PostgreSQL. This is what makes the isolation actually happen.
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 3. SESSION OVERRIDE — a drop-in replacement for the app's get_db dependency.
def override_get_db():
    """Drop-in replacement for get_db, yielding a session bound to the test DB."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# 4. Register the swap: whenever an endpoint asks for get_db, FastAPI now calls
#    override_get_db instead, so every request runs against the in-memory DB.
app.dependency_overrides[get_db] = override_get_db


# 5. ISOLATION — give every test a clean database. autouse=True means pytest runs
#    this automatically for EVERY test, so no test can be polluted by data left
#    behind by another. Tables are built before the test and dropped afterwards.
@pytest.fixture(autouse=True)
def reset_database():
    """Create all tables before each test, drop them all afterwards."""
    Base.metadata.create_all(bind=engine)  # before: fresh, empty tables
    yield  # the test runs at this point
    Base.metadata.drop_all(bind=engine)  # after: wipe everything for the next test


# 6. Reusable client fixture: a test gets it by taking `client` as an argument.
@pytest.fixture
def client():
    """A TestClient wrapping the app; endpoints it calls hit the in-memory DB."""
    return TestClient(app)


# 7. Session for ARRANGING data: a test takes `db_session`, inserts rows and
#    commits them, so the endpoint under test can then read them back.
@pytest.fixture
def db_session():
    """A session tests use to seed data directly into the in-memory DB."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
