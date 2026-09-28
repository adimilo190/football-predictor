# app/models.py
# SQLAlchemy models = the physical tables in PostgreSQL, one class per table:
# a competition (League), a club (Team), a single row of a league table (Standing)
# and a single match (Fixture).
#
# These classes describe how data is STORED. What the API gives back to the
# outside world is described separately in schemas.py - keeping the two apart
# means an internal column can never leak into a response by accident.
#
# Changing a class here does NOT change the database: the schema is migrated
# exclusively through Alembic (alembic revision --autogenerate, then upgrade).

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

    # Same choice as League and Team: reuse the API-Football id as our primary
    # key, so re-importing a match updates the existing row instead of cloning it.
    id = Column(Integer, primary_key=True, index=True)

    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    season = Column(Integer, nullable=False)

    # Round name exactly as API-Football spells it ("Quarter-finals", but also
    # "Regular Season - 5" for league matches). The bracket endpoint groups
    # matches by this value, which is why we store the label and not a number.
    round = Column(String)
    date = Column(DateTime, nullable=False)

    # A match always has two sides, so two foreign keys into the same table.
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)

    # Match status as API-Football spells it: "NS" (not started), "FT" (full
    # time), "AET" (after extra time), "PEN" (penalties), and others. This is how
    # we tell a played match from a scheduled one (see FINISHED_STATUSES).
    status = Column(String)

    # Nullable on purpose: a match that has not kicked off yet has no score.
    home_goals = Column(Integer)
    away_goals = Column(Integer)
    league = relationship("League")
    # Two FKs point at teams, so SQLAlchemy needs foreign_keys= to know
    # which column feeds which relationship (home vs away).
    home_team = relationship("Team", foreign_keys=[home_team_id])
    away_team = relationship("Team", foreign_keys=[away_team_id])
