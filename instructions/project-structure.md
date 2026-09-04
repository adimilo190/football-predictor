# Struktura projektu — mapa plików i folderów

> Streszczenie całego projektu w jednym miejscu: co jest w każdym pliku/folderze i po co.
> **Ten plik aktualizujemy przy każdej zmianie struktury** (nowy plik/folder = nowy wpis tutaj) —
> to stały punkt rytuału końca sesji.
> Stan na: Sesja 16 (2026-09-04).

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
| `.vscode/` | Lokalne ustawienia VS Code (`settings.json` — format-on-save: Ruff/Python 4 spacje, Prettier/TS 2 spacje). W `.gitignore` — NIE w gicie |
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
| `constants.py` | **Stałe biznesowe**: `TARGET_LEAGUE_IDS` (**15** rozgrywek = `DOMESTIC_LEAGUE_IDS` + `DOMESTIC_CUP_IDS` + `EUROPEAN_COMPETITION_IDS` z LM/LE/Konf), `DEFAULT_SEASON = 2024`, `KNOCKOUT_ROUNDS` (nazwy rund pucharowych dla filtra `knockout_only`), `FINISHED_STATUSES` (`{FT, AET, PEN}` — statusy meczu rozegranego, dla `past-matches`) |
| `main.py` | **Cienki punkt wejścia** (~30 linii): tworzy `FastAPI`, konfiguruje **CORS** (origin `:5173`), rejestruje routery. Endpointy żyją w `routers/`. Dokumentacja: `/docs` (Swagger UI) |
| `routers/` | **Endpointy podzielone na moduły** — szczegóły niżej |

**Przepływ danych:** `.env` → `config.py` → `database.py` → `models.py` → (`schemas.py` +) `routers/` ← `main.py`.

### `app/routers/` — endpointy w modułach

