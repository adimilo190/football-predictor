# Struktura projektu — mapa plików i folderów

> Streszczenie całego projektu w jednym miejscu: co jest w każdym pliku/folderze i po co.
> **Ten plik aktualizujemy przy każdej zmianie struktury** (nowy plik/folder = nowy wpis tutaj) —
> to stały punkt rytuału końca sesji.
> Stan na: Sesja 18 (2026-09-13).

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
| `schemas.py` | **Schematy Pydantic = kontrakt API** (co wychodzi na zewnątrz): `LeagueResponse`, `TeamResponse`, `StandingResponse` (zagnieżdżona drużyna), `FixtureResponse` (dwie drużyny, gole nullable), `BracketRound` (runda + lista meczów; budowany ręcznie), `PredictionResponse`+`ScoreLine` (wynik predykcji: P(1/X/2) + top wyniki; wartości liczone, bez `from_attributes`) |
| `constants.py` | **Stałe biznesowe**: `TARGET_LEAGUE_IDS` (**15** rozgrywek = `DOMESTIC_LEAGUE_IDS` + `DOMESTIC_CUP_IDS` + `EUROPEAN_COMPETITION_IDS` z LM/LE/Konf), `DEFAULT_SEASON = 2024`, `KNOCKOUT_ROUNDS` (nazwy rund pucharowych dla filtra `knockout_only`), `FINISHED_STATUSES` (`{FT, AET, PEN}` — statusy meczu rozegranego, dla `past-matches`), `HOME_ADVANTAGE = 1.3` (mnożnik przewagi boiska dla predyktora Poissona) |
| `main.py` | **Cienki punkt wejścia** (~30 linii): tworzy `FastAPI`, konfiguruje **CORS** (origin `:5173`), rejestruje routery. Endpointy żyją w `routers/`. Dokumentacja: `/docs` (Swagger UI) |
| `routers/` | **Endpointy podzielone na moduły** — szczegóły niżej |
| `prediction/` | **Model predykcji (Poisson)** — czysta logika, niezależna od API — szczegóły niżej |

**Przepływ danych:** `.env` → `config.py` → `database.py` → `models.py` → (`schemas.py` +) `routers/` ← `main.py`.

### `app/routers/` — endpointy w modułach

| Plik | Co robi |
|---|---|
| `__init__.py` | Robi z `routers/` pakiet |
| `competitions.py` | **Odczyty (READ)**: `GET /leagues`, `GET /leagues/{id}/standings` (sort po `rank`, `joinedload` przeciw N+1), `GET /leagues/{id}/fixtures` (płaska lista), `GET /leagues/{id}/bracket` (grupowanie rundami + filtr `knockout_only`), `GET /leagues/{id}/seasons` (**dostępne sezony** — `UNION` sezonów ze `standings` (ligi) i `fixtures` (puchary), pod selektor tabel **i** drabinek). Helper `query_fixtures` (DRY) |
| `imports.py` | **Zapisy / ETL (WRITE)**: `POST /import-leagues`, `POST /import-standings`, `POST /import-fixtures` (ligi + puchary + europejskie = `TARGET_LEAGUE_IDS`) + funkcje `fetch_*` (Extract z API-Football) i `upsert_*` (Transform+Load). Obsługa limitów i błędów HTTP |
| `teams.py` | **Odczyty o drużynach (READ)**: `GET /teams/{id}/past-matches` (ostatnie rozegrane — `or_` home/away + `FINISHED_STATUSES` + `date desc` + `limit`), `GET /teams/{id}/future-matches` (najbliższe zaplanowane — `status NS` + `date asc`), `GET /teams?search=` (wyszukiwarka — `name.ilike("%…%")`, `limit 20`). Mecze/wyniki **cross-competition** (forma drużyny niezależnie od rozgrywki) |
| `predictions.py` | **Predykcja (READ)**: `GET /predict` (2 drużyny w ramach jednej ligi → `PredictionResponse`: P(1/X/2) + top 5 wyników). Walidacja 404 (drużyny muszą mieć `standings`), `float()` pod JSON. Woła `prediction/strength.py` (λ) → `prediction/poisson.py` (matematyka) |

