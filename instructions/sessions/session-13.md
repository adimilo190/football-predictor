# Sesja 13 — 20 sierpnia 2026

> **Daty + godziny meczów w drabince** oraz **selektor sezonu dla tabel ligowych.**
> Na starcie: decyzja o kierunku (start Fazy 2 — core projektu) i o **źródle żywych
> danych** (właściciel kupuje **API-Football premium**). Backend: nowy endpoint
> `GET /leagues/{id}/seasons` + doimport sezonów 2022/2023. Frontend: cała ścieżka
> wielosezonowa (warstwa API → `LeagueTable` → selektor w `LeaguePage`).
> (Kalendarzowo Sesja 13 realizuje „Wizję UX: selektor roku" + dopieszczenie drabinki,
> a nie „Faza 2 backend" z ROADMAP — rozjazd numeracji trwa, patrz ryzyko #4.)

## Decyzje na starcie (i dlaczego)
- **Kierunek: start Fazy 2** (predyktor/ML to core CV), z odłożeniem tabeli fazy ligowej
  i szlifów Fazy 1 na później. Ale „najpierw" (życzenie właściciela): daty w drabince
  + selektor sezonu.
- **Źródło danych Fazy 2 — API-Football premium (~19 €/mies), kupuje właściciel.**
  Faza 2 wymaga żywego sezonu (nadchodzące mecze), a Free daje tylko 2022–2024.
  Wybór premium nad darmową hybrydą: **spójne ID z naszą bazą** (zero mapowania drużyn),
  puchary krajowe, logo, bieżący sezon + historia z jednego źródła. (Ryzyko #1 domknięte.)
- **Import 2022/2023 z Free teraz** (nie czekać na premium): odblokowuje front selektora,
  tanio (~12 zapytań), a kod endpointów jest niezależny od źródła — premium tylko dołoży
  nowsze sezony później.
- **Selektor najpierw dla tabel** (standings), drabinki analogicznie w Sesji 14.

## Co zostało zrobione

### 1. Krok 1 — daty i godziny w drabince (tylko frontend)
- Backend już **wysyłał** datę (`FixtureResponse.date`), ale `groupIntoMatchups` ją gubiła.
- **`api/bracket.ts`**: pole `date: string` dodane do obiektu `legs` w typie `Matchup`
  (data to dana **per mecz**, jak gole — dwumecz ma dwie daty), i `date: leg.date`
  dopisane w `groupIntoMatchups` (bez warunku — data nie zależy od home/away).
- **`components/MatchupCard.tsx`**: helper `formatDate` (ISO → `toLocaleString("pl-PL",
  { dateStyle: "short", timeStyle: "short" })`) + wiersz dat na dole karty
  (`legs.map(...).join(" / ")`). Format `12.03.2025, 21:00`.

### 2. Krok 2 — selektor sezonu (tabele)
- **Backend — endpoint `GET /leagues/{id}/seasons`** (napisał właściciel, ze wskazówkami):
  `db.query(models.Standing.season).filter(league_id).distinct().order_by(desc()).all()`,
  wyłuskanie krotek zwykłą pętlą (`row[0]`), `response_model=list[int]`. Zwraca faktyczne
  sezony z bazy (prawda, nie lista na sztywno).
- **Dane — doimport 2022 i 2023** przez istniejący `POST /import-standings?season=`
  (zero nowego kodu — endpoint był już parametryzowany). Wynik: `seasons` zwraca
  `[2024, 2023, 2022]`. ~12 zapytań do API-Football.
- **Frontend — warstwa API (`api/standings.ts`)**: `getStandings(leagueId, season)`
  (drugi parametr **wymagany** + `?season=${season}`) i nowa `getSeasons(leagueId):
  Promise<number[]>`.
- **Frontend — `components/LeagueTable.tsx`**: prop `season`, `queryKey: ["standings",
  leagueId, season]` (**sezon w kluczu** = osobny cache per sezon → zmiana sezonu pobiera
  świeże dane), `queryFn: () => getStandings(leagueId, season)`.
- **Frontend — `pages/LeaguePage.tsx`** (napisane przez Claude na prośbę właściciela —
  koncepty przerobione wcześniej pytaniami): `useState(2024)` dla wybranego sezonu
  (UI state), `useQuery(getSeasons)` dla listy (server state), kontrolowany `<select>`
  (`value`+`onChange` z `Number(e.target.value)`), reguły hooków (guard `if (!id)` **pod**
  hookami), `enabled: !!id` + `id!`.

### 3. Poprawka pozycji selektora
- Selektor wyśrodkowany → prawy róg (`flex justify-end`), by rozwijana lista natywnego
  `<select>` nie zasłaniała tabeli (pomiar `getBoundingClientRect`: tabela 324–941px,
  po prawej ~340px wolnego). Właściciel przesunął go ostatecznie na lewo.
- **Bug wychwycony w review:** `justify-begin` **nie istnieje** w Tailwind (działał
  „przypadkiem", bo flex domyślnie wyrównuje do lewej) → poprawione na `justify-start`.

## Czego się nauczyliśmy (do utrwalenia)
- **Front i backend gadają tylko przez URL.** Parametr funkcji (JS) ≠ dana dla serwera —
  trzeba jej wartość **wkleić do URL** (`?season=${season}`), bo backend nie widzi
  zmiennych JS.
- **Path param vs query param.** `leagueId` w ścieżce (rozpoznawany po **pozycji**:
  `/leagues/39/`), `season` w query stringu (po **nazwie**: `?season=`). Path = który
  zasób, query = filtr/opcja. Query wymaga nazw, bo parametrów może być wiele w dowolnej
  kolejności (`&`).
- **Parametr wymagany vs opcjonalny.** Z wartością domyślną (`season: int =
  DEFAULT_SEASON`) = opcjonalny (klient może pominąć — dlatego stary front działał bez
  `?season=`); bez wartości = wymagany. Backend liberalny (default), front rygorystyczny
  (`season` wymagany — bo zawsze mamy go z selektora).
- **Query jednej kolumny zwraca listę KROTEK.** `db.query(Standing.season)...all()`
  → `[(2024,), (2023,)]`, nie `[2024, 2023]` (bo można pytać o wiele kolumn). Stąd
  `row[0]`. `(2024,)` — przecinek robi krotkę jednoelementową. `DISTINCT` = unikalne.
- **Server state vs UI state** — sedno pytania właściciela („czemu `useState`, skoro
  zamieniliśmy go na `useQuery`?"). Refaktor z Sesji 11 zamienił `useState`+`useEffect`
  → `useQuery` **tylko dla danych z serwera**. `useState` wraca **wyłącznie** dla stanu
  UI (wybór sezonu — serwer o nim nie wie). `useEffect` zniknął na dobre (odpalał fetch,
  co `useQuery` robi sam).
- **`queryKey` musi zawierać `season`** — inaczej TanStack Query przy zmianie sezonu
  zwróciłby zcache'owaną starą tabelę zamiast pobrać nową.
- **Reguły hooków** — `useState`/`useQuery` muszą się wykonać przy każdym renderze, więc
  early return (`if (!id)`) idzie **pod** nimi.
- **`toLocaleString` auto-przelicza UTC → strefa lokalna** (mecz „20:00 UTC" pokaże się
  jako 21:00/22:00 czasu PL). `toLocaleDateString` = tylko dzień.
- **Natywny `<select>` popup przykrywa treść pod spodem** — nie da się tego wyłączyć
  CSS-em; rozwiązanie to pozycja, pod którą jest wolna przestrzeń.
- **`justify-begin` nie istnieje** — poprawne klasy Tailwind to `justify-start` /
  `justify-end` / `justify-center`. Zła klasa nie jest błędem lintu (to tylko string).

## Stan repo po sesji
- **Backend — nowe**: `GET /leagues/{id}/seasons` w `app/routers/competitions.py`.
  Baza: dołożone standings sezonów **2022 i 2023** (6 lig × 2) + drużyny-spadkowicze
  spoza 2024. Ruff czysty; pytest **7/7** (bez zmian — **dług: endpoint `seasons` nie ma
  jeszcze testu**, do dopisania).
- **Frontend — zmienione**: `api/standings.ts` (`getStandings` + `season`, nowa
  `getSeasons`), `components/LeagueTable.tsx` (prop `season` + `season` w `queryKey`),
  `pages/LeaguePage.tsx` (stan sezonu + `useQuery` listy + `<select>`),
  `components/MatchupCard.tsx` + `api/bracket.ts` (daty w legach).
- **Jakość**: `npm run build` zielony, oxlint **0/0**, prettier czysty; Ruff czysty,
  pytest 7/7.
- **Zapytania do API-Football**: ~12 (import standings 2022 + 2023).

## TODO na Sesję 14
1. **Selektor sezonu dla drabinek** (analogicznie do tabel): `getBracket(leagueId,
   season)` + `season` w `queryKey`, selektor na `BracketPage`. Uwaga: dla innych sezonów
   drabinki trzeba **doimportować fixtures** (`POST /import-fixtures?season=`).
2. **Po zakupie premium**: zweryfikować dostęp do sezonów 2025/26 i **2026/27** (żywy),
   doimportować; wtedy ruszyć **właściwą Fazę 2** (wyniki/terminarz drużyn + wyszukiwarka,
   endpointy `GET /teams/{id}/results`, `GET /teams/{id}/fixtures`, `GET /teams?search=`).
3. **Dług**: dopisać test pytest dla `GET /leagues/{id}/seasons`.
4. (odłożone) tabela fazy ligowej LM/LE/Konf.

## Praca domowa
> Metoda: czytaj z otwartym repo. Zobacz, jak `getSeasons`/`getStandings` i selektor
> w `LeaguePage` łączą trzy warstwy: wybór (useState) → lista (useQuery) → dane (useQuery).

### 🔴 Priorytet 1 — pod selektor drabinek i Fazę 2
1. **API-Football — plany i sezony premium** ·
   https://www.api-football.com/pricing oraz https://www.api-football.com/documentation-v3
   — sprawdź, do jakich sezonów daje dostęp płatny plan (czy 2025/26 i 2026/27) i jaki
   limit zapytań. To determinuje start właściwej Fazy 2.
2. **React — controlled components** ·
   https://react.dev/reference/react-dom/components/select
   — dlaczego `<select>` potrzebuje `value` **i** `onChange` (React trzyma prawdę o
   wartości). Zwróć uwagę na `e.target.value` (zawsze string → stąd `Number(...)`).

### 🟢 Priorytet 2 — utrwalenie
3. **TanStack Query — queryKey jako zależność** ·
   https://tanstack.com/query/latest/docs/framework/react/guides/query-keys
   — dlaczego dołożenie `season` do klucza wystarcza, by zmiana sezonu pobrała nowe dane
   (klucz = tożsamość zapytania w cache).
