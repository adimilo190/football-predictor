# Sesja 4 — 9 lipca 2026

## Co zostało zrobione
1. **Nowa zasada współpracy w `CLAUDE.md`**: po każdej sesji Claude zadaje pracę domową (dokumentacja/materiały pod TODO następnej sesji) — dopisywana jako sekcja „Praca domowa" w logu sesji.
2. **`app/constants.py` rozdzielony na grupy**: `DOMESTIC_LEAGUE_IDS` (6 lig z tabelą), `DOMESTIC_CUP_IDS` (6 pucharów), `EUROPEAN_COMPETITION_IDS` (LM); `TARGET_LEAGUE_IDS` = scalenie grup operatorem `**` (jedno źródło prawdy). Dodana stała `DEFAULT_SEASON = 2024` (najnowszy sezon na planie free).
3. **Extract — `fetch_league_standings(client, league_id, season)`** w `app/main.py`: zapytanie `standings?league={id}&season={rok}` z `params=` i `timeout=15s`; pełna obsługa błędów: `raise_for_status()` + `except httpx.HTTPError` → `HTTPException(502)`, kontrola pola `errors` w treści (API-Football potrafi zwrócić 200 OK z błędem w środku!), kontrola pustego `response`; spłaszczenie listy grup zwykłą pętlą z `extend` (czytelność > zwięzłość — decyzja właściciela).
4. **Transform + Load — `upsert_league_standings(db, league_id, season, rows)`**: upsert drużyny (`teams`) i wpisu tabeli (`standings`) per wiersz; guard clause 404 gdy ligi nie ma w bazie; aktualizacja przez przypisania atrybutów (SQLAlchemy unit of work); funkcja celowo NIE commituje — o transakcji decyduje wywołujący; zwraca licznik `{teams_added, standings_added, standings_updated}`.
5. **Endpoint `POST /import-standings`**: pętla po 6 ligach na jednym współdzielonym `AsyncClient` (6 zapytań API), query param `season: int = DEFAULT_SEASON`, JEDEN `db.commit()` po pętli (all-or-nothing), odpowiedź z raportem per liga + sumami.
6. **Import wykonany i zweryfikowany** (TestClient): 114 drużyn / 114 wpisów standings; liczby lig zgodne z rzeczywistością (20/20/20/18/18/18); mistrzowie 2024/25 poprawni (Liverpool, Barcelona, Napoli, Bayern, PSG, Sporting CP); upsert potwierdzony w boju (PL z wcześniejszego testu: 0 added / 20 updated).
7. **Idempotencja upsertu przetestowana bez kosztu API**: dwa przebiegi na tych samych danych w pamięci → drugi przebieg 0 insertów, 20 update'ów, zero duplikatów.
8. Ruff format + check czyste. Zużycie limitu API: 8/100 zapytań (2 testy + 6 importu).

## Decyzje (i dlaczego)
- **Upsert aplikacyjny (ORM: sprawdź → INSERT/UPDATE) zamiast SQL `INSERT ... ON CONFLICT`** — czytelniejszy i wystarczający przy 6×20 wierszach; `ON CONFLICT` ma sens przy dużej skali/współbieżności. `UniqueConstraint uq_standing` zostaje w bazie jako siatka bezpieczeństwa.
- **Helpery nie commitują; commit raz, w endpoincie** — import 6 lig to jedna transakcja: błąd w połowie = baza nietknięta (nigdy „w rozkroku").
- **`team.country` z ligi** — payload standings nie zawiera kraju drużyny; drużyny ligi krajowej dziedziczą kraj ligi.
- **Sezon jako query param z domyślną `DEFAULT_SEASON`** — elastyczność (można zaimportować 2022/2023) bez komplikowania podstawowego użycia.
- **Odświeżanie danych = świadoma ręczna akcja** (strategia limitów): dane trzymamy u siebie, `POST /import-standings` kosztuje 6 zapytań, więc wywołujemy go celowo, nie automatycznie.
- **Styl kodu (feedback właściciela): proste pętle zamiast zagnieżdżonych comprehension** — czytelność dla uczącego się > zwięzłość. Zapisane w pamięci Claude.

## Czego się nauczyliśmy (do utrwalenia!)
- **ETL**: Extract (pobierz surowe) → Transform (przemapuj) → Load (zapisz) — rozdzielone etapy = łatwiejsze testowanie i debugowanie.
- **Obsługa błędów HTTP klienta**: `raise_for_status()` (statusy 4xx/5xx → wyjątek), `httpx.HTTPError` (klasa-matka błędów statusu I transportu: timeout, DNS), `timeout=` (nie wisimy w nieskończoność), pułapka „200 OK z błędem w treści".
- **`HTTPException(502 Bad Gateway)`** = „zawiodło nasze zewnętrzne źródło, nie my"; 404 z podpowiedzią („run /import-leagues first") zamiast tajemniczego wybuchu FK.
- **Upsert** = UPDATE jeśli istnieje, INSERT jeśli nie; idempotencja = wielokrotne uruchomienie bez duplikatów.
- **SQLAlchemy unit of work**: przypisanie `standing.points = 84` wystarcza — ORM śledzi zmiany i generuje UPDATE przy commicie.
- **Granice transakcji**: kto commituje, ten decyduje o atomiczności; commit po pętli = all-or-nothing.
- **FastAPI query params**: parametr funkcji z wartością domyślną = parametr `?season=...` z walidacją typu za darmo (422 przy błędnym typie).
- **`**` (dict unpacking)**: scalanie słowników bez duplikowania danych; `list.extend` vs `append` (dokleja elementy vs całą listę jako jeden element).
- **PYTHONPATH**: Python szuka pakietów od katalogu skryptu, nie od cwd — skrypt spoza projektu potrzebuje `PYTHONPATH=/ścieżka/do/projektu`.

