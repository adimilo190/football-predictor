# app/database.py
# The project's one and only door to PostgreSQL. It builds the three SQLAlchemy
# objects the rest of the code needs - the engine (physical connection), the
# session factory (one short conversation with the database) and Base (the class
# our models inherit from) - plus the get_db dependency that hands every endpoint
# its own session. Nothing else in the project opens a connection itself, so
# there is a single place to look when connection behaviour needs to change.

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# We take the whole configuration from a single place - the settings object.
# No more load_dotenv() or os.getenv() - pydantic-settings did that for us and
# already verified at startup that DATABASE_URL exists (otherwise the app would
# not have started). That is why the old manual "if not ...: raise" is redundant.
from app.config import settings

# 1. ENGINE: the "engine" - it physically connects to the database.
#    The Connection String (database address) comes from settings.DATABASE_URL.
#
#    The two pool options matter in production, not locally. Our managed database
#    (Neon) suspends its compute after a few minutes without traffic, and the free
#    hosting plan puts the whole web service to sleep too - so connections sitting
#    idle in the pool get closed on the server side while we still believe we hold
#    them. A local PostgreSQL never does that, which is exactly why this class of
#    bug only ever shows up after deploying.
#      pool_pre_ping: test a pooled connection with a tiny query before handing it
#        out; if it is dead, discard it and open a fresh one instead of raising
#        "server closed the connection unexpectedly" in the user's face.
#      pool_recycle: proactively drop connections older than 5 minutes (the same
#        order of magnitude as the database's idle timeout), so they are replaced
#        before they have a chance to go stale.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
)

# 2. SESSION: a "session factory". A session is a single "conversation" with the
#    database (e.g. when we save a list of leagues).
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. BASE: the base class. Our models (e.g. League) inherit from it, and
#    SQLAlchemy turns them into physical tables in PostgreSQL.
Base = declarative_base()


# 4. DB DEPENDENCY: open a session for one request, and guarantee it is closed.
#    It lives HERE (not in main.py) so the routers can import it without an import
#    cycle — main.py imports the routers, so the routers must not import from main.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