| Plik | Co robi |
|---|---|
| `__init__.py` | Robi z `routers/` pakiet |
| `competitions.py` | **Odczyty (READ)**: `GET /leagues`, `GET /leagues/{id}/standings` (sort po `rank`, `joinedload` przeciw N+1), `GET /leagues/{id}/fixtures` (płaska lista), `GET /leagues/{id}/bracket` (grupowanie rundami + filtr `knockout_only`), `GET /leagues/{id}/seasons` (**dostępne sezony** — `UNION` sezonów ze `standings` (ligi) i `fixtures` (puchary), pod selektor tabel **i** drabinek). Helper `query_fixtures` (DRY) |
| `imports.py` | **Zapisy / ETL (WRITE)**: `POST /import-leagues`, `POST /import-standings`, `POST /import-fixtures` (ligi + puchary + europejskie = `TARGET_LEAGUE_IDS`) + funkcje `fetch_*` (Extract z API-Football) i `upsert_*` (Transform+Load). Obsługa limitów i błędów HTTP |
| `teams.py` | **Odczyty o drużynach (READ)**: `GET /teams/{id}/past-matches` (ostatnie rozegrane — `or_` home/away + `FINISHED_STATUSES` + `date desc` + `limit`), `GET /teams/{id}/future-matches` (najbliższe zaplanowane — `status NS` + `date asc`), `GET /teams?search=` (wyszukiwarka — `name.ilike("%…%")`, `limit 20`). Mecze/wyniki **cross-competition** (forma drużyny niezależnie od rozgrywki) |

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
| `App.tsx` | **Layout + routing**: wspólny `<header>` (klikalny tytuł → `/`) nad `<Routes>`; trasy `/` → `HomePage`, `/leagues/:id` → `LeaguePage` (tabela), `/bracket/:id` → `BracketPage` (drabinka), **`/teams` → `SearchPage`** (wyszukiwarka), **`/teams/:id` → `TeamPage`** (mecze drużyny) |
| `index.css` | Globalne style: `@import "tailwindcss"` (utility + preflight) + zmienne motywu i style `#root`/`h1`. **Wymuszony ciemny motyw** (wartości dark w `:root` + `color-scheme: dark`, usunięta bramka `@media prefers-color-scheme`). ⚠️ Globalne `h1`/`h2` (font/margin) z szablonu — nielayerowane, biją utilki Tailwinda; do sprzątnięcia |
| `App.css` | ⚠️ Pozostałość po szablonie Vite — **nieużywana** (nigdzie nieimportowana). Do sprzątnięcia |
| `api/config.ts` | `API_BASE_URL` z `VITE_API_URL` (`import.meta.env` + fallback). Jedno źródło adresu backendu |
| `api/standings.ts` | **Warstwa API (tabele)**: typy `Team`/`Standing` + `getStandings(leagueId, season)` (`fetch` z `?season=` + `throw` przy `!res.ok`) + `getSeasons(leagueId)` (lista dostępnych sezonów). Wołane jako `queryFn` |
| `api/bracket.ts` | **Warstwa API (drabinki)**: typy `Fixture`/`BracketRound` + `getBracket(leagueId, season, knockoutOnly)`; oraz `Matchup` + `groupIntoMatchups` (grupowanie dwumeczów w pary pod drzewko) |
| `api/teams.ts` | **Warstwa API (drużyny)**: `searchTeams(search)` (`?search=` + `encodeURIComponent`), `getPastMatches(id)`, `getFutureMatches(id)` — reuse typów `Team`/`Fixture` przez `import type`. Wołane jako `queryFn` |
| `hooks/useDebounce.ts` | **Custom hook** `useDebounce<T>(value, delayMs)`: opóźniona kopia wartości (`useState` + `useEffect` + `setTimeout` + cleanup `clearTimeout`). Używany przez `SearchPage` — fetch po ustaniu pisania, nie po każdym znaku |
| `components/LeagueTable.tsx` | Tabela ligowa: prop `season`; `useQuery(["standings", leagueId, season], getStandings)` (**sezon w kluczu** = cache per sezon) → `data`/`isLoading`/`isError`, render `<table>` |
| `components/Bracket.tsx` | Drabinka: `useQuery(["bracket", leagueId], getBracket)` + **drzewko turniejowe** (kolumny rund `flex`+`items-stretch`+`justify-around`, `overflow-x-auto`); grupuje mecze przez `groupIntoMatchups`, renderuje `MatchupCard` |
| `components/MatchupCard.tsx` | Karta pary: dwie drużyny (herb + nazwa) + wyniki legów w pudełkach; dla dwumeczu nagłówki `1/2/Σ` i wynik zsumowany (agregat); wiersz **dat/godzin** meczów (helper `formatDate`, `toLocaleString`). **Reużyty też w `TeamPage`** (pojedynczy mecz = dwumecz z jedną nogą, przez adapter `fixtureToMatchup`). Style pod ciemny motyw (`bg-gray-800` karta, `bg-gray-700` pudełka) |
| `pages/HomePage.tsx` | Strona główna: karta **„Find team"** → `/teams` (wyszukiwarka) + **accordion** przez `<details>` — 6 krajów (`COUNTRIES`: liga→`/leagues/:id`, puchar→`/bracket/:id`) + „European Competitions" (→`/bracket/:id`) |
| `pages/LeaguePage.tsx` | Strona ligi: czyta `:id` (`useParams`); **selektor sezonu** — `useState` wybranego sezonu (UI state) + `useQuery(getSeasons)` (lista) + `<select>`; przekazuje `leagueId`+`season` do `LeagueTable` |
| `pages/BracketPage.tsx` | Strona rozgrywki pucharowej: czyta `:id` przez `useParams` (strażnik), przekazuje `leagueId` do `Bracket` (drabinka) |
| `pages/SearchPage.tsx` | **Wyszukiwarka drużyn**: kontrolowany `<input>` → `useDebounce(300)` → `useQuery(["teamSearch", term], searchTeams, enabled: term.length>0)`; wyniki jako `<Link to={/teams/:id}>`. Render stanów przez zmienną + `if` (input zostaje na ekranie) |
| `pages/TeamPage.tsx` | **Mecze drużyny** (`/teams/:id`): dwa `useQuery` (`getPastMatches`/`getFutureMatches`), guardy po hookach (`if (!past||!future) return null` = zawężenie typu); adapter `fixtureToMatchup` + reuse `MatchupCard`; nagłówek (logo+nazwa z 1. meczu) + dwie kolumny past/future (`flex gap-8`) |
| `data/leagues.ts` | Model nawigacji: typy `Competition`/`Country` + `COUNTRIES` (6 krajów: liga+puchar) i `EUROPEAN_COMPETITIONS` (LM/LE/Konf) — `id` z API-Football |
| `assets/` | Grafiki z szablonu Vite (`react.svg`, `vite.svg`, `hero.png`) — obecnie nieużywane |