### `app/prediction/` — model predykcji (Poisson)

Osobny pakiet: **czysta logika predykcji**. Warstwy: `strength.py` (dane→λ, czyta bazę) → `poisson.py` (λ→prawdopodobieństwa, zero DB). Endpoint `routers/predictions.py` je spina.

| Plik | Co robi |
|---|---|
| `__init__.py` | Robi z `prediction/` pakiet |
| `poisson.py` | **Czysta matematyka** (bez DB): `poisson_pmf` (`λ^k·e^-λ/k!`), `goal_distribution` (wektor P(0..max)), `score_matrix` (`np.outer` dwóch rozkładów + normalizacja), `match_outcome_probabilities` (`np.tril(-1)`/`trace`/`triu(1)` → P(1/X/2)), `top_scorelines` (n najbardziej prawdopodobnych wyników) |
| `strength.py` | **λ z danych** (`standings`): `league_baseline` (średnia goli/mecz w lidze = baza), `team_attack_defence` (siła ataku/obrony względem bazy), `match_lambdas` (składa λ_home/λ_away + `HOME_ADVANTAGE`). Predyktor **within-league** (siła jest względna do ligi) |

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
| `App.tsx` | **Layout + routing**: wspólny `<header>` (klikalny tytuł → `/`) nad `<Routes>`; trasy `/` → `HomePage`, `/leagues/:id` → `LeaguePage` (tabela), `/bracket/:id` → `BracketPage` (drabinka), **`/teams` → `SearchPage`** (wyszukiwarka), **`/teams/:id` → `TeamPage`** (mecze drużyny), **`/predict` → `PredictPage`** (predyktor) |
| `index.css` | Globalne style: `@import "tailwindcss"` (utility + preflight) + zmienne motywu i style `#root`/`h1`. **Wymuszony ciemny motyw** (wartości dark w `:root` + `color-scheme: dark`, usunięta bramka `@media prefers-color-scheme`). ⚠️ Globalne `h1`/`h2` (font/margin) z szablonu — nielayerowane, biją utilki Tailwinda; do sprzątnięcia |
| `App.css` | ⚠️ Pozostałość po szablonie Vite — **nieużywana** (nigdzie nieimportowana). Do sprzątnięcia |
| `api/config.ts` | `API_BASE_URL` z `VITE_API_URL` (`import.meta.env` + fallback). Jedno źródło adresu backendu |
| `api/standings.ts` | **Warstwa API (tabele)**: typy `Team`/`Standing` + `getStandings(leagueId, season)` (`fetch` z `?season=` + `throw` przy `!res.ok`) + `getSeasons(leagueId)` (lista dostępnych sezonów). Wołane jako `queryFn` |
| `api/bracket.ts` | **Warstwa API (drabinki)**: typy `Fixture`/`BracketRound` + `getBracket(leagueId, season, knockoutOnly)`; oraz `Matchup` + `groupIntoMatchups` (grupowanie dwumeczów w pary pod drzewko) |
| `api/teams.ts` | **Warstwa API (drużyny)**: `searchTeams(search)` (`?search=` + `encodeURIComponent`), `getPastMatches(id)`, `getFutureMatches(id)` — reuse typów `Team`/`Fixture` przez `import type`. Wołane jako `queryFn` |
| `api/predictions.ts` | **Warstwa API (predykcja)**: typy `ScoreLine`/`Prediction` (lustro `PredictionResponse`) + `getPrediction(homeId, awayId, leagueId, season)` (`GET /predict`; **klucze query snake_case** = jak backend, zmienne JS camelCase). Wołane jako `queryFn` |
| `hooks/useDebounce.ts` | **Custom hook** `useDebounce<T>(value, delayMs)`: opóźniona kopia wartości (`useState` + `useEffect` + `setTimeout` + cleanup `clearTimeout`). Używany przez `SearchPage` — fetch po ustaniu pisania, nie po każdym znaku |
| `hooks/useSeasonSelector.ts` | **Custom hook** `useSeasonSelector(id)`: lista sezonów (`useQuery`) + wybór usera (`useState`) + efektywny sezon (`selectedSeason ?? seasons[0]` = **derived state**, domyślnie najnowszy). Reuse w `LeaguePage`+`BracketPage` |
| `components/LeagueTable.tsx` | Tabela ligowa: prop `season`; `useQuery(["standings", leagueId, season], getStandings)` (**sezon w kluczu** = cache per sezon) → `data`/`isLoading`/`isError`, render `<table>` |
| `components/Bracket.tsx` | Drabinka: `useQuery(["bracket", leagueId], getBracket)` + **drzewko turniejowe** (kolumny rund `flex`+`items-stretch`+`justify-around`, `overflow-x-auto`); grupuje mecze przez `groupIntoMatchups`, renderuje `MatchupCard` |
| `components/MatchupCard.tsx` | Karta pary: dwie drużyny (herb + nazwa) + wyniki legów w pudełkach; dla dwumeczu nagłówki `1/2/Σ` i wynik zsumowany (agregat); wiersz **dat/godzin** meczów (helper `formatDate`, `toLocaleString`). **Reużyty też w `TeamPage`** (pojedynczy mecz = dwumecz z jedną nogą, przez adapter `fixtureToMatchup`). Style pod ciemny motyw (`bg-gray-800` karta, `bg-gray-700` pudełka) |
| `components/PredictionResult.tsx` | **Wizualizacja predykcji**: 3 paski 1/X/2 (wewnętrzny `OutcomeBar` — **DRY**, tor `bg-gray-700` + wypełnienie o szerokości `%` przez **inline `style`** bo wartość dynamiczna; kolory dark emerald/amber/sky) + lista najbardziej prawdopodobnych wyników. Dostaje `prediction` + nazwy drużyn przez **propsy** (tylko prezentacja) |
| `pages/HomePage.tsx` | Strona główna: karta **„Predict match"** → `/predict` (predyktor) + karta **„Find team"** → `/teams` (wyszukiwarka) + **accordion** przez `<details>` — 6 krajów (`COUNTRIES`: liga→`/leagues/:id`, puchar→`/bracket/:id`) + „European Competitions" (→`/bracket/:id`) |
| `pages/LeaguePage.tsx` | Strona ligi: czyta `:id` (`useParams`); **selektor sezonu** — `useState` wybranego sezonu (UI state) + `useQuery(getSeasons)` (lista) + `<select>`; przekazuje `leagueId`+`season` do `LeagueTable` |
| `pages/BracketPage.tsx` | Strona rozgrywki pucharowej: czyta `:id` przez `useParams` (strażnik), przekazuje `leagueId` do `Bracket` (drabinka) |
| `pages/SearchPage.tsx` | **Wyszukiwarka drużyn**: kontrolowany `<input>` → `useDebounce(300)` → `useQuery(["teamSearch", term], searchTeams, enabled: term.length>0)`; wyniki jako `<Link to={/teams/:id}>`. Render stanów przez zmienną + `if` (input zostaje na ekranie) |
| `pages/TeamPage.tsx` | **Mecze drużyny** (`/teams/:id`): dwa `useQuery` (`getPastMatches`/`getFutureMatches`), guardy po hookach (`if (!past||!future) return null` = zawężenie typu); adapter `fixtureToMatchup` + reuse `MatchupCard`; nagłówek (logo+nazwa z 1. meczu) + dwie kolumny past/future (`flex gap-8`) |
| `pages/PredictPage.tsx` | **Predyktor** (`/predict`): wybór ligi (`COUNTRIES`→`<select>`) → 2 drużyny z tej ligi (`useQuery(getStandings)` + **`enabled`**, dwa selekty, reset przy zmianie ligi) → `useQuery(getPrediction)` (**`enabled`**: obie wybrane i różne) → render `PredictionResult`. Sezon = stała `PREDICTION_SEASON` (ostatni pełny sezon). Predyktor **within-league** |
| `data/leagues.ts` | Model nawigacji: typy `Competition`/`Country` + `COUNTRIES` (6 krajów: liga+puchar) i `EUROPEAN_COMPETITIONS` (LM/LE/Konf) — `id` z API-Football |
| `assets/` | Grafiki z szablonu Vite (`react.svg`, `vite.svg`, `hero.png`) — obecnie nieużywane |

