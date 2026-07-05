# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# We take the whole configuration from a single place - the settings object.
# No more load_dotenv() or os.getenv() - pydantic-settings did that for us and
# already verified at startup that DATABASE_URL exists (otherwise the app would
# not have started). That is why the old manual "if not ...: raise" is redundant.
from app.config import settings

# 1. ENGINE: the "engine" - it physically connects to the database.
#    The Connection String (database address) comes from settings.DATABASE_URL.
engine = create_engine(settings.DATABASE_URL)

# 2. SESSION: a "session factory". A session is a single "conversation" with the
#    database (e.g. when we save a list of leagues).
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. BASE: the base class. Our models (e.g. League) inherit from it, and
#    SQLAlchemy turns them into physical tables in PostgreSQL.
Base = declarative_base()
