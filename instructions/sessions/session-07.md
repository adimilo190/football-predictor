# Sesja 7 — 5 sierpnia 2026

> Sesja porządkowa backendu przed frontendem: testy pytest z izolowaną bazą + podział `main.py` na routery.
> Kolejność świadomie odwrócona względem planu Sesji 6: **najpierw testy** (siatka bezpieczeństwa), **potem refaktor**.

## Co zostało zrobione

### 1. Infrastruktura testowa (`tests/conftest.py`)
Diagnoza na wejściu: 4 istniejące testy **uderzały w dev bazę** (`football_db`) i zależały od danych z Sesji 4–6 — kruche, padłyby na świeżym klonie lub w CI. Zbudowaliśmy izolowaną bazę testową:
- **Silnik testowy:** SQLite **in-memory** (`sqlite:///:memory:`) z `connect_args={"check_same_thread": False}` i **`poolclass=StaticPool`** (jedno współdzielone połączenie — inaczej każde nowe połączenie do `:memory:` to osobna pusta baza, a test i endpoint patrzyłyby w różne bazy).
- **`TestingSessionLocal`** — fabryka sesji `bind`-owana do testowego silnika (te same ustawienia co produkcyjny `SessionLocal`, m.in. `autoflush=False`, żeby testy odtwarzały realne zachowanie).
- **`override_get_db` + `app.dependency_overrides[get_db]`** — podmiana zależności bazy: endpointy bez zmian dostają sesję do bazy testowej.
- **`reset_database` (autouse fixture)** — `create_all` przed każdym testem, `drop_all` po (`yield` dzieli setup/teardown). Każdy test dostaje **czysty blat** → brak wycieku danych między testami.
- **`client` i `db_session`** (fixtures) — pierwszy wysyła żądania HTTP in-process, drugi seeduje dane wprost do bazy testowej.

### 2. Testy endpointów odczytu (6 zielonych)
Wzorzec **Arrange–Act–Assert**: test sam sieje dane, których potrzebuje, i robi **precyzyjne** asercje (`len == 1` + konkretne wartości, nie mgliste `> 0`).
- `test_get_leagues` — seed 1 ligi → lista z tą ligą.
- `test_get_standings` — seed **trzech powiązanych rekordów** (liga + drużyna + standing), bo `StandingResponse` zagnieżdża drużynę.
- `test_get_fixtures` — seed ligi + 2 drużyn + meczu; spójność `home_team_id`/`away_team_id` z wstawionymi drużynami.
- `test_get_bracket` — **kluczowy:** mecze wstawione w kolejności **odwrotnej** do chronologicznej (Final przed Semi), asercja dowodzi, że endpoint sortuje **po dacie**, nie po kolejności wstawiania.
- Zachowane `test_read_root` i `test_standings_unknown_league_returns_404`.
- Testy `/fixtures` i `/bracket` **napisał właściciel samodzielnie** (Claude: specyfikacja + review). Złapane realne błędy: brak `import datetime`, duplikat primary key (`id=10` dla dwóch meczów → `IntegrityError`).

### 3. Refaktor: podział `main.py` (522 → 23 linie) na routery
Wykonany **krok po kroku, z `pytest` po każdym kroku** (siatka 6 testów jako regresja):
- **Krok 1:** `get_db` przeniesiony do `app/database.py` (obok `SessionLocal`). Powód: routery muszą importować `get_db` bez **cyklu importów** — `main.py` importuje routery, więc routery nie mogą importować z `main.py`. `conftest.py` zaktualizowany, by podmiana celowała w `get_db` z `database.py`.
- **Krok 2:** `app/routers/competitions.py` — 4 endpointy **odczytu** (`leagues`, `standings`, `fixtures`, `bracket`) + **helper `query_fixtures`** (guard 404 + `joinedload` home/away + sort po dacie). DRY: `get_league_fixtures` skurczył się do jednej linii, `bracket` woła ten sam helper — koniec duplikacji.
- **Krok 3:** `app/routers/imports.py` — 3 endpointy **zapisu** (`import-*`) + helpery ETL (`fetch_*`, `upsert_*`) + `HEADERS`, przeniesione **słowo w słowo**.
- `main.py` → chudy „spis treści": `app = FastAPI()`, dwa `include_router(...)`, health check. `pytest`: 6/6, Ruff czysty, smoke `import app.main` → 12 tras.

