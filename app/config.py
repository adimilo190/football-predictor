# app/config.py
# JEDNO miejsce na całą konfigurację aplikacji.
# Zamiast wołać os.getenv(...) w wielu plikach, opisujemy wszystkie ustawienia
# jako klasę Settings. Biblioteka pydantic-settings sama wczyta wartości z pliku
# .env, sprawdzi ich typy i od razu przy starcie krzyknie, jeśli czegoś brakuje.

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Wszystkie ustawienia aplikacji w jednym obiekcie.

    Każde pole poniżej odpowiada zmiennej o tej samej nazwie w pliku .env.
    """

    # --- Baza danych ---
    # ": str" to adnotacja typu — mówi: "ta wartość ma być tekstem".
    # Brak wartości domyślnej = pole WYMAGANE. Jeśli nie ma go w .env,
    # aplikacja nie wystartuje (i dobrze — od razu wiemy, co poprawić).
    DATABASE_URL: str

    # --- API-Football ---
    API_FOOTBALL_KEY: str

    # To pole MA wartość domyślną (po "="), więc jest opcjonalne w .env.
    # Jak ktoś nie poda własnego adresu, użyjemy tego.
    API_FOOTBALL_BASE_URL: str = "https://v3.football.api-sports.io"

    # model_config to instrukcja DLA pydantic-settings, skąd i jak czytać ustawienia.
    model_config = SettingsConfigDict(
        env_file=".env",            # z tego pliku wczytujemy zmienne
        env_file_encoding="utf-8",  # kodowanie pliku (polskie znaki itp.)
        extra="ignore",             # dodatkowe zmienne w .env nie wywołają błędu
    )


# Tworzymy JEDEN wspólny obiekt ustawień. W innych plikach piszemy po prostu:
#   from app.config import settings
# i sięgamy po settings.DATABASE_URL, settings.API_FOOTBALL_KEY itd.
settings = Settings()
