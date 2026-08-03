# Struktura projektu — mapa plików i folderów

> Streszczenie całego projektu w jednym miejscu: co jest w każdym pliku/folderze i po co.
> **Ten plik aktualizujemy przy każdej zmianie struktury** (nowy plik/folder = nowy wpis tutaj).
> Stan na: Sesja 5 (2026-08-03).

---

## Katalog główny

| Plik / folder | Co to jest i po co |
|---|---|
| `app/` | **Cały kod backendu** (pakiet Pythona) — szczegóły niżej |
| `tests/` | **Testy pytest** (`test_main.py`) — sprawdzają endpointy przez `TestClient`, bez uruchamiania serwera. `__init__.py` sprawia, że pytest dokłada katalog projektu do `sys.path` |
| `alembic/` + `alembic.ini` | **Migracje bazy danych** — szczegóły niżej |
| `instructions/` | **Dokumentacja projektu** (plany, logi, decyzje) — szczegóły niżej |
| `venv/` | Wirtualne środowisko Pythona (izolowane paczki projektu). NIE w gicie. Używamy `venv/bin/python`, `venv/bin/pip` |
| `.env` | **SEKRETY**: hasło do bazy (`DATABASE_URL`), klucz API (`API_FOOTBALL_KEY`). NIE w gicie — nigdy nie commitować! |
| `.env.example` | Wzór pliku `.env` bez prawdziwych wartości — jest w gicie, żeby każdy wiedział, jakie zmienne trzeba ustawić |
| `.gitignore` | Lista rzeczy, których git ma NIE śledzić (venv, `__pycache__`, `.env`, node_modules) |
| `requirements.txt` | Zamrożone wersje wszystkich paczek Pythona — `pip install -r requirements.txt` odtwarza środowisko. Aktualizowany po każdej instalacji (`pip freeze`) |
| `CLAUDE.md` | Zasady współpracy z Claude: tryb nauki, rytm pracy (jeden krok naraz), rytuał końca sesji, szczegóły środowiska (WSL, venv, PostgreSQL) |
| `.claude/` | Ustawienia Claude Code dla tego projektu (`settings.local.json` — uprawnienia narzędzi) |
| `.git/` | Wewnętrzna baza gita (historia commitów). Nie ruszamy ręcznie |
| `__pycache__/`, `.ruff_cache/`, `.pytest_cache/` | Automatyczne cache Pythona / Ruffa / pytest — można bezpiecznie skasować, odtworzą się same. NIE w gicie |

---

## `app/` — kod backendu (FastAPI)

Pakiet Pythona (ma `__init__.py`). Warstwy od spodu do góry:

