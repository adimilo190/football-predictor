# Sesja 5 — 3 sierpnia 2026

## Co zostało zrobione
1. **Schematy Pydantic `TeamResponse` i `StandingResponse`** (`app/schemas.py`). `TeamResponse` to bliźniak `LeagueResponse`. `StandingResponse` wprowadza **zagnieżdżony schemat**: pole `team: TeamResponse` zamiast gołego `team_id` — dzięki relacji `Standing.team` + `from_attributes` Pydantic sam buduje drużynę, więc frontend dostaje komplet (nazwa + logo) jednym zapytaniem.
2. **`GET /leagues`** — rename dawnego `/my-leagues` na konwencję REST (zasób = rzeczownik w liczbie mnogiej); funkcja `get_leagues`. Grep potwierdził brak wiszących referencji w kodzie (tylko wzmianki w dokumentacji).
3. **`GET /leagues/{league_id}/standings`** — nowy endpoint: path param `{league_id}`, query param `season: int = DEFAULT_SEASON`, `404` gdy ligi brak w bazie, sortowanie po `rank`, `response_model=list[StandingResponse]`.
4. **`joinedload` przeciw N+1** — `.options(joinedload(models.Standing.team))` w zapytaniu standings. Demo na żywej bazie pokazało: bez joinedload **21 zapytań** (1 + 20 osobnych SELECT-ów na drużyny), z joinedload **1 zapytanie** (JOIN). Endpoint zweryfikowany na danych: Liverpool → Arsenal → City (PL 2024/25).
5. **Pierwsze testy (pytest)** — `pytest 9.1.1` zainstalowany + `requirements.txt` zamrożony. Folder `tests/` (`__init__.py` + `test_main.py`). 4 testy przez `TestClient` (root, `/leagues`, standings z `rank==1` i zagnieżdżoną drużyną, błędne id → 404) — **wszystkie zielone**. Ruff czysty (`app/` + `tests/`).

## Decyzje (i dlaczego)
- **ZMIANA TRYBU PRACY (kluczowa):** właściciel sam pisze kod, Claude tłumaczy koncept, wskazuje plik/miejsce i robi review — **nie wpisuje kodu za niego**. Wyjątek tylko na wyraźną prośbę „zrób/pisz". Powód: to projekt do nauki, wyręczanie odbiera sens. Zapisane w pamięci Claude.
- **Zagnieżdżony `StandingResponse`** (a nie gołe `team_id`) — jedno zapytanie z frontendu zamiast dwóch; pokazuje siłę `relationship` + `from_attributes`.
- **Sezon jako query param z domyślną wartością** (nie path param) — `/leagues/39/standings` działa „od ręki" na domyślnym sezonie, a `?season=2023` pozwala wybrać inny. Spójne z `import_standings`. Domyślna wartość ≠ blokada.
- **`joinedload` teraz, nie „kiedyś"** — problem N+1 pokazany na żywo (21→1), żeby był zrozumiały, a nie magiczny.
- **Testy na razie na prawdziwej bazie deweloperskiej** — świadomy kompromis MVP; osobna baza testowa (override `get_db`) to refaktor na później.
- **`app/routers/` odłożone do Sesji 6** — `main.py` (~290 linii, 5 endpointów) wciąż czytelny; `APIRouter` opłaci się przy endpointach meczów/pucharów, jako naturalna lekcja porządkowania.

