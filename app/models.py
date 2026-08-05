from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import DateTime
from app.database import Base


# The League class inherits from Base (defined in database.py).
class League(Base):
    # Name of the physical table in PostgreSQL.
    __tablename__ = "leagues"

    # Table columns.
    # primary_key=True marks the unique identifier (no two leagues share an ID).
    id = Column(Integer, primary_key=True, index=True)

    # Plain text columns for the league name, country and optional logo link.
    name = Column(String, index=True)
    country = Column(String)
    logo_url = Column(String)

    # Python-side navigation: league.standings returns this league's table rows.
    # This does NOT create a column — the link lives in Standing.league_id below.
    standings = relationship("Standing", back_populates="league")


class Team(Base):
    __tablename__ = "teams"

    # We reuse the API-Football team id as our primary key (same as League).
    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, index=True)
    country = Column(String)
    logo_url = Column(String)

    # No league_id here on purpose: a team plays in many competitions at once
    # (league, domestic cup, Champions League), so the team<->league link
    # is many-to-many and lives in the standings table.
    standings = relationship("Standing", back_populates="team")


class Standing(Base):
    """One row of a league table: a team's position in a league in a season."""

    __tablename__ = "standings"

    # Our own auto-incremented id (API-Football has no id for a standing row).
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys — the database guarantees these point at existing rows.
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)

    # Season is stored as its starting year, API-Football style (2024 = 2024/25).
    season = Column(Integer, nullable=False)

    # Table statistics.
    rank = Column(Integer)
    points = Column(Integer)
    played = Column(Integer)
    wins = Column(Integer)
    draws = Column(Integer)
    losses = Column(Integer)
    goals_for = Column(Integer)
    goals_against = Column(Integer)

    # Recent results as a short string, e.g. "WWDLW" (API-Football format).
    form = Column(String)

    # A team can appear at most once per league per season — re-importing
    # standings must update the existing row instead of inserting a duplicate.
    __table_args__ = (
        UniqueConstraint("league_id", "team_id", "season", name="uq_standing"),
    )

    # Python-side navigation back to the related objects.
    league = relationship("League", back_populates="standings")
    team = relationship("Team", back_populates="standings")


class Fixture(Base):
    """A single match; cups have no table, only fixtures grouped by round"""

    __tablename__ = "fixtures"
    id = Column(Integer, primary_key=True, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    season = Column(Integer, nullable=False)
    round = Column(String)
    date = Column(DateTime, nullable=False)
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    status = Column(String)
    home_goals = Column(Integer)
    away_goals = Column(Integer)
    league = relationship("League")
    # Two FKs point at teams, so SQLAlchemy needs foreign_keys= to know
    # which column feeds which relationship (home vs away).
    home_team = relationship("Team", foreign_keys=[home_team_id])
    away_team = relationship("Team", foreign_keys=[away_team_id])
