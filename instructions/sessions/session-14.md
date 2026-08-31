# Sesja 14 — 31 sierpnia 2026

> **Selektor sezonu dla drabinek** (analogicznie do tabel z S13) + **uruchomienie
> premium API-Football (Pro)** i doimport żywych sezonów. Backend: przeróbka
> `/leagues/{id}/seasons` na `UNION` (jeden endpoint dla lig i pucharów). Frontend:
> cała ścieżka sezonu w drabince (`getBracket` → `Bracket` → `BracketPage`).
> Dane: weryfikacja planu Pro + doimport standings i fixtures dla **2025 i 2026**
> (żywy sezon wszedł do bazy — brama do Fazy 2).

## Decyzje na starcie (i dlaczego)
- **Premium kupione — plan Pro.** Praca domowa z S13 odrobiona; ryzyko #1 domknięte
  w praktyce (nie tylko decyzją, ale i zweryfikowanym dostępem).
- **Zaczynamy od selektora drabinek**, a nie od razu od Fazy 2 — dokończyć „Wizję UX:
  selektor roku" rozpoczętą w S13 dla tabel. Faza 2 (duży, świeży temat) → Sesja 15.
- **Architektura listy sezonów drabinki — opcja B (`UNION` w istniejącym `/seasons`)**
  zamiast osobnego endpointu (opcja A). Wybór właściciela: nie duplikować kodu (DRY).
  Bonus: front zostaje z JEDNYM `getSeasons` — `BracketPage` używa tego samego co
  `LeaguePage`.

## Co zostało zrobione

### Krok 1 — backend `/leagues/{id}/seasons` na `UNION` (napisał właściciel)
- **Problem**: stary endpoint czytał sezony ze `standings`, ale **puchary nie mają
  wierszy w `standings`** (puchar nie ma tabeli ligowej — tylko mecze w `fixtures`).
  Więc dla każdej drabinki zwracał `[]` → selektor byłby pusty.
- **Rozwiązanie**: dwa pod-zapytania (`Standing.season` i `Fixture.season`, filtr po
  `league_id`) złączone `.union()`, dopiero potem `.all()`; wyłuskanie krotek pętlą
  (`row[0]`) i `seasons.sort(reverse=True)` (najnowszy pierwszy).
