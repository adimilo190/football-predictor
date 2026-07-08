# Struktura projektu — mapa plików i folderów

> Streszczenie całego projektu w jednym miejscu: co jest w każdym pliku/folderze i po co.
> **Ten plik aktualizujemy przy każdej zmianie struktury** (nowy plik/folder = nowy wpis tutaj).
> Stan na: Sesja 3 (2026-07-08).

---

## Katalog główny

| Plik / folder | Co to jest i po co |
|---|---|
| `app/` | **Cały kod backendu** (pakiet Pythona) — szczegóły niżej |
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
| `__pycache__/`, `.ruff_cache/` | Automatyczne cache Pythona i Ruffa — można bezpiecznie skasować, odtworzą się same. NIE w gicie |

---

## `app/` — kod backendu (FastAPI)

Pakiet Pythona (ma `__init__.py`). Warstwy od spodu do góry:

| Plik | Co robi |
|---|---|
| `__init__.py` | Pusty plik, który mówi Pythonowi „ten folder to pakiet" — dzięki niemu działają importy `from app...` |
| `config.py` | **Jedno źródło konfiguracji.** Klasa `Settings` (pydantic-settings) wczytuje `.env`, waliduje i głośno krzyczy na starcie, jeśli czegoś brakuje. Reszta kodu robi `from app.config import settings` |
| `database.py` | **Połączenie z PostgreSQL**: `engine` (fizyczne połączenie), `SessionLocal` (fabryka sesji — jedna sesja = jedna „rozmowa" z bazą), `Base` (klasa bazowa, z której dziedziczą modele) |
| `models.py` | **Modele SQLAlchemy = tabele w bazie**: `League` (rozgrywki), `Team` (drużyna — celowo bez przypisania do ligi, bo gra w wielu rozgrywkach), `Standing` (wiersz tabeli ligowej: liga + drużyna + sezon + statystyki; klucze obce i blokada duplikatów) |
| `schemas.py` | **Schematy Pydantic = kontrakt API**: co dokładnie endpointy zwracają na zewnątrz (np. `LeagueResponse`). Osobna warstwa od `models.py`: baza może mieć więcej pól niż pokazujemy światu |
| `constants.py` | **Stałe biznesowe**: `TARGET_LEAGUE_IDS` — ID 13 śledzonych rozgrywek w API-Football (6 lig + 6 pucharów krajowych + Liga Mistrzów) |
| `main.py` | **Serce API**: tworzy aplikację FastAPI i definiuje endpointy — `GET /` (test), `POST /import-leagues` (pobiera rozgrywki z API-Football do naszej bazy), `GET /my-leagues` (pokazuje naszą bazę). Dokumentacja interaktywna: `/docs` (Swagger UI) |

**Przepływ danych:** `.env` → `config.py` → `database.py` → `models.py` → (`schemas.py` +) `main.py`.

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
| `teams` | Drużyny (na razie pusta — wypełni ją import standings w Sesji 4) |
| `standings` | Wiersze tabel ligowych: liga + drużyna + sezon + statystyki (na razie pusta) |
| `alembic_version` | „Zakładka" Alembica — ID aktualnie wykonanej migracji |

---

## Co dojdzie później (wg ROADMAP)

- `tests/` — testy pytest (od Sesji 5)
- `frontend/` — React + TypeScript + Vite + Tailwind (od Sesji 7)
- `app/routers/` — podział endpointów na moduły, gdy ich przybędzie
- `app/prediction/` — model Poissona (Sesja 16)
