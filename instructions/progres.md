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

## Sesja 3 (2026-07-08) — Migracje Alembic, modele Team/Standing, docelowe rozgrywki
* [x] Alembic: init + konfiguracja (`env.py`: URL bazy z `settings`, `target_metadata`, import modeli); adres bazy NIE trafia do plików w gicie.
* [x] Migracja bazowa „czysty start": DROP testowej tabeli `leagues` → migracja `create leagues table` → `upgrade head`; baza odtwarzalna od zera jedną komendą.
* [x] `create_all` usunięty z `main.py` — schematem bazy zarządza wyłącznie Alembic.
* [x] Modele `Team` (bez league_id — relacja wiele-do-wielu przez standings) i `Standing` (FK do leagues/teams, season, statystyki, `UniqueConstraint(league_id, team_id, season)`); druga migracja wykonana.
* [x] `app/constants.py` — `TARGET_LEAGUE_IDS`: 13 śledzonych rozgrywek (6 lig + 6 pucharów krajowych + Liga Mistrzów).
* [x] `/import-leagues`: `GET`→`POST` (REST), 1 zapytanie o pełną listę lig + filtr lokalny (limit 100/dzień), odpowiedź z listą zaimportowanych nazw.
* [x] Import wykonany: 13/13 rozgrywek w bazie, zweryfikowane przez `TestClient` i `/my-leagues`.
* [x] `FastAPI(title="Football Predictor API")`; Ruff czysty; `requirements.txt` zaktualizowany (alembic).
* [x] Nowa zasada współpracy w `CLAUDE.md`: jeden krok planu naraz + pytanie o zgodę przed następnym.
* **Wynik:** Fundament danych gotowy — wersjonowany schemat (2 migracje), tabele `teams`/`standings` czekają na import tabel ligowych w Sesji 4.

