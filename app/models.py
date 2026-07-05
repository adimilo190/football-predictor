from sqlalchemy import Column, Integer, String
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