**Przepływ:** `main.tsx` → `App.tsx` (routing) → `pages/` → `components/` → `api/` → backend.

---

## `tests/` — testy automatyczne (pytest)

| Plik | Co robi |
|---|---|
| `__init__.py` | Robi z `tests/` pakiet (pytest dokłada katalog projektu do `sys.path`) |
| `conftest.py` | **Infrastruktura testowa**: izolowana baza **SQLite in-memory** (`StaticPool`), podmiana `get_db` przez `app.dependency_overrides`, autouse fixture czyszcząca bazę per test, fixtures `client`/`db_session` |
| `test_main.py` | **14 testów** endpointów (Arrange–Act–Assert, własny seed): `/`, `/leagues`, `/standings`, `/fixtures`, `/bracket` (wszystkie rundy + dowód sortu, oraz filtr `knockout_only`), `/seasons` (`UNION` standings+fixtures + dedup + sort), `/teams/{id}/past-matches` (scenariusz szczelny `or_`/status/sort), `/teams/{id}/future-matches` (`NS`+`asc`), `/teams?search=` (`ilike` substring + case-insensitive + `order_by` + pusty wynik), błędne id → 404 (standings + drużyna), `/predict` (P(1/X/2) sumują ≈1 + top 5) i 404 dla drużyny spoza ligi |
| `test_poisson.py` | **5 testów** czystej matematyki Poissona (bez DB, known-values): `poisson_pmf`, `goal_distribution` (suma≈1), `score_matrix` (kształt + komórka 1:0), `match_outcome_probabilities` (61/21/18), `top_scorelines` (sort). Razem z `test_main.py`: **pytest 19/19** |

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
| `sessions/` | **Logi sesji** (`session-01`…`session-18`): co zrobiono, decyzje, lekcje, TODO, praca domowa |