## TODO na start Sesji 5 (Publiczne endpointy + pierwsze testy)
1. Schematy Pydantic dla `Team`/`Standing` (przeniesione z opcjonalnego punktu S4 — potrzebne do `response_model`).
2. `GET /leagues` i `GET /leagues/{id}/standings` — czyste dane dla przyszłego frontendu (path param, sortowanie po `rank`).
3. **pytest**: folder `tests/`, konfiguracja, 3–4 pierwsze testy z `TestClient` (root, `/my-leagues`, standings, błędne id).
4. Rozważyć `app/routers/` — endpointów przybywa (decyzja: czy już czas).
5. Rytm pracy: jeden krok naraz + pytanie o zgodę.

## Stan repo po sesji
- Gałąź `main`. Zmienione: `CLAUDE.md` (zasada pracy domowej), `app/constants.py` (grupy rozgrywek + `DEFAULT_SEASON`), `app/main.py` (fetch_league_standings, upsert_league_standings, `POST /import-standings`, import `HTTPException`).
- Baza: `leagues` 13, `teams` 114, `standings` 114 (sezon 2024) — pełne tabele 6 lig.
- Ruff czysty; smoke test tras OK; import zweryfikowany end-to-end (mistrzowie zgodni z rzeczywistością).
- Migracji NIE przybyło (schemat bez zmian — tylko dane).

## Praca domowa
**DUŻA praca domowa (na życzenie właściciela):** nie tylko pod Sesję 5, ale komplet wiedzy obowiązkowej do tego momentu projektu.

### 🔴 Priorytet 1 — przed Sesją 5 (~1,5 h)
1. **pytest — Get Started** · https://docs.pytest.org/en/stable/getting-started.html — konwencja `test_*`, goły `assert`, uruchamianie i czytanie wyników.
2. **FastAPI — Testing** · https://fastapi.tiangolo.com/tutorial/testing/ — `TestClient`, sprawdzanie `status_code` i `json()`; test nie potrzebuje działającego serwera.
3. **FastAPI — Dependencies** · https://fastapi.tiangolo.com/tutorial/dependencies/ — nasz `get_db` + `Depends`; w testach będziemy podmieniać zależności (baza testowa). Zwrócić uwagę na zależności z `yield`.

### 🟠 Priorytet 2 — fundament (wszystko już użyte w naszym kodzie; ~4–5 h w tydzień–dwa)
4. **MDN — przegląd HTTP** · https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview
5. **MDN — metody HTTP** · https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods — czemu import = POST, odczyt = GET.
6. **MDN — kody statusu** · https://developer.mozilla.org/en-US/docs/Web/HTTP/Status — rodziny 2xx/4xx/5xx; nasze 404, 422, 502.
7. **FastAPI — First Steps + Query Parameters** · https://fastapi.tiangolo.com/tutorial/first-steps/ + https://fastapi.tiangolo.com/tutorial/query-params/ — nasz `season: int = DEFAULT_SEASON`.
8. **FastAPI — Response Model** · https://fastapi.tiangolo.com/tutorial/response-model/ — nasz `response_model=list[LeagueResponse]`.
9. **FastAPI — Handling Errors** · https://fastapi.tiangolo.com/tutorial/handling-errors/ — `HTTPException`.
10. **FastAPI — Async („In a hurry?")** · https://fastapi.tiangolo.com/async/ — najprzystępniejsze wyjaśnienie `async/await`; techniczne detale można pominąć.
11. **SQLAlchemy — Session Basics** · https://docs.sqlalchemy.org/en/20/orm/session_basics.html — „Basics of Using a Session" + „Adding New or Existing Items"; unit of work, co robi `commit()`.
12. **FastAPI — SQL Databases** · https://fastapi.tiangolo.com/tutorial/sql-databases/ — nasz układ models/schemas/database opisany oficjalnie.
13. **Alembic — Tutorial** · https://alembic.sqlalchemy.org/en/latest/tutorial.html — do „Downgrading" włącznie; revision → upgrade head, łańcuch `down_revision`.
14. **Python — Errors and Exceptions** · https://docs.python.org/3/tutorial/errors.html — try/except/raise.
15. **Python — Data Structures** · https://docs.python.org/3/tutorial/datastructures.html — listy (`append` vs `extend`), słowniki (`.get()`, `.items()`), comprehensions.
16. **pydantic-settings** · https://docs.pydantic.dev/latest/concepts/pydantic_settings/ — początek: mapowanie pól na `.env` (nasz `config.py`).
17. **httpx — Quickstart** · https://www.python-httpx.org/quickstart/ — jeśli nie doczytane przed S4: statusy, `.json()`, `raise_for_status()`, timeouts.

### 🟢 Priorytet 3 — pogłębienie (bez terminu)
18. **SQLBolt (interaktywny SQL)** · https://sqlbolt.com/ — lekcje 1–12; co ORM pisze za nas.
19. **Pro Git — rozdz. 2 Git Basics** · https://git-scm.com/book/en/v2 — jest wersja polska.
20. **Alembic — ślepe punkty autogenerate** · https://alembic.sqlalchemy.org/en/latest/autogenerate.html#what-does-autogenerate-detect-and-what-does-it-not-detect — np. rename kolumny = drop+add.

**Metoda:** czytać z otwartym `app/main.py` obok — cel to „aha, to TO robiliśmy", nie wkuwanie.