- **Bugi wychwycone w review**:
  - `.all()` **na pod-zapytaniach** — materializuje `Query` w `list`, a `list` nie ma
    `.union()` → `AttributeError`. Lekcja: `Query` (leniwe, komponowalne) vs `.all()`
    (wykonanie, koniec łańcucha). Usunięte — `.union()` woła się na `Query`, `.all()` raz.
  - zbędne `.distinct()` i `.order_by()` na pod-zapytaniach (`UNION` sam dedupuje;
    `ORDER BY` wewnątrz operandu `UNION` jest niestandardowy) → sort w Pythonie.
  - `seasons.sort()` (rosnąco) → `sort(reverse=True)` (zgodnie z „newest-first").
- **Weryfikacja (curl)**: FA Cup (45) `[2024]`, Champions League (2) `[2024]`,
  Premier League (39) `[2024,2023,2022]`. Puchary, które wcześniej dałyby `[]`, mają
  swój sezon z `fixtures`. Ruff czysty.

### Krok 2 — frontend `getBracket(leagueId, season)` (`api/bracket.ts`)
- `season: number` dodany jako **drugi** argument, **przed** opcjonalnym `knockoutOnly`
  (reguła TS: parametr wymagany nie może stać po parametrze z wartością domyślną).
  Spójne z `getStandings(leagueId, season)`.
- URL: doklejone `&season=${season}` do query stringa.

### Krok 3 — frontend `Bracket` (`components/Bracket.tsx`)
- Prop `season: number`; `queryKey: ["bracket", leagueId, season]` (**sezon w kluczu**
  = osobny cache per sezon); `queryFn: () => getBracket(leagueId, season)`. Wzorzec 1:1
  z `LeagueTable` z S13. To ugasiło błąd TS z Kroku 2 (łańcuch zależności).

### Krok 4 — frontend selektor na `BracketPage` (`pages/BracketPage.tsx`)
- `useState` wybranego sezonu (UI state) + `useQuery(getSeasons)` (server state,
  **ten sam `getSeasons` co `LeaguePage`** — premia opcji B) + kontrolowany `<select>`;
  guard `if (!id)` **pod** hookami; `<Bracket leagueId={id} season={season} />`.
- **Bug review**: `useState(2026)` (intencja: „bieżący sezon") → `2024`. W chwili pisania
  fixtures dla 2026 jeszcze nie było w bazie → pusta drabinka + rozjazd kontrolowanego
  `<select>` (value spoza listy opcji). Zapisany **dług UX**: domyślny sezon powinien być
  „najnowszy z pobranej listy" (`seasons[0]`), nie hardkodowany rok — dotyczy też
  `LeaguePage`.

### Krok 5 — dane: premium + doimport (zgoda właściciela)
- **`/status`** (skrypt diagnostyczny, bez PII): plan **Pro**, `active`, `end`
  2026-10-01, **limit 7500 zapytań/dobę** (Free miał 100).
- **Dostęp do sezonów** (skrypt diagnostyczny, read-only): 2025 **i** 2026 dostępne dla
  standings **i** fixtures (Free dawał tylko 2022–2024). Sezon 2026 „żywy" — mniej meczów
  (dopiero się rozkręca).
- **Import** przez istniejące endpointy (zero nowego kodu — sparametryzowane po `season`):
  - `POST /import-standings?season=2025` i `2026`: 2× **114** wierszy tabel.
  - `POST /import-fixtures?season=2025`: **2430** meczów (+348 drużyn);
    `?season=2026`: **1052** meczów (+93 drużyny). Same czyste inserty (`_updated: 0`).
  - Copa del Rey / Coupe de France 2026 = **0 meczów** (puchary jeszcze nie ruszyły) —
    ETL to toleruje (pusty response → `[]`).
- **Weryfikacja `/seasons` po imporcie**: FA Cup `[2026,2025,2024]`, CL `[2026,2025,2024]`,
  **Copa del Rey `[2025,2024]`** (bez 2026 — dowód, że endpoint mówi prawdę o bazie),
  PL `[2026,2025,2024,2023,2022]`.
- **Build** (`npm run build`, tsc + vite) zielony; właściciel zweryfikował selektor na
  żywo w przeglądarce.

## Czego się nauczyliśmy (do utrwalenia)
- **`UNION` (SQL)**: skleja wyniki dwóch zapytań i usuwa duplikaty; obie strony muszą
  zwracać tę samą liczbę kolumn tego samego typu. Jeden endpoint obsłużył oba światy
  (ligi ze `standings`, puchary z `fixtures`).
- **`Query` vs `.all()`**: `db.query(...).filter(...)` to leniwy, komponowalny `Query`
  (można `.union()`, `.filter()`…); `.all()` **wykonuje** go i zwraca `list` — koniec
  łańcucha. `.all()` za wcześnie psuje `.union()`.
- **Anatomia URL**: `schemat://host:port` + **ścieżka** (segmenty przez `/` = hierarchia
  zasobu) + `?` + **query string** (pary `klucz=wartość`, pierwsza po `?`, każda kolejna
  po `&`). `/` buduje adres zasobu, `&` dokłada opcje.
- **Dwa różne „porządki"**: kolejność argumentów **funkcji** jest pozycyjna (liczy się
  miejsce → reguła „wymagany przed opcjonalnym"); kolejność **query paramów w URL** jest
  nazwana (dowolna — backend czyta po nazwie). Wymagalność argumentu nie ma wpływu na URL.
- **Kontrolowany `<select>`**: gdy `value` wskazuje sezon spoza listy `<option>`, React
  i DOM się rozjeżdżają, a komponent dostaje sezon bez danych → pusty widok. Domyślna
  wartość musi istnieć w danych.
- **Node w WSL**: `bash -ic` (interactive) ładuje `.bashrc` → nvm → **Node v20** (npm/tsc
  działają); `bash -lc` (login) daje systemowy **Node v12** → `tsc`/Vite wywalają się na
  `??`/`?.`. Do npm zawsze `bash -ic`.
- **Endpoint jako „prawda z bazy"**: `/seasons` dla Copa del Rey nie pokazuje 2026, bo
  puchar nie ruszył — lista sezonów odzwierciedla realny stan, nie sztywną tablicę.

## Stan repo po sesji
- **Backend**: `GET /leagues/{id}/seasons` przerobiony na `UNION` (`competitions.py`).
  Baza po imporcie: **leagues 15, teams 1959, standings 572, fixtures 5893**. Ruff czysty;
  pytest **7/7** (dług: wciąż brak testu `seasons`, tym ważniejszego po zmianie na `UNION`).
- **Frontend**: `api/bracket.ts` (`getBracket` + `season`), `components/Bracket.tsx`
  (prop + `season` w `queryKey`), `pages/BracketPage.tsx` (selektor sezonu). Build zielony.
  Struktura plików bez zmian (edycje istniejących plików).
- **API-Football**: plan **Pro** (7500/dobę, do 2026-10-01). Zużycie: ~30 zapytań
  (import 2 sezonów × 2 typy) + kilka diagnostycznych.

## TODO na Sesję 15
1. **Dług**: test pytest dla `GET /leagues/{id}/seasons` — pokryć **oba** źródła `UNION`
   (liga ze `standings`, puchar z `fixtures`, dedup wspólnego sezonu).
2. **Start właściwej Fazy 2 (backend)** — mamy żywe dane 2026 i premium:
   - import **fixtures ligowych** (przeszłe + przyszłe kolejki 6 lig, sezon 2026) — nowa
     grupa w `import-fixtures` (obecnie leci tylko po pucharach) lub nowy import,
   - `GET /teams/{id}/results?last=5`, `GET /teams/{id}/fixtures?next=5` (filtr po dacie
     `< now` / `> now`, `order_by`, `limit`),
   - `GET /teams?search=...` (wyszukiwarka drużyn).
3. **Dług UX**: domyślny sezon = najnowszy z listy (`seasons[0]`) zamiast hardkodu `2024` —
   wspólne dla `LeaguePage` i `BracketPage`.
4. (odłożone) tabela fazy ligowej LM/LE/Konf; upiększacze drabinki (linie łączące,
   rozszerzenie `KNOCKOUT_ROUNDS` o rundy pucharów krajowych).

## Praca domowa
> Metoda: czytaj z otwartym repo. Sesja 15 to **Faza 2 — wyniki i terminarz drużyn**:
> filtrowanie meczów po drużynie i dacie oraz wyszukiwarka. Materiały pod te endpointy.

### 🔴 Priorytet 1 — pod Fazę 2 (backend)
1. **API-Football — Fixtures (parametry `team`, `last`, `next`, `season`, `from`/`to`)** ·
   https://www.api-football.com/documentation-v3#tag/Fixtures
   — jak pobrać mecze **jednej drużyny** i jak działa `last`/`next` (ostatnie/następne N).
   Zwróć uwagę na `status` meczu (rozegrany vs zaplanowany) i pole daty.
2. **SQLAlchemy — filtrowanie, sortowanie, limit** ·
   https://docs.sqlalchemy.org/en/20/orm/queryguide/select.html
   — pod `results?last=5` / `fixtures?next=5`: `filter` po dacie (`< datetime.now()` /
   `>`), `order_by(...desc())`, `limit(5)`. To rozszerzenie tego, co już znasz z `/seasons`.

### 🟢 Priorytet 2 — pod wyszukiwarkę i wydajność
3. **React — kontrolowany input + debounce** ·
   https://react.dev/reference/react-dom/components/input
   — pod `GET /teams?search=`: kontrolowany `<input>` (jak `<select>` w S13/S14) oraz
   pojęcie **debounce** (nie wysyłaj zapytania po każdym znaku — poczekaj chwilę po
   ostatnim). Na razie tylko koncept.
4. **Indeksy w bazie (krótko)** ·
   https://use-the-index-luke.com/sql/anatomy
   — dlaczego filtrowanie `fixtures` po `team_id`/`date` skorzysta na indeksie i kiedy go
   dodać. Pierwsze zetknięcie — bez wchodzenia w szczegóły.
