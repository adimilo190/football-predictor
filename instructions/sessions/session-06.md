# Sesja 6 — 5 sierpnia 2026

## Co zostało zrobione

### 1. Model `Fixture` + migracja Alembic nr 3
- Nowy model `Fixture` (`app/models.py`): mecz z **dwoma kluczami obcymi do `teams`** (`home_team_id`, `away_team_id`) + `league_id`, `season`, `round`, `date` (`DateTime`), `status`, `home_goals`/`away_goals` (nullable — mecz może być nierozegrany). `id` **reużyty z API-Football** (nie auto-increment).
- **Kluczowa lekcja:** dwa FK do tej samej tabeli → SQLAlchemy nie wie, przez który iść, więc relacje wymagają `foreign_keys=[...]`: `home_team = relationship("Team", foreign_keys=[home_team_id])` i analogicznie `away_team`. Relacje **jednokierunkowe** (bez `back_populates`) — `Team` nietknięty, bo w tej fazie potrzebujemy tylko kierunku mecz → drużyna.
- Migracja Alembic nr 3 (`03d5cc4db1d2_create_fixtures_table.py`) przez `--autogenerate`, przejrzana i zastosowana (`upgrade head`). Tabela `fixtures` fizycznie w bazie.

### 2. Pełny ETL importu meczów pucharowych
- `fetch_fixtures(client, league_id, season)` — Extract (bliźniak `fetch_league_standings`). URL `/fixtures`, **płaski payload** (`response` = od razu lista meczów, bez „list list" jak w standings).
- `upsert_team(db, team_info) -> bool` — helper (DRY): upsert jednej drużyny. Nowej drużynie daje `country=None` (payload meczu nie ma kraju), istniejącej **nie nadpisuje** kraju. Zwraca `True` przy insercie.
- `upsert_fixtures(db, league_id, season, fixtures)` — Transform+Load: guard (rozgrywka istnieje?), **dedup drużyn** (`seen_team_ids` set), parsowanie daty ISO (`datetime.fromisoformat`), upsert meczu **po `id`**.
- `POST /import-fixtures` — pętla po 7 pucharach (`DOMESTIC_CUP_IDS` + `EUROPEAN_COMPETITION_IDS`), jeden commit (all-or-nothing), raport per rozgrywka.
- **Import zweryfikowany na żywo:** 1733 mecze, 1267 drużyn, 7 rozgrywek. Zużycie API: ~14/100 (dwie próby × 7 zapytań).

### 3. Endpointy odczytu + schematy
- `FixtureResponse` (`app/schemas.py`) — mecz z **dwiema zagnieżdżonymi drużynami** (`home_team`/`away_team: TeamResponse`), `round`, `date`, `status`, gole nullable.
- `TeamResponse.country` zluzowany na `str | None = None` — bo drużyny pucharowe mają `country=None`.
- `BracketRound` (`round: str`, `fixtures: list[FixtureResponse]`) — **bez `from_attributes`**, bo budowany ręcznie w kodzie (nie z obiektu ORM).
- `GET /leagues/{id}/fixtures` — płaska lista, **podwójny `joinedload`** (home + away, przeciw N+1×2), sort po dacie.
- `GET /leagues/{id}/bracket` — grupowanie meczów po rundzie do `dict` (insertion order = chronologia), zwraca `list[BracketRound]`. Zweryfikowany: 17 rund LM 2024/25 w idealnej kolejności turniejowej, finał PSG 5-0 Inter na końcu.
- Komentarze w sekcji endpointów uporządkowane: mylącą numerację `1./2./3. ENDPOINT` zastąpiono nagłówkami grup `WRITE`/`READ`; polskie komentarze przetłumaczone na angielski.

## Decyzje (i dlaczego)
- **Nazewnictwo generyczne:** `fetch_fixtures` (nie `fetch_cup_fixtures`) i parametr `league_id` (nie `cup_id`). Powód: funkcja działa dla **dowolnej** rozgrywki (API-Football nie rozróżnia ligi od pucharu), a u nas „league" = dowolna rozgrywka. „Cup" to intencja wywołania (pętla endpointu), nie natura funkcji. Bonus: `fetch_fixtures` przyda się w Fazie 2 do meczów ligowych.
- **Odporność na braki danych (decyzja właściciela):** pusty `response` z API → zwracamy `[]` (toleruj), a **prawdziwe awarie** (błąd HTTP, pole `errors` = np. wyczerpany limit) **nadal rzucają `502`**. Zastosowane w OBU fetchach (fixtures + standings). Granica: „brak danych" ≠ „awaria". Widoczność zapewnia raport per rozgrywka (0 = brak danych). To świadoma, udokumentowana zmiana względem wcześniejszego twardego `502` w standings.
- **Dedup drużyn w `upsert_fixtures`:** `SessionLocal` ma `autoflush=False`, więc świeżo dodana (pending) drużyna jest niewidoczna dla kolejnego `query().first()` do czasu commitu. W pucharze drużyna gra wiele rund → bez dedup dodalibyśmy ją wielokrotnie → `duplicate key`. Standings tego nie miał, bo tam każda drużyna jest unikalna.
- **`country=None` dla drużyn pucharowych** (payload meczu nie zawiera kraju) → `TeamResponse.country` musiał zostać `str | None`.
- **Sortowanie rund po dacie, nie po nazwie** — rundy grają się chronologicznie, więc data = pozycja w turnieju; `dict` zachowuje kolejność wstawiania. Zero ręcznego mapowania chaotycznych nazw rund.
- **`BracketRound` w `schemas.py`, nie w `models.py`** — to dane **pochodne** (grupowanie meczów, które już są w bazie), a nie źródłowe. Zasada: w bazie trzymamy fakty źródłowe; co da się wyliczyć — liczymy na żądanie (single source of truth). Schematy nie są lustrem modeli.
- **DRY przez helper, nie „endpoint woła endpoint":** przy próbie reużycia `get_league_fixtures` z bracketu — bezpośrednie wywołanie endpointu jako funkcji pomija `response_model` i `Depends`, miesza warstwy. Właściwie: wspólny helper `query_fixtures`. Właściciel na razie zostawił duplikację guard+query w obu endpointach — do sprzątnięcia w Sesji 7 (krok routerów).
- **Ścieżki spójne `/leagues/{id}/...`** (nie `/cups/...`) — bo puchar to też „league" w naszej bazie; spójnie ze `standings`.

## Czego się nauczyliśmy (do utrwalenia)
- **Dwa FK do tej samej tabeli → `foreign_keys=` na relacjach** (inaczej „ambiguous"). `configure_mappers()` w smoke teście weryfikuje spójność mapperów.
- **`Column` (realna kolumna w bazie) vs `relationship`** (skok po kluczu obcym do obiektu — nie tworzy kolumny). String w `relationship("Team")` = forward reference (rozwiązywany później z rejestru, niezależnie od kolejności klas).
- **Migracje = git dla schematu bazy:** `down_revision` (łańcuch), `upgrade()`/`downgrade()` (symetria), tabela `alembic_version` (gdzie jesteś), `upgrade head` (na czubek).
- **`async` vs `def`:** jest `await` w środku → musi być `async def`. `httpx` async → `fetch_*` async; SQLAlchemy sync → `upsert_*` zwykłe `def`.
- **ZIELONY `ruff`/smoke ≠ poprawny kod.** Realne bugi wychodzą dopiero na danych. I różne narzędzia łapią różne rzeczy: `ruff check` złapał `F821` (undefined name — smoke by przepuścił), smoke złapał `import datetime` (moduł) vs klasa (ruff przepuścił), realny import złapał `duplicate key` i `ResponseValidationError`.
- **`autoflush=False`** → pending obiekty niewidoczne dla `query` do commitu → deduplikacja w pamięci (set).
- **`import X` (moduł) vs `from X import Y` (nazwa)** — pułapka: moduł `datetime` zawiera klasę `datetime`.
- **`response_model` waliduje WYJŚCIE** — chroni kontrakt z frontendem; złapał `country=None` tam, gdzie schemat obiecywał string.
- **Grupowanie z zachowaniem kolejności:** `dict` (Python 3.7+) pamięta kolejność wstawiania → dane wejściowe posortowane po dacie dają rundy w kolejności turnieju.
- **Dane źródłowe (baza) vs pochodne (wyliczane on-the-fly).**
- **DRY:** współdzieloną logikę wydzielaj do helpera; nigdy „endpoint woła endpoint".

## TODO na Sesję 7 (porządki backendu przed frontendem)
1. **Routery (`app/routers/`):** `main.py` urósł do ~520 linii — podzielić na `APIRouter` (np. `imports.py`, `competitions.py`), z `prefix`/`tags`. Przy okazji **wydzielić helper `query_fixtures`** (guard + `joinedload` + sort) i usunąć duplikację z `get_league_fixtures` i `get_league_bracket`.
2. **Testy (pytest):** dopisać testy do `/import-fixtures` (lub jego części), `/leagues/{id}/fixtures`, `/leagues/{id}/bracket` (kolejność rund!). Rozważyć **osobną bazę testową** przez `app.dependency_overrides[get_db]` + `@pytest.fixture`.
3. **Filtrowanie rund w drabince (do przemyślenia):** bracket zwraca teraz wszystkie rundy (kwalifikacje, faza ligowa LM, knockout). Rozważyć query param albo listę „głównych rund" dla czystej drabinki knockout.
4. Dopiero potem: start frontendu (dawna Sesja 7 z ROADMAP — przesuwa się).

## Stan repo po sesji
- Gałąź `main`. Nowe/zmienione: `app/models.py` (`Fixture`), migracja `03d5cc4db1d2`, `app/main.py` (`fetch_fixtures`, `upsert_team`, `upsert_fixtures`, `import_fixtures`, `get_league_fixtures`, `get_league_bracket`, `from datetime import datetime`, import grup z `constants`, komentarze endpointów, `fetch_league_standings` pusty→`[]`), `app/schemas.py` (`FixtureResponse`, `BracketRound`, `TeamResponse.country: str | None`, `from datetime import datetime`).
- Baza: `fixtures` **1733** (7 rozgrywek, sezon 2024), `teams` **1267+** (drużyny pucharowe z `country=None`), `leagues` 13, `standings` 114. Migracja nr 3 zastosowana.
- API-Football: ~14/100 zapytań zużyte dziś (2 próby importu).
- Ruff czysty, smoke OK, endpointy `/fixtures` i `/bracket` zweryfikowane na żywo (TestClient, bez zużycia API).
- **Commit + push robi właściciel** (proponowany message w rozmowie).

## Praca domowa
### 🔴 Priorytet 1 — przed Sesją 7 (routery + testy)
1. **FastAPI — Bigger Applications / APIRouter** · https://fastapi.tiangolo.com/tutorial/bigger-applications/ — jak rozbić jeden `main.py` na moduły `routers/`. Na co patrzeć: `APIRouter()`, `prefix=`, `tags=`, `include_router()` w `main.py`.
2. **FastAPI — Testing dependencies (override)** · https://fastapi.tiangolo.com/advanced/testing-dependencies/ — `app.dependency_overrides[get_db]` do podmiany bazy na testową. To klucz do sensownych testów, które nie ruszają bazy deweloperskiej.
3. **pytest — Fixtures** · https://docs.pytest.org/en/stable/how-to/fixtures.html — `@pytest.fixture` do przygotowania klienta i bazy testowej raz, bez powtórzeń w każdym teście.

### 🟢 Priorytet 2 — bez terminu
4. **SQLAlchemy — Session basics (flush/autoflush)** · https://docs.sqlalchemy.org/en/20/orm/session_basics.html — utrwalenie, dlaczego pending obiekty bywają niewidoczne i czym jest flush (kontekst naszego buga z duplikatami).

**Metoda:** czytaj z otwartym `app/main.py` obok — zwłaszcza sekcją endpointów (kandydat na podział) i dwoma prawie-identycznymi `get_league_fixtures`/`get_league_bracket` (kandydat na helper).
