# Struktura projektu — mapa plików i folderów

> Streszczenie całego projektu w jednym miejscu: co jest w każdym pliku/folderze i po co.
> **Ten plik aktualizujemy przy każdej zmianie struktury** (nowy plik/folder = nowy wpis tutaj) —
> to stały punkt rytuału końca sesji.
> Stan na: Sesja 11 (2026-08-18).

---

## Katalog główny

| Plik / folder | Co to jest i po co |
|---|---|
| `app/` | **Kod backendu** (pakiet Pythona, FastAPI) — szczegóły niżej |
| `frontend/` | **Kod frontendu** (React + TypeScript + Vite + Tailwind) — szczegóły niżej |
| `tests/` | **Testy pytest** — sprawdzają API przez `TestClient` na izolowanej bazie, bez uruchamiania serwera |
| `alembic/` + `alembic.ini` | **Migracje bazy danych** — szczegóły niżej |
| `instructions/` | **Dokumentacja projektu** (plany, logi, decyzje) — szczegóły niżej |
| `venv/` | Wirtualne środowisko Pythona (izolowane paczki). NIE w gicie. Używamy `venv/bin/python`, `venv/bin/pip` |
| `.env` | **SEKRETY**: `DATABASE_URL`, `API_FOOTBALL_KEY`. NIE w gicie — nigdy nie commitować! |
| `.env.example` | Wzór `.env` bez prawdziwych wartości — jest w gicie, żeby było wiadomo, jakie zmienne ustawić |
| `.gitignore` | Czego git ma NIE śledzić (venv, `__pycache__`, `.env`, `node_modules`, `dist`) |
| `requirements.txt` | Zamrożone wersje paczek Pythona — `pip install -r requirements.txt` odtwarza środowisko (`pip freeze` po każdej instalacji) |
| `CLAUDE.md` | Zasady współpracy: tryb nauki, rytm (jeden krok naraz), rytuał końca sesji, środowisko (WSL, venv, PostgreSQL) |
| `.claude/` | Ustawienia Claude Code dla projektu (`settings.local.json` — uprawnienia narzędzi) |
| `.git/` | Wewnętrzna baza gita (historia commitów). Nie ruszamy ręcznie |
| `__pycache__/`, `.ruff_cache/`, `.pytest_cache/` | Automatyczne cache Pythona / Ruffa / pytest — można skasować, odtworzą się. NIE w gicie |

---

## `app/` — kod backendu (FastAPI)

Pakiet Pythona (`__init__.py`). Warstwy od spodu do góry:

| Plik | Co robi |
|---|---|
| `__init__.py` | Pusty plik — mówi Pythonowi „ten folder to pakiet"; dzięki temu działają importy `from app...` |
| `config.py` | **Jedno źródło konfiguracji.** Klasa `Settings` (pydantic-settings) wczytuje `.env`, waliduje, krzyczy na starcie, jeśli czegoś brak. Reszta kodu: `from app.config import settings` |
| `database.py` | **Połączenie z PostgreSQL**: `engine`, `SessionLocal` (fabryka sesji), `Base` (klasa bazowa modeli) + zależność `get_db` (jedna sesja na request; tu, by uniknąć cyklu importów) |
| `models.py` | **Modele SQLAlchemy = tabele**: `League` (rozgrywki), `Team` (drużyna — bez ligi, bo gra w wielu), `Standing` (wiersz tabeli: liga+drużyna+sezon+statystyki), `Fixture` (mecz: **dwa** FK do `teams` — home/away, wynik, data, runda, status) |
| `schemas.py` | **Schematy Pydantic = kontrakt API** (co wychodzi na zewnątrz): `LeagueResponse`, `TeamResponse`, `StandingResponse` (zagnieżdżona drużyna), `FixtureResponse` (dwie drużyny, gole nullable), `BracketRound` (runda + lista meczów; budowany ręcznie) |
| `constants.py` | **Stałe biznesowe**: `TARGET_LEAGUE_IDS` (13 rozgrywek = `DOMESTIC_LEAGUE_IDS` + `DOMESTIC_CUP_IDS` + `EUROPEAN_COMPETITION_IDS`), `DEFAULT_SEASON = 2024`, `KNOCKOUT_ROUNDS` (nazwy rund pucharowych dla filtra `knockout_only`) |
| `main.py` | **Cienki punkt wejścia** (~30 linii): tworzy `FastAPI`, konfiguruje **CORS** (origin `:5173`), rejestruje routery. Endpointy żyją w `routers/`. Dokumentacja: `/docs` (Swagger UI) |
| `routers/` | **Endpointy podzielone na moduły** — szczegóły niżej |

