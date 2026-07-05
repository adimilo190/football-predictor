from fastapi import FastAPI, Depends
import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app import models
from app.database import engine, SessionLocal

# Tworzymy tabele (jeśli jeszcze ich nie ma)
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- KONFIGURACJA API ---
API_KEY = settings.API_FOOTBALL_KEY
HEADERS = {"x-apisports-key": API_KEY}

# --- FUNKCJA POMOCNICZA BAZY DANYCH ---
# Otwiera bezpieczne połączenie (sesję) z bazą na czas trwania zapytania i zamyka po wszystkim
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Witaj w Football Predictor API! Serwer i baza działają."}

# --- 1. ENDPOINT POBIERAJĄCY Z API I ZAPISUJĄCY DO BAZY ---
@app.get("/import-leagues")
async def import_leagues(db: Session = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        # Pukamy do kelnera z API-Football
        response = await client.get(
            f"{settings.API_FOOTBALL_BASE_URL}/leagues",
            headers=HEADERS,
            params={"country": "England"} # Zostajemy przy Anglii dla testu
        )
        data = response.json()
        
        # API-Football trzyma właściwe dane w kluczu "response"
        leagues_data = data.get("response", [])
        
        added_count = 0
        
        # Przechodzimy pętlą przez każdą ligę, którą zwróciło API
        for item in leagues_data:
            league_info = item["league"]
            country_info = item["country"]
            
            # Sprawdzamy, czy liga o tym ID już u nas jest, żeby nie robić duplikatów!
            existing_league = db.query(models.League).filter(models.League.id == league_info["id"]).first()
            
            if not existing_league:
                # Jeśli jej nie ma, tworzymy nowy "obiekt" na podstawie naszego modelu
                new_league = models.League(
                    id=league_info["id"],
                    name=league_info["name"],
                    country=country_info["name"],
                    logo_url=league_info["logo"]
                )
                db.add(new_league) # Dodajemy do "koszyka"
                added_count += 1
                
        db.commit() # Płacimy za koszyk (zapisujemy wszystkie zmiany fizycznie w bazie!)
        
        return {"message": f"Sukces! Zapisano {added_count} nowych lig do Twojej bazy."}

# --- 2. ENDPOINT WYŚWIETLAJĄCY TWOJĄ WŁASNĄ BAZĘ ---
@app.get("/my-leagues")
def get_my_leagues(db: Session = Depends(get_db)):
    # To zapytanie to czysty Python, a SQLAlchemy samo tłumaczy to na: SELECT * FROM leagues;
    leagues = db.query(models.League).all()
    return leagues