**Przepływ:** `main.tsx` → `App.tsx` (routing) → `pages/` → `components/` → `api/` → backend.

---

## `tests/` — testy automatyczne (pytest)

| Plik | Co robi |
|---|---|
| `__init__.py` | Robi z `tests/` pakiet (pytest dokłada katalog projektu do `sys.path`) |
| `conftest.py` | **Infrastruktura testowa**: izolowana baza **SQLite in-memory** (`StaticPool`), podmiana `get_db` przez `app.dependency_overrides`, autouse fixture czyszcząca bazę per test, fixtures `client`/`db_session` |
| `test_main.py` | **12 testów** endpointów (Arrange–Act–Assert, własny seed): `/`, `/leagues`, `/standings`, `/fixtures`, `/bracket` (wszystkie rundy + dowód sortu, oraz filtr `knockout_only`), `/seasons` (`UNION` standings+fixtures + dedup + sort), `/teams/{id}/past-matches` (scenariusz szczelny `or_`/status/sort), `/teams/{id}/future-matches` (`NS`+`asc`), `/teams?search=` (`ilike` substring + case-insensitive + `order_by` + pusty wynik), błędne id → 404 (standings + drużyna) |

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
| `sessions/` | **Logi sesji** (`session-01`…`session-15`): co zrobiono, decyzje, lekcje, TODO, praca domowa |

---

## Baza danych (PostgreSQL w WSL, `football_db`)

Nie jest plikiem w repo, ale to część projektu:

| Tabela | Co trzyma |
|---|---|
| `leagues` | **15** śledzonych rozgrywek (6 lig + 6 pucharów krajowych + LM/LE/Konf; id z API-Football, nazwa, kraj, logo) |
| `teams` | Drużyny — **1962** (ligowe + pucharowe/europejskie; +3 z importu meczów ligowych 2026 w Sesji 15) |
| `standings` | Wiersze tabel ligowych: liga+drużyna+sezon+statystyki — **572** (6 lig × sezony **2022–2026**) |
| `fixtures` | Mecze — **7980** (puchary krajowe + LM/LE/Konf **oraz mecze ligowe**; sezony **2024–2026**; +2087 z importu meczów ligowych 2026 w Sesji 15) |
| `alembic_version` | „Zakładka" Alembica — ID aktualnie wykonanej migracji |

---

## Co dojdzie później (wg ROADMAP)

- **Close-out Fazy 2 (Sesja 17)**: dark-polish komponentów (tabela ligowa, hovery) + domyślny sezon = najnowszy (`seasons[0]`); sprzątnięcie `index.css`/`App.css` (pozostałości szablonu)
- `app/prediction/` — model Poissona, niezależny od API (**Sesja 17**, po close-oucie Fazy 2)
- **Tabela fazy ligowej** (LM/LE/Konf) — policzona z meczów lub z importu standings (odłożone)
- **Selektor sezonu** — ✅ zrobiony dla **tabel** (Sesja 13) **i drabinek** (Sesja 14, `/seasons` na `UNION`)
- Upiększacze drabinki: linie łączące pary; rozszerzenie `KNOCKOUT_ROUNDS` o rundy pucharów krajowych (żeby FA Cup pokazywał więcej niż QF→Final)
