# Sesja 15 — 1 września 2026

> **Start właściwej Fazy 2 (backend) na żywych danych 2026.** Domknięcie długu
> testowego z S14 (`/seasons`), import meczów **ligowych** (rozszerzenie
> `import-fixtures` o ligi), oraz trzy nowe endpointy o drużynach w osobnym
> routerze `teams.py`: ostatnie wyniki, najbliższe mecze i wyszukiwarka.
> Wszystko zweryfikowane na żywych danych (Manchester City, wyszukiwarka „real").

## Decyzje na starcie (i dlaczego)
- **Kolejność**: rozgrzewka testem `/seasons` (domknięcie długu z S14) → dopiero
  potem Faza 2 — zgodnie z naszym rytmem „mały krok najpierw".
- **Import lig — opcja A (rozszerzyć `/import-fixtures`)** zamiast osobnego endpointu.
  Powód: helpery `fetch_fixtures`/`upsert_fixtures` są **generyczne** (działają dla
  ligi i pucharu), więc osobny endpoint = duplikacja. Spójne z duchem `UNION` z S14.
- **„Rozegrany" przez `status`** (nie przez datę): `status in {FT, AET, PEN}` — mecz
  z ważnym wynikiem. Data `< now` błędnie łapałaby odwołane/przełożone/trwające.
- **Nazwy endpointów o drużynach — zestaw B**: `past-matches` / `future-matches`
  (symetria past/future). Odrzucone: `results`/`fixtures` (kolizja: `get_league_fixtures`
  zwraca WSZYSTKIE mecze, a `get_team_fixtures` znaczyłby „tylko przyszłe"). „games"→
  „matches" dla spójności słownika (model to `Fixture`). URL: `/past-matches` +
  `/future-matches` (rzeczownik na końcu — reguła REST).

## Co zostało zrobione

### Krok A — test pytest dla `GET /leagues/{id}/seasons` (dług z S14)
- `test_get_seasons_merges_standings_and_fixtures` (`tests/test_main.py`, napisał właściciel).
- **Scenariusz szczelny**: liga `id=1` z sezonami `2023` (tylko `standings`), `2025`
  (tylko `fixtures`), `2024` (w OBU → dedup). Każdy sezon broni innej części logiki
  `UNION` — usunięcie dowolnego pod-zapytania wywala test.
- **Bug review**: `assert sorted(data) == [2025, 2024, 2023]` — `sorted()` (rosnąco)
  vs lista malejąca → test by padł, a przy okazji **zamazywał sortowanie** endpointu.
  Poprawka: `assert data == [2025, 2024, 2023]` — bezpośrednie porównanie sprawdza
  zawartość + dedup + kolejność malejącą naraz (endpoint gwarantuje kolejność).
- **pytest 7/7 → 8/8**. Dług testowy z S14 domknięty. Przy okazji Ruff wyłapał
  zaległe formatowanie `competitions.py` (trailing space z S14) — posprzątane.

### Krok B1 — import meczów ligowych (rozszerzenie `import-fixtures`)
- **Odkrycie**: `fetch_fixtures`/`upsert_fixtures` są generyczne — brakowało tylko
  lig w pętli. Zmiana: `competitions = TARGET_LEAGUE_IDS` (już zawiera ligi + puchary
  + europejskie = 15 rozgrywek; napisał właściciel).
- **Rename** `cups_report` → `competitions_report` (4 miejsca) + komentarz/docstring
  — nazwy przestały kłamać („to już nie tylko puchary").
- **F401 po refaktorze**: `TARGET_LEAGUE_IDS` osierocił importy `DOMESTIC_CUP_IDS`
  i `EUROPEAN_COMPETITION_IDS` — Ruff je wyłapał, usunięte (`DOMESTIC_LEAGUE_IDS`
  ZOSTAŁ, bo używa go `import_standings`).
- **Import 2026 (na żywo, zgoda właściciela)**: `POST /import-fixtures?season=2026`.
  - Ligi = **same INSERTY** (fixtures lig wcześniej nie było): PL/La Liga/Serie A po
    **380** (20 drużyn × 38), Bundesliga/Ligue 1/Primeira po **306** (18 × 34) —
    liczby zgodne z wielkością lig. Razem **2058** ligowych.
  - Puchary + europejskie = **1052 UPDATE** (dokładnie te z importu 2026 w S14 →
    empiryczny dowód idempotencji, 0 duplikatów). Taça +29, +3 nowe drużyny.
  - `fixtures_added: 2087`, `fixtures_updated: 1052`. Baza `fixtures`: 5893 → **7980**.

### Krok B2 — `GET /teams/{id}/past-matches` (ostatnie wyniki)
- Nowa stała `FINISHED_STATUSES = {"FT", "AET", "PEN"}` w `constants.py` (wzór
  `KNOCKOUT_ROUNDS`; FT=pełny czas, AET=dogrywka, PEN=karne).
- **Nowy router `app/routers/teams.py`** (`APIRouter(tags=["teams"])`) + wpięcie
  w `main.py` (`include_router`). Endpoint `get_team_past_matches`: guard 404,
  `or_(home_id == team_id, away_id == team_id)` (**pierwszy raz LUB**),
  `status.in_(FINISHED_STATUSES)`, `order_by(date.desc())`, `limit(last)`, `joinedload`.
- **Weryfikacja na żywo** (Man City, `?last=5`): 5 meczów, malejąco, same `FT`,
  City raz u siebie, raz na wyjeździe — `or_` działa. Endpoint łączy sezony i
  rozgrywki (PL + puchary) = **„forma" cross-competition** (świadoma decyzja).

### Krok B3 — `GET /teams/{id}/future-matches` (najbliższe mecze)
- Bliźniak `past` z trzema różnicami: `status == "NS"` (Not Started),
  `order_by(date.asc())` (najbliższy pierwszy), parametr `next: int = 5`.
- **Weryfikacja** (Man City, `?next=5`): 5 meczów `NS`, rosnąco, gole `null`.
  `past` kończy się 28 sie, `future` zaczyna 5 wrz — **dzisiejsza data (1 wrz)
  idealnie rozdziela** przeszłość od przyszłości. Wśród PL siedzi mecz Ligi
  Mistrzów (Porto) — terminarz też cross-competition.

### Krok B4 — `GET /teams?search=...` (wyszukiwarka)
- `search_teams`: `Team.name.ilike(f"%{search}%")`, `order_by(Team.name)`,
  `limit(20)`, reużyty `TeamResponse`. Bez guardu (pusta lista = poprawna).
- **Weryfikacja**: `?search=real` → Real Madrid/Betis/Sociedad, ale też
  Vil**larreal**, Mont**real**, Vila Real (wzorzec „zawiera" w dowolnym miejscu).
  `?search=MANCHESTER` (wielkie) → Manchester City/United (case-insensitive `ilike`).

## Czego się nauczyliśmy (do utrwalenia)
- **Szczelność testu**: dobierz dane tak, by usunięcie *dowolnego* fragmentu logiki
  wywaliło test (sezon tylko-standings + sezon tylko-fixtures + wspólny na dedup).
- **`data == [...]` vs `sorted(data) == [...]`**: gdy endpoint *gwarantuje* kolejność,
  testuj ją wprost — `sorted()` ją zamazuje.
- **`ruff check` (lint) ≠ `ruff format` (styl)** — dwa różne narzędzia. `format` NIE
  łapie: martwych importów (**F401** to `check`) ani długich **komentarzy** (nie umie
  ich dzielić). Projekt nie ma reguł `I` (sort importów), `E501` (długość), `A`
  (shadowing builtinów) — więc te pilnujemy sami.
- **Generyczność ETL**: `fetch_fixtures`/`upsert_fixtures` obsługują ligę i puchar tak
  samo (API-Football nie rozróżnia). `TARGET_LEAGUE_IDS` = „wszystko, co śledzimy".
- **Ligi i puchary w JEDNEJ tabeli `leagues`** (różne `league_id`). Standings ma tylko
  liga; fixtures ma puchar **oraz** (od teraz) liga → stąd `UNION` w `/seasons`.
- **`APIRouter`**: grupa tras w osobnym pliku; `include_router` scala je z `app`
  (bez wpięcia = 404, choć plik poprawny); `tags` = sekcja w Swaggerze.
- **Parametr endpointu FastAPI**: path (w ścieżce) vs query (zwykły typ → `?x=`) vs
  dependency (`Depends`). `= wartość` → query param **opcjonalny**; bez → wymagany.
- **SQLAlchemy**: `or_` (LUB; przecinek w `.filter` to AND) — import z `sqlalchemy`,
  nie `.orm`; `.in_(zbiór)`; `.desc()`/`.asc()`; `.limit(n)`; `ilike` + `%` (wildcard,
  case-insensitive). `f"%{s}%"` w `ilike` jest **bezpieczne** — bind parameter, nie
  sklejanie surowego SQL (brak injection).
- **Status meczu**: `{FT, AET, PEN}` = rozegrany; `NS` = zaplanowany. Semantyczny filtr
  bije filtr po dacie. „Ostatnie/najbliższe mecze" liczymy **cross-competition** (forma).
- **Naming/URL**: nazwa funkcji ≠ ścieżka URL (dwie warstwy); URL kończy się
  **rzeczownikiem** (zasobem), nie przymiotnikiem; spójność słownika w kodzie
  (`matches`, nie nowe `games`). `next` przesłania builtina — tu nieszkodliwe.
- **`No newline at end of file`** — pliki tekstowe kończymy `\n` (konwencja POSIX;
  Ruff dokłada).

## Stan repo po sesji
- **Backend Fazy 2 — KOMPLETNY (część serwerowa)**: import ligowy + 3 endpointy
  o drużynach.
  - `app/routers/teams.py` — **NOWY** router (`past-matches`, `future-matches`, `teams?search=`).
  - `app/main.py` — wpięty `teams.router`.
  - `app/constants.py` — `FINISHED_STATUSES`.
  - `app/routers/imports.py` — `import-fixtures` obejmuje ligi (`TARGET_LEAGUE_IDS`).
  - `app/routers/competitions.py` — doczyszczone formatowanie (zaległość S14).
  - `tests/test_main.py` — +1 test (`seasons`), **8/8**.
- **Baza**: `leagues 15, teams 1962 (+3), standings 572, fixtures 7980 (+2087)`.
- **Jakość**: Ruff (format + lint) czysty, pytest **8/8**. API-Football (Pro): ~15
  zapytań importu + kilka odczytowych (weryfikacja endpointów lokalna).

## TODO na Sesję 16
1. **Dług testowy (rozgrzewka)**: pytest dla `past-matches`, `future-matches`,
   `search_teams` (3 endpointy bez testów). Wzorce: `or_`/status/sort/limit,
   `ilike` (case-insensitive), pusty wynik, 404 dla nieznanej drużyny.
2. **Frontend Fazy 2 — wybór ulubionych** (ROADMAP Blok 3):
   - warstwa API `frontend/src/api/teams.ts` (`getPastMatches`, `getFutureMatches`,
     `searchTeams` + typy — wzór `standings.ts`/`bracket.ts`),
   - **wyszukiwarka**: kontrolowany `<input>` + **debounce** (nie fetch po każdym
     znaku) + `useQuery` (`enabled` gdy fraza niepusta),
   - **ulubione**: dodawanie/usuwanie + zapis w `localStorage` (custom hook
     `useFavorites`) — bez logowania (świadome MVP).
3. **Dług UX**: domyślny sezon = najnowszy z listy (`seasons[0]`) zamiast hardkodu
   `2024` — wspólne dla `LeaguePage` i `BracketPage`.
4. (odłożone) tabela fazy ligowej LM/LE/Konf; upiększacze drabinki.

## Praca domowa
> Metoda: czytaj z otwartym repo. Sesja 16 to **frontend Fazy 2** (wyszukiwarka +
> ulubione) i testy nowych endpointów. Materiały pod te tematy.

### 🔴 Priorytet 1 — pod wyszukiwarkę i ulubione (frontend)
1. **React — `localStorage` + custom hook** ·
   https://react.dev/learn/reusing-logic-with-custom-hooks
   — jak wyciągnąć logikę „ulubionych" do `useFavorites` (własny hook = funkcja
   `useXxx` używająca innych hooków). Zwróć uwagę: hook zwraca stan + funkcje
   (`favorites`, `add`, `remove`), a `localStorage` czytamy/zapisujemy w `useEffect`.
2. **Debounce w praktyce** ·
   https://react.dev/reference/react/useEffect#fetching-data-with-effects
   — dlaczego przy wyszukiwarce NIE wysyłamy zapytania po każdym znaku: `useEffect`
   z `setTimeout` + funkcja czyszcząca (cleanup) anulująca poprzedni timer. Na razie
   koncept — implementację poprowadzę.

### 🟢 Priorytet 2 — pod testy nowych endpointów
3. **pytest — powtórka naszego wzorca** · przejrzyj `tests/test_main.py`
   — jak seedujemy `Fixture` z różnym `status` (`FT` vs `NS`) i `date`, żeby
   przetestować `past`/`future`. Pomyśl: jaki scenariusz danych udowodni, że
   `past` bierze tylko `FT`, a `future` tylko `NS` (analogia do „szczelności"
   z testu `/seasons`).
4. **TanStack Query — `enabled` i `placeholderData`** ·
   https://tanstack.com/query/latest/docs/framework/react/guides/dependent-queries
   — jak nie odpalać zapytania, gdy fraza pusta (`enabled: search.length > 0`)
   i jak nie „mrugać" wynikami przy kolejnych literach. Pierwsze zetknięcie.
