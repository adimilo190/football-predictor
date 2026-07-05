# Zrealizowane Zadania i Obecny Stan Projektu

## Architektura i Środowisko
* [x] Inicjalizacja projektu i utworzenie folderu `football-predictor`.
* [x] Utworzenie i aktywacja wirtualnego środowiska Pythona (`venv`).
* [x] Migracja i konfiguracja silnika PostgreSQL z systemu Windows do środowiska WSL (wirtualnego Linuxa) w celu wyeliminowania błędów sieciowych ("Connection refused", "Timeout").
* [x] Konfiguracja podglądu bazy danych bezpośrednio w VS Code za pomocą wtyczki SQLTools (ominięcie problemów z pgAdmin4 na styku Windows-WSL).

## Backend (FastAPI + Baza Danych)
* [x] Instalacja kluczowych paczek: `fastapi`, `uvicorn`, `httpx`, `sqlalchemy`, `psycopg2-binary`.
* [x] Skonfigurowanie połączenia z bazą PostgreSQL (plik `database.py` z wykorzystaniem `sessionmaker` i `create_engine`).
* [x] Stworzenie pierwszego modelu tabeli SQLAlchemy (plik `models.py` -> klasa `League` przechowująca id, name, country, logo_url).
* [x] Zaimplementowanie automatycznego tworzenia brakujących tabel w bazie przy starcie serwera (`models.Base.metadata.create_all`).

## Integracja z API-Football (ETL)
* [x] Skonfigurowanie autoryzacji z zewnętrznym API (headers, API Key).
* [x] Stworzenie endpointu pobierającego (`/import-leagues`):
  * Asynchroniczne odpytanie API-Football o ligi.
  * Przetwarzanie otrzymanego pliku JSON.
  * Walidacja duplikatów (sprawdzanie po ID w naszej bazie).
  * Zapisanie nowych rekordów do bazy PostgreSQL poprzez sesję SQLAlchemy.
* [x] Stworzenie endpointu wyświetlającego (`/my-leagues`):
  * Odpytanie własnej bazy PostgreSQL i zwrócenie wszystkich zapisanych lig do przeglądarki klienta.
* **Wynik:** Sukces. Własna baza danych zasilana jest poprawnie pierwszymi danymi (zaimportowano m.in. 46 lig brytyjskich w celach testowych).

## Sesja 1 (2026-07-02) — Bezpieczeństwo, organizacja, plan
* [x] Audyt całego projektu + ocena stacku (werdykt: stack trafiony, drobne uzupełnienia opisane w `tools.md`).
* [x] Sekrety (klucz API, hasło DB) wyniesione z kodu do `.env` (`python-dotenv`); wzór w `.env.example`.
* [x] `.gitignore` (venv, `__pycache__`, `.env`, node_modules) — repo gotowe do publikacji bez wycieków.
* [x] `requirements.txt` — odtwarzalne środowisko.
* [x] Smoke test: aplikacja startuje i łączy się z bazą przez `.env`.
* [x] `instructions/ROADMAP.md` — plan 24 sesji do 30 września (kamienie milowe + ryzyka).
* [x] `CLAUDE.md` — zasady współpracy i rytuał końca sesji; logi sesji w `instructions/sessions/`.
* [x] Git: gałąź `main`, pierwszy commit.
* [x] Push na GitHub — repo istniało z wcześniejszej próby; wygenerowano nowy token, push wykonany.

## Sesja 2 (2026-07-05) — Struktura backendu, konfiguracja, schematy, Ruff
* [x] Restrukturyzacja: kod przeniesiony do pakietu `app/` (`__init__.py` + importy pakietowe `from app...`).
* [x] `app/config.py` — pydantic-settings (`Settings`) jako jedno źródło konfiguracji; usunięte `os.getenv`/`load_dotenv` i martwy `if not DATABASE_URL`.
* [x] `app/schemas.py` — `LeagueResponse` + `response_model` na `/my-leagues`; rozdzielone warstwy models (baza) vs schemas (API).
* [x] Adres API wyniesiony do konfiguracji (`settings.API_FOOTBALL_BASE_URL`).
* [x] Ruff (lint + format) skonfigurowany; kod przechodzi bez uwag; `requirements.txt` zaktualizowany.
* [x] Język w kodzie zmieniony na angielski (komentarze/docstringi); zasada zapisana w `CLAUDE.md` i pamięci Claude.
* [x] `.claude/settings.local.json` — ogólne reguły uprawnień (mniej klikania „allow"); `tools.md` — notatka o WSL/Bash.
* [x] Smoke test (`import app.main`) po każdej zmianie — zawsze OK.

