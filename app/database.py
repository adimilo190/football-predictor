# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Całą konfigurację bierzemy z jednego miejsca — obiektu settings.
# Nie ma już load_dotenv() ani os.getenv() — zrobił to za nas pydantic-settings,
# który PRZY STARCIE sprawdził, że DATABASE_URL istnieje (inaczej aplikacja
# w ogóle by nie wstała). Dlatego stare ręczne "if not ...: raise" jest zbędne.
from app.config import settings

# 1. ENGINE: "silnik" — to on fizycznie łączy się z bazą.
#    Connection String (adres bazy) czytamy przez settings.DATABASE_URL.
engine = create_engine(settings.DATABASE_URL)

# 2. SESSION: "fabryka sesji". Sesja to pojedyncza "rozmowa" z bazą
#    (np. kiedy zapisujemy listę lig).
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. BASE: klasa bazowa. Nasze modele (np. League) dziedziczą po niej,
#    a SQLAlchemy zamienia je na fizyczne tabele w PostgreSQL.
Base = declarative_base()