## Decyzje (i dlaczego)
- **Testy przed refaktorem** — testy jako *regression safety net*: po każdym przeniesieniu kodu `pytest` w 0,1 s potwierdzał brak regresu. To jedna z najważniejszych ról testów w prawdziwej pracy.
- **SQLite in-memory zamiast osobnej bazy Postgres** (decyzja właściciela) — zero setupu, błyskawiczne, testy działają wszędzie bez stawiania Postgresa (klucz dla przyszłego CI, Sesja 24). Ryzyko różnic silnika przy naszych prostych zapytaniach = pomijalne.
- **`get_db` w `database.py`, nie w `main.py`** — jedyny sposób na uniknięcie cyklu importów po wprowadzeniu routerów. `database.py` niczego nie importuje z routerów, więc jest bezpiecznym domem dla zależności.
- **`query_fixtures` jako wspólny helper** (nie „endpoint woła endpoint") — dług DRY z Sesji 6 spłacony: guard + zapytanie w jednym miejscu, oba endpointy (`fixtures`, `bracket`) na nim stoją.
- **ETL przeniesiony słowo w słowo** — testy nie pokrywają importów (wołają API-Football), więc przy przenoszeniu zero zmian logiki; `pytest` (collection) + smoke `import app.main` weryfikują brak literówek/importów.
- **Jawne pętle w `bracket` zachowane** (nie zamienione na comprehension) — zgodnie z zasadą czytelności dla początkującego.

## Czego się nauczyliśmy (do utrwalenia)
- **Izolacja testów = osobna baza + `dependency_overrides` + czyszczenie per test.** Dobry test jest samowystarczalny i powtarzalny; nie zależy od stanu dev bazy.
- **Pułapka SQLite `:memory:`** — każde połączenie to osobna baza; `StaticPool` wymusza jedno wspólne. Plus `check_same_thread=False` dla `TestClient` (osobny wątek).
- **`autouse` fixture + `yield`** — automatyczny setup/teardown dla każdego testu bez proszenia argumentem.
- **`close()` sesji ≠ czyszczenie bazy** — sesja to „rozmowa"; zamknięcie nie kasuje zacommitowanych danych. Izolacja danych wymaga aktywnego `drop_all`/`create_all`.
- **Dane testowe są zmyślone i niezależne od dev bazy** — liczy się tylko **spójność wewnętrzna** seeda (`fixture.home_team_id` musi wskazywać wstawioną drużynę).
- **`import datetime` (moduł) vs `from datetime import datetime` (klasa)** — znów! `datetime.datetime(...)` wymaga pierwszego, `datetime(...)` drugiego.
- **Primary key jest unikalny** — dwa rekordy z tym samym `id` → `IntegrityError` (baza chroni przed bałaganem).
- **`APIRouter` + `include_router`** — router to „mini-aplikacja"; `main.py` staje się spisem treści, endpointy żyją w tematycznych plikach; `tags=[...]` grupuje je w Swaggerze.
- **Cykl importów** — dlatego współdzielone zależności (`get_db`) idą do warstwy, której nikt „w górę" nie importuje.
- **Ruff jako test refaktoru** — martwy import po wycięciu kodu = `F401`; brak uwag = wycięliśmy dokładnie tyle, ile trzeba.

## TODO na Sesję 8 (start frontendu — dawna Sesja 7 z ROADMAP)
1. **Node.js w WSL przez `nvm`** — instalacja; co to `npm` i `package.json`.
2. **`npm create vite@latest frontend`** → React + TypeScript; tour po wygenerowanych plikach.
3. **Uruchomienie dev-servera Vite**, pierwszy własny komponent.
4. **CORS w FastAPI** (`CORSMiddleware`) — żeby przeglądarka pozwoliła frontendowi (inny port) gadać z backendem. Dodać do `app/main.py` (albo osobny moduł konfiguracji).
5. (opcjonalnie, dług z Sesji 6/7) **filtrowanie rund w `bracket`** — query param albo lista „głównych rund" dla czystej drabinki knockout.

## Stan repo po sesji
- Gałąź `main`. Nowe pliki: `tests/conftest.py`, `app/routers/__init__.py`, `app/routers/competitions.py`, `app/routers/imports.py`. Zmienione: `app/main.py` (522→23), `app/database.py` (+`get_db`), `tests/test_main.py` (6 testów, fixtures `client`/`db_session`).
- **Testy: 6/6 zielone.** Ruff (`app/` + `tests/`) czysty, formatowanie OK. Smoke `import app.main` → 12 tras.
- Migracji **nie przybyło** (zmiany tylko w kodzie, nie w schemacie). Baza dev bez zmian.
- API-Football: **0 zapytań** dziś (testy działają na bazie in-memory, refaktor bez ruchu do API).
- **Commit + push robi właściciel** (proponowany message poniżej).

## Praca domowa
### 🔴 Priorytet 1 — przed Sesją 8 (start frontendu)
1. **Node.js + nvm w WSL** · https://github.com/nvm-sh/nvm#installing-and-updating — instalacja `nvm`, potem `nvm install --lts`. Na co patrzeć: dlaczego `nvm` (przełączanie wersji Node), że instalujemy **w WSL**, nie w Windows.
2. **Vite — Getting Started** · https://vite.dev/guide/ — czym jest Vite (dev-server + bundler) i po co. Na co patrzeć: komenda `npm create vite@latest`, wybór szablonu **react-ts**, co robi `npm install` i `npm run dev`.
3. **React — Quick Start** · https://react.dev/learn — fundament: komponent = funkcja zwracająca JSX. Na co patrzeć: JSX, komponenty, propsy (na razie bez `useState`/`useEffect` — to Sesja 9).
4. **FastAPI — CORS (CORSMiddleware)** · https://fastapi.tiangolo.com/tutorial/cors/ — dlaczego przeglądarka blokuje żądania między portami i jak to odblokować. Na co patrzeć: `allow_origins` (adres dev-servera Vite, np. `http://localhost:5173`), `add_middleware`.

### 🟢 Priorytet 2 — bez terminu
5. **TypeScript for JS devs** · https://www.typescriptlang.org/docs/handbook/typescript-in-5-minutes.html — po co typy w JS. Na co patrzeć: typowanie prostych wartości i kształtu obiektu (przyda się do typów odpowiedzi API).

**Metoda:** czytaj z otwartym repo — po instalacji Node zobejrzysz strukturę projektu Vite obok naszego backendu. CORS przetestujemy dopiero, gdy frontend faktycznie zawoła `GET /leagues`.
