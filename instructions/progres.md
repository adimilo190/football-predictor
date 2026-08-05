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

