import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Wczytuje zmienne z pliku .env do środowiska procesu (os.environ).
# Dzięki temu hasła i klucze NIE siedzą w kodzie, który trafia na GitHuba.
load_dotenv()

# To jest tzw. Connection String - adres, pod którym Python znajdzie Twoją bazę.
# Format to: postgresql://użytkownik:hasło@serwer:port/nazwa_bazy
# Wartość trzymamy w pliku .env (wzór do skopiowania: .env.example).
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError("Brak zmiennej DATABASE_URL - utwórz plik .env na podstawie .env.example")

# 1. ENGINE: Tworzymy "silnik" - to on wykonuje ciężką pracę i fizycznie łączy się z bazą
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 2. SESSION: Tworzymy "fabrykę sesji". 
# Sesja to pojedyncza "rozmowa" z bazą (np. kiedy będziemy chcieli zapisać listę lig)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. BASE: Klasa bazowa. Za chwilę użyjemy jej do tworzenia klas w Pythonie, 
# które SQLAlchemy automatycznie zamieni na tabele w PostgreSQL.
Base = declarative_base()