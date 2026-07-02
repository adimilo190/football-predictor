from sqlalchemy import Column, Integer, String
from database import Base

# Tworzymy klasę League, która dziedziczy po Base z naszego pliku database.py
class League(Base):
    # Tak będzie się nazywać fizyczna tabela w bazie PostgreSQL
    __tablename__ = "leagues"

    # Definiujemy kolumny tabeli
    # primary_key=True oznacza, że to unikalny identyfikator (nie mogą być dwie ligi z tym samym ID)
    id = Column(Integer, primary_key=True, index=True)
    
    # Zwykłe kolumny tekstowe na nazwę ligi, kraj i ewentualnie link do logo
    name = Column(String, index=True)
    country = Column(String)
    logo_url = Column(String)