---

## Baza danych (PostgreSQL w WSL, `football_db`)

Nie jest plikiem w repo, ale to część projektu:

| Tabela | Co trzyma |
|---|---|
| `leagues` | **15** śledzonych rozgrywek (6 lig + 6 pucharów krajowych + LM/LE/Konf; id z API-Football, nazwa, kraj, logo) |
| `teams` | Drużyny — **1962** (ligowe + pucharowe/europejskie) |
| `standings` | Wiersze tabel ligowych: liga+drużyna+sezon+statystyki — **572** (6 lig × sezony **2022–2026**) |
| `fixtures` | Mecze — **7980** (puchary krajowe + LM/LE/Konf **oraz mecze ligowe**; sezony **2024–2026**) |
| `alembic_version` | „Zakładka" Alembica — ID aktualnie wykonanej migracji |

---

## Co dojdzie później (wg ROADMAP)

- **Deploy (Sesja 19, po powrocie ~26 wrz)** — PRIORYTET: backend + PostgreSQL (Railway/Render), frontend (Vercel), rozszerzenie CORS o domenę Vercela, **README pro** pod CV. PRZED Fazą 4/5.
- **Model #2 (Dixon-Coles)** — **uśrednianie danych z wielu sezonów** (wagi czasowe: ostatni + bieżący) + korekta niskich wyników; split dom/wyjazd z `fixtures`. Potem **model #3 (ML)** + porównanie modeli (Faza 5).
- **Faza 4 (symulator Monte Carlo)** — symulacja meczu/ligi (po deployu).
- **Długi UI**: `TeamSelect` (duplikacja dwóch selektów w `PredictPage`), sprzątnięcie `index.css`/`App.css` (pozostałości szablonu Vite), loading state drużyn w `PredictPage`.
- **Tabela fazy ligowej** (LM/LE/Konf) — policzona z meczów lub z importu standings (odłożone).
- Upiększacze drabinki: linie łączące pary; rozszerzenie `KNOCKOUT_ROUNDS` o rundy pucharów krajowych (żeby FA Cup pokazywał więcej niż QF→Final).