## Sesja 4 (2026-07-09) — Import tabel lig (pełny rurociąg ETL)
* [x] Nowa zasada w `CLAUDE.md`: po każdej sesji praca domowa (dokumentacja pod następną sesję) w logu sesji.
* [x] `app/constants.py`: rozgrywki rozdzielone na grupy (`DOMESTIC_LEAGUE_IDS` / `DOMESTIC_CUP_IDS` / `EUROPEAN_COMPETITION_IDS`), `TARGET_LEAGUE_IDS` = scalenie `**`; stała `DEFAULT_SEASON = 2024`.
* [x] Extract: `fetch_league_standings` — httpx z `params`/`timeout`, `raise_for_status`, obsługa pułapki „200 OK z błędem w treści" i pustego `response` → `HTTPException(502)`.
* [x] Transform + Load: `upsert_league_standings` — upsert drużyn i wpisów tabeli przez ORM (unit of work), guard clause 404, bez commita (transakcją zarządza wywołujący), raport liczników.
* [x] `POST /import-standings`: pętla po 6 ligach na jednym `AsyncClient`, query param `season`, jeden commit (all-or-nothing), odpowiedź z raportem per liga.
* [x] Import zweryfikowany (TestClient): 114 drużyn / 114 wpisów; liczby drużyn per liga zgodne (20/20/20/18/18/18); mistrzowie 2024/25 poprawni; idempotencja upsertu potwierdzona (2. przebieg: 0 insertów, same update'y).
* [x] Ruff czysty; zużycie API: 8/100 zapytań; migracji nie przybyło (zmiany tylko w danych).
* **Wynik:** Backend ma komplet danych tabel 6 lig sezonu 2024/25 — gotowe pod publiczne endpointy i testy (Sesja 5).

## Sesja 5 (2026-08-03) — Publiczne endpointy odczytu + pierwsze testy (pytest)
* [x] `app/schemas.py`: `TeamResponse` (bliźniak `LeagueResponse`) i `StandingResponse` z **zagnieżdżonym** `team: TeamResponse` (relacja `Standing.team` + `from_attributes` → jedno zapytanie z frontendu zamiast dwóch).
* [x] `GET /leagues` — rename dawnego `/my-leagues` na konwencję REST (`get_leagues`); grep potwierdził brak wiszących referencji w kodzie.
* [x] `GET /leagues/{league_id}/standings` — path param, `season` jako query param z `DEFAULT_SEASON`, `404` gdy ligi brak, sort po `rank`, `response_model=list[StandingResponse]`.
* [x] `joinedload(models.Standing.team)` przeciw N+1 — demo na żywej bazie: bez niego **21** zapytań (1 + 20 na drużyny), z nim **1** (JOIN). Endpoint zweryfikowany: Liverpool → Arsenal → City (PL 2024/25).
* [x] `pytest 9.1.1` zainstalowany (`requirements.txt` zamrożony); folder `tests/` (`__init__.py` + `test_main.py`), 4 testy przez `TestClient` (root, `/leagues`, standings z `rank==1` i zagnieżdżoną drużyną, błędne id → 404) — 4/4 zielone; Ruff czysty (`app/` + `tests/`).
* **Zmiana trybu pracy:** właściciel sam pisze kod, Claude prowadzi i robi review (nie wpisuje kodu za niego); wyjątek na wyraźną prośbę.
* **Wynik:** API ma czyste endpointy odczytu pod frontend i pierwszą siatkę testów. `app/routers/` odłożone do Sesji 6.

## Sesja 6 (2026-08-05) — Puchary i drabinki (model Fixture, ETL, endpointy bracket)
* [x] Model `Fixture`: dwa klucze obce do `teams` (`home_team_id`/`away_team_id`) + `foreign_keys=` na relacjach; `id` reużyty z API; `date` jako `DateTime`; gole nullable. Migracja Alembic **nr 3** (`03d5cc4db1d2`) — autogenerate, przejrzana, zastosowana.
* [x] Pełny ETL importu meczów: `fetch_fixtures` (Extract, generyczny — działa dla dowolnej rozgrywki), `upsert_team` (helper, `country=None` dla drużyn pucharowych), `upsert_fixtures` (Transform+Load: guard, dedup drużyn, parsowanie daty ISO, upsert po `id`), `POST /import-fixtures` (pętla po 7 pucharach, one commit).
* [x] Odporność ETL na braki danych (decyzja właściciela): pusty `response` → `[]` (toleruj), awarie API (`errors`/HTTP) nadal → `502`. Zastosowane w OBU fetchach.
* [x] Import zweryfikowany na żywo: **1733 mecze / 1267 drużyn / 7 rozgrywek**, sezon 2024. Bug `duplicate key` (przez `autoflush=False` + drużyny grające wiele rund) rozwiązany deduplikacją w pamięci.
* [x] Schematy: `FixtureResponse` (dwie zagnieżdżone drużyny, gole nullable), `BracketRound` (bez `from_attributes` — budowany ręcznie); `TeamResponse.country` → `str | None`.
* [x] `GET /leagues/{id}/fixtures` (płaska lista, podwójny `joinedload`, sort po dacie) + `GET /leagues/{id}/bracket` (grupowanie po rundzie, `dict` insertion order = kolejność turnieju). Drabinka LM 2024/25 zweryfikowana: 17 rund w kolejności, finał PSG 5-0 Inter.
* [x] Porządki: komentarze sekcji endpointów (numeracja → grupy WRITE/READ, PL → EN).
* **Wynik:** Faza 1 backend **kompletna** — ligi + puchary w bazie i API. Do Sesji 7: podział `main.py` na routery (+ helper `query_fixtures`) i testy pytest.

## Sesja 7 (2026-08-05) — Porządki backendu: testy pytest + routery
* [x] **Infrastruktura testowa** (`tests/conftest.py`): izolowana baza SQLite **in-memory** (`StaticPool` + `check_same_thread=False`), podmiana `get_db` przez `app.dependency_overrides`, autouse fixture `reset_database` (czysta baza per test), fixtures `client` i `db_session`.
* [x] **6 testów** endpointów odczytu (Arrange–Act–Assert, seed własnych danych): `/leagues`, `/standings`, `/fixtures`, `/bracket` (dowód sortowania rund po dacie) + root + 404. Testy `/fixtures` i `/bracket` napisał właściciel (Claude: prowadzenie + review).
* [x] **Refaktor `main.py` 522 → 23 linie** na routery: `get_db` → `database.py` (uniknięcie cyklu importów), `app/routers/competitions.py` (odczyty + helper `query_fixtures`, DRY), `app/routers/imports.py` (zapisy + ETL). Wykonany krok po kroku z `pytest` po każdym kroku.
* [x] Weryfikacja: 6/6 testów zielone przez cały refaktor, Ruff czysty, smoke `import app.main` → 12 tras. Zero zapytań do API-Football, bez nowych migracji.
* **Wynik:** Backend Fazy 1 domknięty i uporządkowany (routery + testy). Gotowe pod start frontendu (Sesja 8).

## Sesja 8 (2026-08-10) — Start frontendu (Vite + React + TS), CORS, filtr bracket
* [x] **Frontend od zera:** Node.js v20.20.2 (nvm, w WSL) + npm 10.8.2; `npm create vite@latest frontend -- --template react-ts` (React 19 + Vite 8 + oxlint) + `npm install` (27 paczek). Fundament przez analogię Python→JS (node/npm/package.json/node_modules).
* [x] **Pierwszy komponent** (napisał właściciel): `LeagueCard` (props `{name, country}` typowane, destrukturyzacja, JSX) reużyty 5× w `App`; fragment `<>` + `export default`. Dev-server `npm run dev` (:5173, HMR), render zweryfikowany.
* [x] **CORS** (`CORSMiddleware` w `app/main.py`, origin `http://localhost:5173`, credentials): weryfikacja curlem — preflight `OPTIONS` + `GET` z dozwolonym/obcym origin. Lekcja: CORS to ochrona przeglądarki, nie autoryzacja serwera.
* [x] **Dług spłacony — filtr `knockout_only`** w `GET /leagues/{id}/bracket`: opt-in query param (default `False`) + stała `KNOCKOUT_ROUNDS` w `constants.py`. Diagnostyka realnych rund (CL 17, FA Cup 20). Poprawka po review: default `True`→`False` (kompatybilność wsteczna + semantyka opt-in).
* [x] **2 testy bracket:** `test_get_bracket_all_stages` (default = wszystko + dowód sortu po dacie), `test_get_bracket_with_knockout_only` (filtr). pytest **7/7**, Ruff (`app/` + `tests/`) czysty.
* **Wynik:** Frontend wystartował (działający komponent + CORS gotowy pod fetch w Sesji 9). Backend Fazy 1 dopięty o czysty filtr drabinki knockout. 0 zapytań do API-Football.

## Sesja 9 (2026-08-17) — Interaktywny React + pierwsza tabela na żywych danych
* [x] **`useState` + `useEffect`** (rozgrzewka `Counter`): stan = pamięć + trigger re-render; efekt wg tablicy zależności (`[]` = raz po zamontowaniu), nie co render. Ominięta pułapka `onClick={() => ...}` (funkcja, nie wywołanie).
* [x] **`LeagueTable` z fetchem**: typy TS `Team`/`Standing` jako lustro `schemas.py` (snake_case, `string | null`, zagnieżdżony `team`); idiom async-w-`useEffect`, dwa `await`, `.map` + `key`. `GET /leagues/39/standings` → 20 wierszy; **CORS zagrał na żywo**.
* [x] **Stany loading/error**: `try/catch/finally`, pułapka `res.ok` (`fetch` nie rzuca przy 404 → ręczny `throw` = frontendowy `raise_for_status`), generyk `useState<string | null>`.
* [x] **Tailwind CSS v4** (setup Claude, metoda zweryfikowana WebFetch): `@tailwindcss/vite` + `@import "tailwindcss"` (NIE stara v3). Utility-first, warianty `hover:`/`odd:`, dziedziczenie `text-align`; stylowanie tabeli (właściciel).
* [x] **Porządek**: rozbicie na `src/components/LeagueCard.tsx` + `LeagueTable.tsx` (`import`/`export default`), `App.tsx` = szkielet, usunięty `Counter`; **prettier** dodany (skrypt `npm run format`, odpowiednik `ruff format`).
* [x] **Logo drużyn**: `<img>` + warunkowy render `{logo_url && …}` + flex; poprawka kolumn po review (9 komórek = 9 nagłówków).
* **Jakość:** oxlint 0/0, build (tsc + vite) zielony, format czysty. Backend bez zmian (7/7 testów), 0 zapytań do API-Football.
* **Wynik:** Działa pierwsza tabela ligowa na żywych danych (PL 2024/25), odporna na błędy i ostylowana. Do Sesji 10: routing (React Router) — nawigacja po 6 ligach, `useParams` zamiast zahardkodowanego `39`.

## Sesja 10 (2026-08-17) — Routing i nawigacja (React Router, useParams, Link, layout, env)
* [x] **React Router v7** (`react-router-dom ^7.18.2`): `<BrowserRouter>` w `main.tsx`; teoria SPA (URL → komponent bez przeładowania, History API).
* [x] **Strony vs komponenty**: nowy folder `src/pages/` (`HomePage`, `LeaguePage`); `src/data/leagues.ts` (6 lig, pierwszy `export` nazwany); `<Routes>`/`<Route>` w `App.tsx` (`/` → `HomePage`, `/leagues/:id` → `LeaguePage`).
* [x] **`useParams`**: `LeaguePage` czyta `:id` (zawsze string; strażnik `if (!id)` = zawężanie typu), przekazuje `leagueId` do `LeagueTable`; fetch na template literal; **deps `[leagueId]`** (refetch przy zmianie ligi). Jeden komponent = wszystkie 6 lig (zweryfikowane na żywo: PL/La Liga/Bundesliga). Złapany błąd cudzysłowy zamiast backticków (kompilator nie łapie).
* [x] **`<Link>` + layout**: klikalne karty (`to={` `` `/leagues/${id}` `` `}`, `key` na `Link`), wspólny `<header>` (landmark `banner`) z nagłówkiem-linkiem do `/` nad `<Routes>`; zduplikowany `<h1>` usunięty ze stron.
* [x] **Bazowy URL API w `.env`**: `frontend/.env` + `.env.example` (`VITE_API_URL`), `src/api/config.ts` (`import.meta.env` + `??` fallback, jedno źródło prawdy); `LeagueTable` używa `API_BASE_URL`. Zaszyty `http://localhost:8000` zniknął z kodu. Lekcja: zmienne `VITE_` nie są tajne.
* **Jakość:** `npm run build` (tsc+vite) zielony, `npm run lint` (oxlint) 0/0, `npm run format` (prettier) czysty. Backend uruchamiany tylko do weryfikacji na żywo; **0 zapytań** do API-Football.
* **Wynik:** Nawigacja po 6 ligach działa (klikalne karty ⇄ tabela ligi, bez przeładowania), URL API skonfigurowany przez `.env`. Do Sesji 11: **TanStack Query** — porządne pobieranie danych (cache, `isLoading`/`isError`), refaktor ręcznego fetcha i wspólny klient API.

## Sesja 11 (2026-08-18) — Porządne pobieranie danych (TanStack Query) + kosmetyka Fazy 1
* [x] **TanStack Query** (`@tanstack/react-query ^5.101.4`): `QueryClient` + `QueryClientProvider` owinięty wokół `<App/>` w `main.tsx` (analogicznie do `BrowserRouter`) — „mózg" cache dla całej aplikacji. Teoria: server state (cache, deduplikacja, refetch) vs ręczny `useState`+`useEffect`.
* [x] **Warstwa API** `src/api/standings.ts` (napisana wspólnie): typy `Team`/`Standing` przeniesione z komponentu (modelują dane serwera), `getStandings(leagueId): Promise<Standing[]>` — `fetch` + `if (!res.ok) throw` (most do `isError`, bo `fetch` nie rzuca na 4xx/5xx) + `return res.json()`. Zero `useState`/`try/catch`.
* [x] **Refaktor `LeagueTable` na `useQuery`** (sedno, właściciel): `queryKey: ["standings", leagueId]` (cache per liga, zastępuje deps `[leagueId]`), `queryFn: () => getStandings(leagueId)` (strzałka — nie natychmiastowe wywołanie); 3× `useState` + `useEffect` + `try/catch` → jeden `useQuery`. Strażnik `if (!data) return null` (zawężenie `Standing[] | undefined`); typ `data` **wywnioskowany** z `getStandings` (bez importu `Standing`).
* [x] **Kosmetyka Fazy 1** (Tailwind, `LeagueCard`/`HomePage`/`App`): karty lig — `border`, `rounded-lg`, `p-4`, `shadow-sm`+`hover:shadow-md`, `transition`, `cursor-pointer`; siatka `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4` (pierwsze **responsywne prefiksy**, mobile-first); nagłówek `border-b` + `hover:opacity-80`. Usunięta martwa klasa `league-card`. Odkrycie: **Tailwind preflight** zeruje domyślne style `<a>`/nagłówków.
* [x] **Nowa wizja UX** zanotowana w ROADMAP: HomePage jako rozwijana lista krajów + puchary europejskie (LM/LE/LKonf), accordion → liga/puchar krajowy, klik → tabela/drabinka, selektor roku, zakładka predyktorów (dalszy etap).
* **Jakość:** `npm run build` (tsc+vite) zielony, oxlint 0/0, prettier czysty. Backend bez zmian, **0 zapytań** do API-Football. Praktyczna lekcja: zapis pliku „od spodu" (narzędzie) vs otwarty bufor VS Code → przy przeładowaniu wybrać **Don't Save**.
* **Wynik:** Pobieranie danych na profesjonalnym wzorcu (cache gratis), strona główna wygląda „na serio". Do Sesji 12: **drabinki pucharowe (UI)** — komponent `Bracket` (rundy jako kolumny) + `useQuery` dla `GET /leagues/{id}/bracket`; ewentualnie start przebudowy nawigacji wg nowej wizji.