| Plik | Co robi |
|---|---|
| `__init__.py` | Pusty plik, który mówi Pythonowi „ten folder to pakiet" — dzięki niemu działają importy `from app...` |
| `config.py` | **Jedno źródło konfiguracji.** Klasa `Settings` (pydantic-settings) wczytuje `.env`, waliduje i głośno krzyczy na starcie, jeśli czegoś brakuje. Reszta kodu robi `from app.config import settings` |
| `database.py` | **Połączenie z PostgreSQL**: `engine` (fizyczne połączenie), `SessionLocal` (fabryka sesji — jedna sesja = jedna „rozmowa" z bazą), `Base` (klasa bazowa, z której dziedziczą modele) |
| `models.py` | **Modele SQLAlchemy = tabele w bazie**: `League` (rozgrywki), `Team` (drużyna — celowo bez przypisania do ligi, bo gra w wielu rozgrywkach), `Standing` (wiersz tabeli ligowej: liga + drużyna + sezon + statystyki; klucze obce i blokada duplikatów) |
| `schemas.py` | **Schematy Pydantic = kontrakt API**: co endpointy zwracają na zewnątrz — `LeagueResponse`, `TeamResponse`, `StandingResponse` (ten ostatni z zagnieżdżoną drużyną). Osobna warstwa od `models.py`: baza może mieć więcej pól niż pokazujemy światu |
| `constants.py` | **Stałe biznesowe**: `TARGET_LEAGUE_IDS` — ID 13 śledzonych rozgrywek (6 lig + 6 pucharów + LM), rozbite na grupy; `DEFAULT_SEASON = 2024` |
| `main.py` | **Serce API**: tworzy aplikację FastAPI i definiuje endpointy — `GET /` (test), `POST /import-leagues` i `POST /import-standings` (ETL z API-Football), `GET /leagues` (lista lig), `GET /leagues/{id}/standings` (tabela ligowa, sort po `rank`, `joinedload`). Dokumentacja interaktywna: `/docs` (Swagger UI) |

**Przepływ danych:** `.env` → `config.py` → `database.py` → `models.py` → (`schemas.py` +) `main.py`.

---

## `tests/` — testy automatyczne (pytest)

| Plik | Co robi |
|---|---|
| `__init__.py` | Robi z `tests/` pakiet — efekt uboczny: pytest dokłada katalog projektu do `sys.path`, więc działa `from app.main import app` |
| `test_main.py` | Testy endpointów przez `TestClient` (woła API bez uruchamiania serwera): `/`, `/leagues`, `/leagues/{id}/standings` (m.in. `rank==1` i zagnieżdżona drużyna), błędne id → 404 |

**Uruchomienie:** `venv/bin/pytest -v` (w WSL). Na razie testy korzystają z prawdziwej bazy deweloperskiej — osobna baza testowa (override `get_db`) to zaplanowany refaktor.

---

## `alembic/` — migracje bazy danych

Migracja = wersjonowana zmiana schematu bazy (jak commit w gicie, ale dla struktury tabel).
Schematem bazy zarządza WYŁĄCZNIE Alembic (żadnych `create_all` / ręcznych DROP-ów).

| Plik / folder | Co robi |
|---|---|
| `alembic.ini` (w katalogu głównym) | Konfiguracja Alembica. Adres bazy jest tu placeholderem — prawdziwy wstrzykuje `env.py` z `.env` (żeby hasło nie trafiło do gita) |
| `env.py` | Skrypt startowy każdej komendy Alembica: podłącza URL bazy z `settings` i `Base.metadata` z naszych modeli (dzięki temu `--autogenerate` widzi różnice modele↔baza) |
| `versions/` | **Pliki migracji** — każdy to jedna zmiana schematu z funkcjami `upgrade()` (wykonaj) i `downgrade()` (cofnij), połączone w łańcuch przez `down_revision`. Obecnie: 1) `create leagues table`, 2) `add teams and standings tables` |
| `script.py.mako` | Szablon, z którego Alembic generuje nowe pliki migracji |
| `README` | Domyślna notka wygenerowana przez Alembica |

**Codzienny workflow:** zmień `models.py` → `alembic revision --autogenerate -m "opis"` → **przeczytaj wygenerowany plik** → `alembic upgrade head`.

---

## `instructions/` — dokumentacja projektu

| Plik / folder | Co zawiera |
|---|---|
| `project-assumptions.md` | **CO budujemy**: cel (portfolio do CV) i 5 faz projektu (tabele/drabinki → ulubione drużyny → predictor → symulator → ML) |
| `ROADMAP.md` | **JAK i KIEDY**: plan 24 sesji do 30 września, kamienie milowe, statusy `[x]/[~]/[ ]` + sekcja **Ryzyka** (m.in. zweryfikowane limity API-Football: darmowy plan = tylko sezony 2022–2024, 100 zapytań/dzień) |
| `tools.md` | **CZYM budujemy**: opis stacku (FastAPI, PostgreSQL, React...) i notatki środowiskowe |
| `progres.md` | Skrócona lista wszystkiego, co dotąd zrobiono (sekcja per sesja) |
| `project-structure.md` | Ten plik — mapa projektu |
| `sessions/` | **Logi sesji** (`session-NN.md`): co zrobiono, decyzje i dlaczego, czego się nauczyliśmy, TODO na następną sesję. Najlepsze miejsce do powtórek i przypomnienia kontekstu |

---

## Baza danych (PostgreSQL w WSL, `football_db`)

Nie jest plikiem w repo, ale to część projektu:

| Tabela | Co trzyma |
|---|---|
| `leagues` | 13 śledzonych rozgrywek (id z API-Football, nazwa, kraj, logo) |
| `teams` | Drużyny — 114 (wypełnione importem standings w Sesji 4) |
| `standings` | Wiersze tabel ligowych: liga + drużyna + sezon + statystyki — 114 (sezon 2024) |
| `alembic_version` | „Zakładka" Alembica — ID aktualnie wykonanej migracji |

---

## Co dojdzie później (wg ROADMAP)

- `frontend/` — React + TypeScript + Vite + Tailwind (od Sesji 7)
- `app/routers/` — podział endpointów na moduły, gdy ich przybędzie (planowane na Sesję 6)
- `app/prediction/` — model Poissona (Sesja 16)
