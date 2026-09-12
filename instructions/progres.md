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

## Sesja 12 (2026-08-19) — Drabinki pucharowe (drzewko turniejowe) + nawigacja + doimport LE/Konf
* [x] **Backend — doimport Ligi Europy (3) i Konferencji (848)**: `constants.py` +2 id w `EUROPEAN_COMPETITION_IDS` (dzięki merge `**` rozprowadzone „wszędzie" z jednego miejsca). Import: **13→15 rozgrywek**, **+678 meczów** (LE 269 / Konf 409), **+137 drużyn**.
* [x] **Backend — naprawa latentnego buga importu**: `duplicate key teams_pkey` przy drużynach grających w kilku europejskich pucharach. Przyczyna: `seen_team_ids` per-rozgrywka + `autoflush=False` (obiekt `pending` niewidoczny dla `db.query`) → podwójny `db.add`. Poprawka: **jeden wspólny `seen_team_ids` na cały import** (parametr `upsert_fixtures`). Testy 7/7, Ruff czysty. Lekcja: „działa" ≠ „poprawne" — ukryte założenie obalone nowymi danymi.
* [x] **Frontend — ścieżka drabinki**: `api/bracket.ts` (typy `Fixture`/`BracketRound` + `getBracket` z `knockout_only=true`), `components/Bracket.tsx` (`useQuery(["bracket", id])` + guardy), `pages/BracketPage.tsx` + trasa `/bracket/:id`. Nazwa `BracketPage` (nie `CupPage`) — od widoku, bo część „pucharów" ma fazę ligową. Wzorzec 1:1 ze standings.
* [x] **Frontend — drzewko turniejowe**: layout schodkowy (`items-stretch` + `justify-around` = wyśrodkowanie co do piksela, bez linii, `overflow-x-auto`). `groupIntoMatchups` — grupowanie dwumeczów po nieuporządkowanej parze drużyn (mapowanie goli mimo zamiany home/away). `MatchupCard` — herby + wyniki legów w pudełkach; dla dwumeczu nagłówki `1/2/Σ` + **agregat**. Odporne na mieszane rundy (Copa del Rey: single + dwumecz). Zwężenie 1152→910px.
* [x] **Frontend — nawigacja przez kraje**: model `COUNTRIES` (kraj → liga + puchar) + `EUROPEAN_COMPETITIONS` w `data/leagues.ts` (usunięte stare `LEAGUES`); `HomePage` jako 7 rozwijanych sekcji przez natywny **`<details>`** (6 krajów + „European Competitions"), linki liga→`/leagues/:id`, puchar/europejskie→`/bracket/:id`. Usunięty martwy `LeagueCard.tsx`.
* [x] **Nauka**: komponent Reacta nie jest `async` (rysuje bieżący stan, `useQuery` przerysowuje); drzewko przez flexbox; `?? "-"` vs `|| "-"` (0 to valid); `key` na elemencie w `.map`, wrapper na zewnątrz; error vs warning; skąd uczyć się flexboxa (Froggy/CSS-Tricks/Tailwind docs/DevTools); WSL: `npm run dev` wymaga jawnego `. ~/.nvm/nvm.sh` (systemowy node v12 wywala Vite).
* **Jakość:** `npm run build` (tsc+vite) zielony, oxlint **0/0**, prettier czysty; pytest **7/7**, Ruff czysty. Zużycie API-Football: ~19 zapytań (doimport + retry po bugu).
* **Wynik:** **Faza 1 domknięta** — od HomePage klika się do każdej tabeli i drabinki; drabinki jako drzewka turniejowe. Do Sesji 13 (decyzja na starcie): tabela fazy ligowej (LM/LE/Konf) / szlify Fazy 1 (responsywność, skeletony) / upiększacze drabinki.

## Sesja 13 (2026-08-20) — Selektor sezonu (tabele) + daty w drabince + decyzja źródła Fazy 2
* [x] **Decyzja kierunku i źródła danych**: start Fazy 2 (core), ale najpierw daty w drabince + selektor sezonu. Blocker Fazy 2 (Free API tylko 2022–2024, brak żywego sezonu) rozwiązany decyzją: **właściciel kupuje API-Football premium** — spójne ID z bazą (zero mapowania), puchary, bieżący sezon + historia z jednego źródła. Ryzyko #1 domknięte.
* [x] **Krok 1 — daty/godziny w drabince** (tylko frontend; backend już wysyłał `date`): `api/bracket.ts` — `date` przeniesione przez `groupIntoMatchups` do `legs` (dana per mecz, jak gole); `components/MatchupCard.tsx` — helper `formatDate` (`toLocaleString("pl-PL", {dateStyle, timeStyle: "short"})`, auto strefa UTC→lokalna) + wiersz dat `legs.map(...).join(" / ")`. Format `12.03.2025, 21:00`.
* [x] **Krok 2 — backend endpoint `GET /leagues/{id}/seasons`** (napisał właściciel): `query(Standing.season).filter(league_id).distinct().order_by(desc())`, wyłuskanie krotek pętlą (`row[0]`), `response_model=list[int]`. Pyta bazę o prawdę zamiast listy na sztywno.
* [x] **Krok 2 — dane**: doimport standings **2022 i 2023** przez istniejący `POST /import-standings?season=` (endpoint już parametryzowany — zero kodu). `seasons` zwraca `[2024, 2023, 2022]`. ~12 zapytań API.
* [x] **Krok 2 — frontend**: `api/standings.ts` — `getStandings(leagueId, season)` (+`?season=`) i nowa `getSeasons(): number[]`; `LeagueTable` — prop `season` + **`season` w `queryKey`** (osobny cache per sezon); `LeaguePage` — `useState` wybranego sezonu (UI state) + `useQuery(getSeasons)` (server data) + kontrolowany `<select>` (`Number(e.target.value)`), reguły hooków (guard pod hookami), `enabled: !!id`.
* [x] **Poprawka selektora**: pozycja (natywny `<select>` popup zasłaniał tabelę → `flex justify-end`, potem właściciel na lewo); **bug review**: `justify-begin` nie istnieje w Tailwind (działał przypadkiem — flex domyślnie start) → `justify-start`.
* **Nauka**: front↔backend tylko przez URL (parametr funkcji ≠ dana serwera); path param (pozycja) vs query param (nazwa); parametr z default = opcjonalny, bez = wymagany; query 1 kolumny → lista **krotek** `(2024,)`, `DISTINCT`; **server state (useQuery) vs UI state (useState)** — refaktor S11 dotyczył tylko danych serwera; `queryKey` musi zawierać `season`; reguły hooków; `toLocaleString` auto-strefa.
* **Jakość**: build zielony, oxlint 0/0, prettier czysty; Ruff czysty, pytest **7/7** (dług: brak testu `seasons`). ~12 zapytań API-Football.
* **Wynik**: Tabele ligowe są **wielosezonowe** (2022–2024, przełączane selektorem), drabinki mają daty meczów. Do Sesji 14: selektor dla drabinek + (po premium) właściwa Faza 2 (wyniki/terminarz drużyn).

## Sesja 14 (2026-08-31) — Selektor sezonu (drabinki) na `UNION` + premium Pro + doimport 2025/2026
* [x] **Decyzje**: premium kupione (**plan Pro**); zaczynamy od selektora drabinek (Fazę 2 na S15). Architektura listy sezonów — **opcja B (`UNION`)** zamiast osobnego endpointu (DRY; front zostaje z jednym `getSeasons`).
* [x] **Krok 1 — backend `/leagues/{id}/seasons` na `UNION`** (napisał właściciel): problem — puchary nie mają wierszy w `standings`, więc stary endpoint zwracał `[]` dla drabinek. Rozwiązanie: dwa pod-zapytania (`Standing.season` + `Fixture.season`) złączone `.union()`, potem `.all()`, wyłuskanie `row[0]`, `sort(reverse=True)`. Bugi z review: `.all()` na pod-zapytaniach (materializacja `Query`→`list`, brak `.union()` → `AttributeError`); zbędne `.distinct()/.order_by()` (UNION dedupuje); `sort()`→`sort(reverse=True)`. Weryfikacja curl: FA Cup `[2024]`, PL `[2024,2023,2022]`.
* [x] **Krok 2 — `getBracket(leagueId, season)`** (`api/bracket.ts`): `season` jako drugi, wymagany argument **przed** opcjonalnym `knockoutOnly` (reguła TS); `&season=` w URL.
* [x] **Krok 3 — `Bracket`** (`components/Bracket.tsx`): prop `season`, `queryKey: ["bracket", leagueId, season]` (cache per sezon), `getBracket(leagueId, season)`. Wzorzec 1:1 z `LeagueTable`.
* [x] **Krok 4 — selektor na `BracketPage`**: `useState` sezonu + `useQuery(getSeasons)` (ten sam co `LeaguePage`) + kontrolowany `<select>`, guard pod hookami. Bug review: `useState(2026)`→`2024` (brak fixtures 2026 wtedy → pusta drabinka + rozjazd controlled select). Dług UX: default = najnowszy z listy zamiast hardkodu.
* [x] **Krok 5 — dane (premium)**: `/status` → Pro, 7500/dobę, do 2026-10-01. Dostęp do sezonów 2025 i 2026 zweryfikowany (standings + fixtures; Free dawał tylko 2022–2024). Doimport: standings 2025/2026 (2×114), fixtures 2025 (**2430** meczów) + 2026 (**1052**). Copa del Rey/Coupe de France 2026 = 0 (puchary nie ruszyły — ETL toleruje). Weryfikacja `/seasons`: Copa del Rey `[2025,2024]` (bez 2026 — prawda z bazy).
* **Nauka**: `UNION` (dedup, ta sama kolumna po obu stronach); `Query` (leniwe, `.union()`) vs `.all()` (materializacja w `list`); anatomia URL (ścieżka `/` = zasób, query `?`/`&` = opcje); kolejność argumentów funkcji (pozycyjna) ≠ query paramów w URL (nazwana); kontrolowany `<select>` z value spoza opcji = rozjazd; **WSL: `bash -ic` (nvm→Node v20) vs `bash -lc` (systemowy v12, wywala `tsc` na `??`)**.
* **Jakość**: `npm run build` (tsc+vite) zielony; Ruff czysty; pytest **7/7** (dług: brak testu `seasons`). Baza po imporcie: **leagues 15, teams 1959, standings 572, fixtures 5893**. API-Football (Pro): ~30 zapytań importu + kilka diagnostycznych.
* **Wynik**: Drabinki są **wielosezonowe** (FA Cup/CL: 2024–2026), a w bazie są **żywe dane 2026/27** — brama do Fazy 2 otwarta. Do Sesji 15: dług test `/seasons` + start Fazy 2 (wyniki/terminarz drużyn + wyszukiwarka) na żywych danych.

## Sesja 15 (2026-09-01) — Start Fazy 2 (backend): mecze drużyn + wyszukiwarka
* [x] **Dług z S14 — test `GET /leagues/{id}/seasons`** (napisał właściciel): scenariusz **szczelny** — sezon tylko w `standings` (2023), tylko w `fixtures` (2025), w obu (2024→dedup); każdy broni innej części `UNION`. Bug review: `sorted(data) == [...]` (rosnąco vs lista malejąca — test by padł i zamazywał sortowanie) → `assert data == [2025,2024,2023]` (zawartość + dedup + kolejność naraz). pytest **7/7 → 8/8**.
* [x] **B1 — import meczów ligowych** (rozszerzenie `POST /import-fixtures`, opcja A): helpery `fetch_fixtures`/`upsert_fixtures` są **generyczne**, więc wystarczyło `competitions = TARGET_LEAGUE_IDS` (15 rozgrywek). Rename `cups_report`→`competitions_report`. F401 po refaktorze (`TARGET_LEAGUE_IDS` osierocił `DOMESTIC_CUP_IDS`/`EUROPEAN_COMPETITION_IDS` — usunięte; `DOMESTIC_LEAGUE_IDS` został dla `import_standings`).
* [x] **Import 2026 (na żywo)**: ligi = same INSERT-y (PL/La Liga/Serie A po **380**, Bundesliga/Ligue 1/Primeira po **306** — zgodne z wielkością lig; razem **2058**); puchary/europejskie = **1052 UPDATE** (te z S14 → dowód idempotencji, 0 duplikatów). `fixtures`: 5893 → **7980**, teams 1959 → **1962**.
* [x] **B2 — `GET /teams/{id}/past-matches`** (nowy router `app/routers/teams.py` + wpięcie w `main.py`): stała `FINISHED_STATUSES = {FT,AET,PEN}`; guard 404, `or_(home==id, away==id)` (**pierwszy raz LUB**), `status.in_(...)`, `order_by(date.desc())`, `limit(last)`, `joinedload`. Weryfikacja na żywo (Man City): 5× `FT`, malejąco, u siebie i na wyjeździe.
* [x] **B3 — `GET /teams/{id}/future-matches`**: bliźniak z `status == "NS"`, `order_by(date.asc())`, `next: int = 5`. Weryfikacja: 5× `NS`, rosnąco, gole `null`; dzisiejsza data (1 wrz) rozdziela past (do 28 sie) od future (od 5 wrz).
* [x] **B4 — `GET /teams?search=...`**: `Team.name.ilike(f"%{search}%")` + `order_by(name)` + `limit(20)`, reużyty `TeamResponse`. Weryfikacja: `?search=real` (łapie Villarreal/Montreal — wzorzec „zawiera"), `?search=MANCHESTER` (case-insensitive).
* **Decyzje**: import lig = rozszerzenie istniejącego endpointu (DRY, maszyneria generyczna); „rozegrany" przez `status` nie datę; nazwy `past-matches`/`future-matches` (kolizja `fixtures` z `get_league_fixtures`; `games`→`matches`); URL kończy się rzeczownikiem.
* **Nauka**: szczelność testu; `ruff check` (F401, lint) ≠ `ruff format` (styl); ligi+puchary w jednej tabeli `leagues`; `APIRouter` + `include_router` (bez wpięcia = 404); path/query/dependency params; `or_`/`.in_`/`.desc()`/`.asc()`/`.limit()`; `ilike`+`%` (bind param = brak SQL injection); status `FT/AET/PEN` vs `NS`; `next` przesłania builtina; nazwa funkcji ≠ URL; `\n` na końcu pliku (POSIX).
* **Jakość**: Ruff czysty, pytest **8/8**. API-Football (Pro): ~15 zapytań importu.
* **Wynik**: **Backend Fazy 2 kompletny** — import ligowy + 3 endpointy o drużynach, zweryfikowane na żywych danych 2026. Do Sesji 16: testy nowych endpointów (rozgrzewka) + **frontend Fazy 2** (wyszukiwarka z debounce + ulubione w `localStorage`, hook `useFavorites`) + dług UX (domyślny sezon `seasons[0]`).

## Sesja 16 (2026-09-04) — Frontend Fazy 2 (wyszukiwarka + podgląd meczów) + ciemny motyw
* [x] **Zmiana zakresu Fazy 2**: właściciel rezygnuje z „ulubionych" (`localStorage`/`useFavorites`/dashboard). Feature = **wyszukiwarka drużyn + podgląd ich meczów** (świadome zawężenie MVP).
* [x] **Rozgrzewka — testy 3 endpointów z S15** (napisał właściciel): `past-matches` (scenariusz szczelny A/B/C/D), `future-matches` (lustro `NS`+`asc`; dane spójne z domeną — `NS` bez goli), `search_teams` („zielone ≠ szczelne": fraza `eSTEr` = substring w środku + asercje **po indeksie** bronią `ilike`/`order_by`; pusty wynik), `team_not_found` (404 past+future). pytest **8 → 12**. Lekcje: seed spełnia `NOT NULL`; `"""..."""` w środku funkcji to nie komentarz (martwy string).
* [x] **`api/teams.ts`**: `searchTeams`/`getPastMatches`/`getFutureMatches` (wzorzec `standings.ts`, reuse typów przez `import type`, `encodeURIComponent`). Decyzja: NIE dublować domyślnej `5` na froncie (backend rządzi — DRY/YAGNI); `teamId: string`.
* [x] **`hooks/useDebounce.ts`** (custom hook, nowy folder `hooks/`): `useState`+`useEffect`+`setTimeout` z cleanupem `clearTimeout` (przy każdym znaku kasuje stary timer → tylko przerwa ≥ delay przepuszcza). Weryfikacja na żywo: „barca" (5 znaków szybko) → **1 zapytanie**, nie 5.
* [x] **`SearchPage.tsx`** (+ trasa `/teams`): kontrolowany `<input>` → `useDebounce(300)` → `useQuery` (`queryKey` z frazą, `enabled: length>0`); render stanów przez **zmienną + `if`** (input musi zostać na ekranie — nie early return). „real" → 12 drużyn (substring: Montreal/Villarreal).
* [x] **`TeamPage.tsx`** (+ trasa `/teams/:id`): dwa `useQuery` (guardy **PO** hookach — Reguła Hooków; `if (!past||!future) return null` = **zawężenie typu** → koniec `?.` w renderze); adapter `fixtureToMatchup` lokalnie; **reuse `MatchupCard`** (pojedynczy mecz = „dwumecz z jedną nogą"); nagłówek (logo+nazwa wyłuskane z pierwszego meczu) + **dwie kolumny** past/future (`flex gap-8`, `flex-1`). Weryfikacja: „real"→klik Real Madrid→`/teams/541`→mecze (cross-competition).
* [x] **Klikalne wyniki** (`Link to={/teams/:id}`) + karta „Find team" na HomePage. Pełna pętla (szukam→klikam→widzę mecze) zweryfikowana end-to-end.
* [x] **Wymuszony ciemny motyw dla wszystkich**: `index.css` — wartości dark w `:root` + `color-scheme: dark` + usunięta bramka `@media (prefers-color-scheme)`. `MatchupCard` rozjaśniony pod dark (`bg-gray-800`/`700`). **Odłożone**: dark-polish reszty komponentów (tabela ligowa, hovery).
* [x] `.vscode/settings.json` (lokalny, poza gitem) — format-on-save Ruff/Prettier per język.
* **Nauka (React od podstaw, bardzo dużo)**: hooki (definicja + reguły + custom hook); `useEffect` (callback po renderze + cleanup + tablica zależności); `() =>` jako callback; `setTimeout`; `A && B`/ternary/`if`+zmienna w JSX; `??`/`?.` vs jawny `if`; `let` vs `const`; **render = snapshot** (nowe `const` co render, pamięć żyje w `useState`); **`import type` vs wartość** (typ wymazany w JS → runtime „does not provide an export"); **zawężanie typu** `if(!x)return`; **warstwy CSS Tailwind v4** (nielayerowany CSS bije utilki → globalny `h1` z szablonu `index.css` nadpisywał `mb-4`/`text-2xl`); **flexbox 2 osie** (`items-*`=pion, `justify-*`=poziom); `text-*` przeciążone (rozmiar vs kolor); prettier NIE formatuje kodu z błędem składni; WSL/Vite — watcher ślepy na zapisy z Windows (restart dev-servera).
* **Jakość**: pytest **12/12** + Ruff czysty; frontend `tsc` + oxlint **0/0** + prettier czysty. Baza bez zmian (leagues 15, teams 1962, standings 572, fixtures 7980). API-Football: tylko odczyty weryfikacyjne (backend uvicorn lokalnie).
* **Wynik**: **Rdzeń Fazy 2 gotowy** — wyszukiwarka + podgląd meczów, klikalny, z HomePage, na ciemnym motywie. Do Sesji 17: krótki **close-out Fazy 2** (dark-polish komponentów + domyślny sezon = najnowszy) → **START Fazy 3 (model Poissona)**.

## Sesja 17 (2026-09-12) — Close-out Fazy 2 + Faza 3 backend (model Poissona)
* [x] **Close-out Fazy 2**: dark-polish `LeagueTable` (nagłówek/hover/ramki — sztywne kolory Tailwinda nie reagują na motyw), hover `MatchupCard` (`group`/`group-hover:`/`transition-colors` — biały tekst+ramka, agregat żółty), empty states `Bracket`+`SearchPage` (lekcja: `!data` vs `.length===0` — pusta tablica jest truthy).
* [x] **Hook `useSeasonSelector`** (DRY z `LeaguePage`+`BracketPage`): domyślny sezon = najnowszy przez **derived state** `selectedSeason ?? seasons?.[0]` (nie kopiować stanu serwera do `useState`). Bug review: typ `number|null`, nie `string` (HTML value to string, ale konwertujemy `Number`).
* [x] **Teoria Poissona** (krok po kroku): λ → rozkład P(k); siła ataku/obrony względem bazy ligowej; `λ=baza×atak×obrona`; macierz (`np.outer`) → trójkąty → P(1/X/2). Baza uwzględnia rywala + utrzymuje skalę.
* [x] **numpy 2.2.6** + nowy pakiet `app/prediction/`. **`poisson.py`** (5 fn: pmf/distribution/score_matrix z normalizacją/outcome/top_scorelines). **`strength.py`** (3 fn: `league_baseline` `func.sum`/`.scalar()`, `team_attack_defence`, `match_lambdas` + `HOME_ADVANTAGE=1,3`). Weryfikacja: λ 1,96/0,95 → 61/21/18; Barca atak 1,86/obrona 0,70; baza Bundesliga 1,618 (golowa — realizm).
* [x] **Endpoint `GET /predict`** (`routers/predictions.py` + rejestracja): walidacja 404 (drużyny w standings), pipeline, `float()` fix; schematy `PredictionResponse`/`ScoreLine`. Barca vs Oviedo → 92,7/5,3/1,8%, top 3:0.
* [x] **Testy**: `tests/test_poisson.py` (5, known-values) + 2 testy `/predict` (**pytest 12→19**). Test złapał realny problem (suma 0,999 przy wysokim λ → **normalizacja macierzy**).
* **Decyzje**: **3 modele** (bazowy Poisson → ulepszony Dixon-Coles → ML); źródło **standings** (fixtures ligowe za ubogie); predyktor **within-league** (siła względna do ligi); `GET` nie `POST`. **Nowy cel/harmonogram**: beta z predyktorem do 13 wrz (UI), **deploy + README + CV po powrocie ~26 wrz** — priorytet MVP na deploy PRZED Fazą 4/5.
* **Nauka**: Poisson/λ; model siły (baza jako odniesienie, uwzględnia rywala); numpy (`outer`/`tril`/`triu`/`trace`, normalizacja); `func.sum`+`.scalar()` vs `.all()`; `list` (klasa) vs `[]`; derived state; `!data` vs `.length===0`; `group-hover`; separacja matematyka/DB/API; GET dla odczytu.
* **Jakość**: pytest **19/19**, Ruff czysty; frontend `tsc`+oxlint **0/0**. Baza bez zmian (leagues 15, teams 1962, standings 572, fixtures 7980). API-Football: **0 zapytań**.
* **Wynik**: **Faza 2 domknięta + backend Fazy 3 (predyktor Poissona) KOMPLETNY**. Do Sesji 18 (sprint do 13 wrz): **UI predyktora** (wybór ligi → 2 drużyny → paski 1/X/2 + top wyniki).