**Przepływ danych:** `.env` → `config.py` → `database.py` → `models.py` → (`schemas.py` +) `routers/` ← `main.py`.

### `app/routers/` — endpointy w modułach

| Plik | Co robi |
|---|---|
| `__init__.py` | Robi z `routers/` pakiet |
| `competitions.py` | **Odczyty (READ)**: `GET /leagues`, `GET /leagues/{id}/standings` (sort po `rank`, `joinedload` przeciw N+1), `GET /leagues/{id}/fixtures` (płaska lista), `GET /leagues/{id}/bracket` (grupowanie rundami + filtr `knockout_only`). Helper `query_fixtures` (DRY) |
| `imports.py` | **Zapisy / ETL (WRITE)**: `POST /import-leagues`, `POST /import-standings`, `POST /import-fixtures` + funkcje `fetch_*` (Extract z API-Football) i `upsert_*` (Transform+Load). Obsługa limitów i błędów HTTP |

---

## `frontend/` — kod frontendu (React + TypeScript + Vite + Tailwind)

Aplikacja SPA (single-page). Uruchomienie: `npm run dev` (w WSL, Node przez `nvm`). Node/npm i `node_modules` NIE w gicie.

### `frontend/` — pliki konfiguracyjne (root)

| Plik / folder | Co robi |
|---|---|
| `index.html` | Szkielet strony: `<div id="root">` + `<script src="/src/main.tsx">`. Punkt startowy, w który React „wstrzykuje" aplikację |
| `package.json` | Zależności JS (React 19, `react-router-dom`, `@tanstack/react-query`, `tailwindcss`, Vite, oxlint, prettier, TypeScript) + skrypty `dev`/`build`/`lint`/`format` |
| `package-lock.json` | Zamrożone dokładne wersje wszystkich paczek (odpowiednik `requirements.txt` dla JS) |
| `vite.config.ts` | Konfiguracja Vite: pluginy React + Tailwind |
| `tsconfig*.json` | Konfiguracja TypeScriptu (`tsconfig.json` spina, `.app`/`.node` — osobno kod aplikacji i narzędzi) |
| `.env` | Konfiguracja per-środowisko: `VITE_API_URL` (adres backendu). NIE tajne (ląduje w bundlu), ale NIE w gicie |
| `.env.example` | Wzór `.env` frontendu — jest w gicie |
| `public/` | Pliki serwowane statycznie „jak są" (np. favicon) |
| `README.md` | Domyślne readme z szablonu Vite |

### `frontend/src/` — kod aplikacji

| Plik / folder | Co robi |
|---|---|
| `main.tsx` | **Punkt wejścia Reacta**: montuje `<App/>` w `#root`, owinięty w `BrowserRouter` (routing) i `QueryClientProvider` (cache TanStack Query); importuje `index.css` |
| `App.tsx` | **Layout + routing**: wspólny `<header>` (klikalny tytuł → `/`) nad `<Routes>`; trasy `/` → `HomePage`, `/leagues/:id` → `LeaguePage` |
| `index.css` | Globalne style: `@import "tailwindcss"` (utility + preflight) + zmienne motywu i style `#root`/`h1` |
| `App.css` | ⚠️ Pozostałość po szablonie Vite — **nieużywana** (nigdzie nieimportowana). Do sprzątnięcia |
| `api/config.ts` | `API_BASE_URL` z `VITE_API_URL` (`import.meta.env` + fallback). Jedno źródło adresu backendu |
| `api/standings.ts` | **Warstwa API**: typy `Team`/`Standing` (lustro `schemas.py`) + `getStandings(leagueId)` (`fetch` + `throw` przy `!res.ok` + `res.json()`). Wołana jako `queryFn` |
| `components/LeagueCard.tsx` | Karta ligi (props `name`/`country`, styl Tailwind: ramka, cień, hover) |
| `components/LeagueTable.tsx` | Tabela ligowa: `useQuery(["standings", leagueId], getStandings)` → `data`/`isLoading`/`isError`, render `<table>` |
| `pages/HomePage.tsx` | Strona główna: siatka `grid` responsywnych kart lig (`LEAGUES`), każda w `<Link>` do `/leagues/:id` |
| `pages/LeaguePage.tsx` | Strona ligi: czyta `:id` przez `useParams` (strażnik na brak), przekazuje `leagueId` do `LeagueTable` |
| `data/leagues.ts` | Statyczne dane nawigacji: typ `League` + `LEAGUES` (6 lig z `id` z API-Football) |
| `assets/` | Grafiki z szablonu Vite (`react.svg`, `vite.svg`, `hero.png`) — obecnie nieużywane |