## Czego się nauczyliśmy (do utrwalenia)
- **Zagnieżdżone schematy Pydantic** — `team: TeamResponse` + `from_attributes` czyta relację ORM automatycznie.
- **Path param `{...}` vs query param `?...`**; **wartość domyślna ≠ blokada** (nadal można wybrać sezon).
- **Lazy vs eager loading / N+1** — domyślnie relacja jest leniwa (SELECT na każdy dostęp); `joinedload` = jeden JOIN. 21 → 1.
- **Łańcuch zapytania SQLAlchemy**: metody budujące (`.filter`, `.options`, `.order_by`) zwracają Query; `.all()`/`.first()` **wykonują** i zwracają dane — więc `.all()` jest zawsze ostatnie (`.all().options(...)` → `AttributeError: 'list' ...`).
- **pytest + TestClient**: funkcje `test_*`, gołe `assert`, `TestClient(app)` woła API bez serwera; `tests/__init__.py` sprawia, że pytest dokłada katalog projektu do `sys.path` (działa `from app.main import app`).
- **Po co testy naprawdę**: łapią *ciche* błędy (zły wynik bez crasha, np. brak filtra sezonu), sprawdzają wszystkie ścieżki za każdym razem, a wartość rośnie z projektem (regresje przy zmianach).
- **Środowisko**: Python/Ruff/git **tylko w WSL**; PowerShell nie zna `&&` ani ścieżek linuksowych — z Windowsa opakowujemy w `wsl.exe -d ubuntu -e sh -c "..."`.
- **`pip freeze > requirements.txt`** po każdej instalacji paczki.

## TODO na Sesję 6 (Puchary i drabinki)
1. Model `Fixture` (mecz: drużyny gospodarz/gość, wynik, data, runda, status) + migracja Alembic nr 3. Uwaga: DWA klucze obce do `teams` (home/away) → `foreign_keys=`.
2. Import meczów pucharowych (puchary krajowe + Liga Mistrzów) — nowy krok ETL na `fixtures`.
3. Endpoint `GET /cups/{id}/bracket` — dane pogrupowane rundami (transformacja pod UI drabinki).
4. **`app/routers/`** — podział `main.py` na moduły (`APIRouter`), gdy przybędzie endpointów.
5. Dopisać testy do nowych endpointów; rozważyć osobną **bazę testową** (override `get_db`).
6. Rytm: jeden krok naraz, Ty piszesz / ja review.

## Stan repo po sesji
- Gałąź `main`. Zmienione: `app/schemas.py` (Team/StandingResponse), `app/main.py` (`/leagues` rename, `get_league_standings` + joinedload, import joinedload). Nowe: `tests/__init__.py`, `tests/test_main.py`. Zaktualizowane: `requirements.txt` (pytest) + dokumenty w `instructions/`.
- Baza bez zmian (migracji nie przybyło): `leagues` 13, `teams` 114, `standings` 114 (sezon 2024).
- Ruff czysty (`app/` + `tests/`); `pytest` 4/4 zielone.
- **Commit + push robi właściciel** (message: „Add league/standings read endpoints and first pytest tests").

## Praca domowa
### 🔴 Priorytet 1 — przed Sesją 6 (modelowanie meczów + drabinki)
1. **SQLAlchemy — Relationship patterns** · https://docs.sqlalchemy.org/en/20/orm/relationship_patterns.html — one-to-many i self-referential. `Fixture` będzie miał DWA klucze obce do `teams` (gospodarz i gość) — zwróć uwagę na `foreign_keys=` przy dwóch FK do tej samej tabeli.
2. **API-Football — Fixtures** · https://www.api-football.com/documentation-v3#tag/Fixtures — kształt payloadu meczu (teams home/away, goals, fixture.status, round). Na co patrzeć: `round` (nazwa rundy) i `status.short` (FT/NS…).
3. **FastAPI — Path Parameters** · https://fastapi.tiangolo.com/tutorial/path-params/ — utrwalenie po naszym `/{league_id}` (pod `GET /cups/{id}/bracket`).

### 🟠 Priorytet 2 — testy głębiej
4. **FastAPI — Testing dependencies (override)** · https://fastapi.tiangolo.com/advanced/testing-dependencies/ — `app.dependency_overrides` do podmiany `get_db` na bazę testową (nasz przyszły refaktor testów).
5. **pytest — Fixtures** · https://docs.pytest.org/en/stable/how-to/fixtures.html — `@pytest.fixture` do przygotowania klienta/bazy testowej (mniej powtórzeń w testach).

### 🟢 Priorytet 3 — bez terminu
6. **SQLAlchemy — Loader strategies** · https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#relationship-loading-techniques — `joinedload` vs `selectinload`; kiedy który (utrwalenie N+1).

**Metoda:** czytaj z otwartym `app/main.py` i `app/models.py` obok.