**Przepływ:** `main.tsx` → `App.tsx` (routing) → `pages/` → `components/` → `api/` → backend.

---

## `tests/` — testy automatyczne (pytest)

| Plik | Co robi |
|---|---|
| `__init__.py` | Robi z `tests/` pakiet (pytest dokłada katalog projektu do `sys.path`) |
| `conftest.py` | **Infrastruktura testowa**: izolowana baza **SQLite in-memory** (`StaticPool`), podmiana `get_db` przez `app.dependency_overrides`, autouse fixture czyszcząca bazę per test, fixtures `client`/`db_session` |
| `test_main.py` | **7 testów** endpointów (Arrange–Act–Assert, własny seed): `/`, `/leagues`, `/standings`, `/fixtures`, `/bracket` (wszystkie rundy + dowód sortu, oraz filtr `knockout_only`), błędne id → 404 |

**Uruchomienie:** `venv/bin/pytest -v` (w WSL). Testy nie ruszają prawdziwej bazy ani API-Football.

---

## `alembic/` — migracje bazy danych

Migracja = wersjonowana zmiana schematu (jak commit, ale dla struktury tabel). Schematem zarządza WYŁĄCZNIE Alembic (żadnych `create_all` / ręcznych DROP-ów).

| Plik / folder | Co robi |
|---|---|
| `alembic.ini` (w katalogu głównym) | Konfiguracja Alembica; adres bazy to placeholder — prawdziwy wstrzykuje `env.py` z `.env` |
| `env.py` | Skrypt startowy: URL bazy z `settings` + `Base.metadata` modeli (żeby `--autogenerate` widział różnice modele↔baza) |
| `versions/` | **Pliki migracji** (łańcuch przez `down_revision`): 1) `create leagues table`, 2) `add teams and standings tables`, 3) `create fixtures table` |
| `script.py.mako` | Szablon nowych migracji |
| `README` | Domyślna notka Alembica |

**Workflow:** zmień `models.py` → `alembic revision --autogenerate -m "opis"` → **przeczytaj plik** → `alembic upgrade head`.

---

## `instructions/` — dokumentacja projektu

| Plik / folder | Co zawiera |
|---|---|
| `project-assumptions.md` | **CO budujemy**: cel (portfolio/CV) i 5 faz (tabele/drabinki → ulubione → predictor → symulator → ML) |
| `ROADMAP.md` | **JAK i KIEDY**: plan sesji do 30 września, kamienie milowe, statusy, sekcja **Ryzyka** (limity API) i **Wizja docelowego UX** (przyszła nawigacja) |
| `tools.md` | **CZYM budujemy**: opis stacku i notatki środowiskowe |
| `progres.md` | Skrócona lista wszystkiego, co zrobiono (sekcja per sesja) |
| `project-structure.md` | Ten plik — mapa projektu (aktualizowana co sesję) |
| `sessions/` | **Logi sesji** (`session-01`…`session-11`): co zrobiono, decyzje, lekcje, TODO, praca domowa |

---

## Baza danych (PostgreSQL w WSL, `football_db`)

Nie jest plikiem w repo, ale to część projektu:

| Tabela | Co trzyma |
|---|---|
| `leagues` | 13 śledzonych rozgrywek (id z API-Football, nazwa, kraj, logo) |
| `teams` | Drużyny — ~1267 (ligowe + pucharowe, po imporcie fixtures w Sesji 6) |
| `standings` | Wiersze tabel ligowych: liga+drużyna+sezon+statystyki — 114 (6 lig, sezon 2024) |
| `fixtures` | Mecze (głównie pucharowe + Liga Mistrzów) — 1733 (sezon 2024) |
| `alembic_version` | „Zakładka" Alembica — ID aktualnie wykonanej migracji |

---

## Co dojdzie później (wg ROADMAP)

- `app/prediction/` — model Poissona, niezależny od API (Sesja 16)
- **Przebudowa nawigacji** wg „Wizji docelowego UX": rozwijana lista krajów + puchary europejskie, selektor sezonu (Faza 1 szlify / Faza 2)
- Doimport **Ligi Europy** i **Ligi Konferencji** (obecnie w bazie tylko Liga Mistrzów)
- `frontend/src/api/` — kolejne funkcje pobierające (`getBracket`, `getFixtures`) obok `getStandings`
