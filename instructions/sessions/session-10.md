# Sesja 10 — 17 sierpnia 2026

> Routing i nawigacja w SPA: React Router (v7), strony `Home`/`League`, `useParams`,
> nawigacja `Link`, wspólny layout z nagłówkiem, oraz bazowy URL API wyniesiony do
> `.env` przez zmienne środowiskowe Vite. (Kalendarzowo Sesja 10 = „Sesja 9 — Routing
> i nawigacja" z ROADMAP.)

## Co zostało zrobione

### 1. React Router — instalacja + `<BrowserRouter>`
- Teoria: SPA ładuje jeden HTML, resztę rysuje JS; routing = „patrz na URL, renderuj
  odpowiedni komponent" bez przeładowania (zachowany stan, działa wstecz/dalej, dzielenie linkiem).
- `npm install react-router-dom` (v7.18.2, +3 zależności; setup zrobił Claude).
- **`<BrowserRouter>`** owinął `<App />` w `main.tsx` (wewnątrz `StrictMode`) — włącza kontekst
  routingu dla całego drzewa. „Browser" = History API (czyste adresy, bez `#`). Wizualnie nic
  się nie zmieniło (router bez tras renderuje children).

### 2. Strony + trasy (`<Routes>`/`<Route>`)
- **Podział „strony vs komponenty"** (konwencja): nowy folder `src/pages/` (widoki przypięte do
  URL) obok `src/components/` (klocki). Powstały `HomePage.tsx` i `LeaguePage.tsx`.
- **Plik danych `src/data/leagues.ts`** (napisał właściciel): `export type League` + `export const
  LEAGUES: League[]` (6 lig z `id` z API-Football, potwierdzone z `app/constants.py`). Pierwszy
  **eksport nazwany** (vs `export default` dla komponentów) — import w klamrach.
- **`HomePage`** (właściciel): `.map` po `LEAGUES` → reużyty `LeagueCard`; `key={league.id}`.
  Utrwalona pułapka `.map`: **okrągłe** nawiasy po `=>` (niejawny return), nie klamry (blok).
- **`App.tsx`** przerobiony na `<Routes>` z dwoma `<Route>`: `/` → `HomePage`,
  `/leagues/:id` → `LeaguePage`. `element={<HomePage />}` (gotowy JSX, nie nazwa).
  Poprawki po review: usunięte wiszące importy (`LeagueCard`/`LeagueTable`), ścieżka ustalona na
  **`/leagues/:id`** (mnoga — spójna z backendem `GET /leagues/{id}/...`).
- **Weryfikacja na żywo** (dev server + backend w WSL, przeglądarka): `/` → 6 kart, `/leagues/39` →
  tabela PL. Pokazano problem: `/leagues/140` wciąż zwracało PL, bo `LeagueTable` miał zaszyte `39`
  → motywacja do `useParams`.

### 3. `useParams` — jeden komponent, wszystkie ligi
- **`LeaguePage`** (właściciel): `const { id } = useParams();` czyta segment dynamiczny `:id`.
  Wartość to zawsze **string**; TS widzi `string | undefined` → **strażnik** `if (!id) return …`
  (zawężanie typu — po `if` `id` jest pewnym `string`). `id` przekazane do tabeli jako prop `leagueId`.
- **`LeagueTable`** (właściciel): przyjmuje `leagueId: string` (typ props jak w `LeagueCard`); fetch
  na **template literal** `` `${…}/leagues/${leagueId}/standings` ``; **tablica zależności `[leagueId]`**
  (nie `[]`) — efekt powtórzy się przy zmianie ligi (niezbędne pod nawigację `Link` bez przeładowania).
- **Złapany podstępny błąd**: cudzysłowy zamiast backticków → `${leagueId}` poszło dosłownie. Lekcja:
  kompilator tego nie wyłapie (poprawny string), dlatego review + test na żywo są konieczne.
- **Weryfikacja**: `/leagues/140` → realnie La Liga (Barcelona), `/leagues/78` → Bundesliga (Bayern).

### 4. Nawigacja `<Link>` + layout z nagłówkiem
- **`<Link>`** vs `<a href>`: `to="…"` zmienia URL i renderuje trasę **bez przeładowania** (renderuje
  się jako `<a>`, więc „otwórz w nowej karcie" działa). Karty na `HomePage` owinięte w
  `<Link to={` `` `/leagues/${league.id}` `` `}>`; `key` przeniesiony na `Link` (najbardziej zewnętrzny
  element `.map`).
- **Layout** (w `App.tsx`): `<header>` z klikalnym `<h1>` (`<Link to="/">`) **nad** `<Routes>` —
  renderuje się zawsze, `<Routes>` podmienia tylko środek. Zduplikowany `<h1>` usunięty z obu stron
  (spłata długu z Sesji 9). `<header>` renderuje się jako semantyczny `banner` (dostępność).
- **Weryfikacja**: klik karty La Liga → tabela (SPA nav); klik nagłówka na `/leagues/78` → powrót na `/`.

### 5. Bazowy URL API — zmienne środowiskowe Vite (wariant „pro")
- Teoria: konfiguracja poza kodem w `.env`; **prefiks `VITE_` obowiązkowy** (tylko takie zmienne Vite
  udostępnia frontowi — zabezpieczenie przed wyciekiem sekretów). **Zmienne `VITE_` NIE są tajne**
  (lądują w bundlu widocznym w przeglądarce) — służą konfiguracji per-środowisko, nie sekretom.
  Po zmianie `.env` → **restart dev servera**.
- `frontend/.env` + `frontend/.env.example` (`VITE_API_URL=http://localhost:8000`; `.gitignore`
  już pokrywał `.env` rekursywnie, `.env.example` przez `!` przechodzi do repo).
- **`src/api/config.ts`**: `export const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000"`
  (`??` = fallback gdy zmiennej brak; jedno źródło prawdy — reszta kodu importuje stałą, nie dotyka `import.meta.env`).
- `LeagueTable` fetchuje na `` `${API_BASE_URL}/leagues/${leagueId}/standings` ``. Zaszyty
  `http://localhost:8000` zniknął z kodu. Po restarcie dev servera tabela ładuje się z adresu z konfiguracji.

## Decyzje (i dlaczego)
- **Ścieżka `/leagues/:id` (mnoga)** — decyzja właściciela; spójna z backendem i konwencją REST
  (`/leagues/39` = element kolekcji). Ważne: **jedna** spójna wszędzie (trasa + linki).
- **Warstwa „strony" (`LeaguePage`) czyta URL, `LeagueTable` dostaje prop** — separacja: komponent
  prezentacyjny pozostaje „czysty" (reużywalny, nie wie o routingu), wiedza o URL siedzi w stronie.
- **`<Link>` owija `LeagueCard` w `HomePage`** (nie przerabiamy `LeagueCard`) — ta sama filozofia
  czystego komponentu.
- **Zmienne środowiskowe Vite (wariant B), nie prosta stała** — realizuje pracę domową o `import.meta.env`,
  to realny wzorzec konfiguracji i przygotowanie pod deploy (prod URL bez tykania kodu).
- **`src/api/config.ts`** — zalążek wspólnego klienta API (część planu ROADMAP „Sesja 10").
- **Dev server i backend uruchamiane w WSL** przez Claude tylko do weryfikacji na żywo (przeglądarka
  w trybie bez obrazu → klik `Link` wywołany programowo; logika identyczna).

## Czego się nauczyliśmy (do utrwalenia)
- Routing w SPA: `BrowserRouter` (kontekst) → `Routes` (pierwszy pasujący `Route`) → komponent; wszystko
  po stronie przeglądarki, bez przeładowania.
- `<Route path="/leagues/:id" element={<X/>} />`: `:id` = segment dynamiczny; `element` bierze gotowy JSX.
- `useParams()` → obiekt z parametrami (klucz = nazwa z trasy); wartość zawsze **string**; TS `string | undefined`
  → obsługa braku strażnikiem (`if (!id) return`) = zawężanie typu.
- **Tablica zależności `useEffect`**: `[]` = raz; `[leagueId]` = ponownie przy zmianie — wpisuj wszystko,
  czego efekt używa z zewnątrz (inaczej „stara" wartość / brak odświeżenia).
- `<Link to>` zamiast `<a href>` = nawigacja bez przeładowania; `key` na najbardziej zewnętrznym elemencie `.map`.
- Layout = wspólna oprawa (`header`) nad `<Routes>`; `<header>` → landmark `banner`.
- **Template literal** wymaga backticków `` ` `` — cudzysłowy nie interpolują `${…}` (błąd, którego kompilator nie łapie).
- Eksport nazwany (`export const`/`export type`, import w klamrach) vs `export default` (komponenty).
- Zmienne środowiskowe Vite: `.env` + prefiks `VITE_` + `import.meta.env`; **nie są tajne**; `??` jako fallback.

## TODO na Sesję 11 (ROADMAP „Sesja 10 — Porządne pobieranie danych")
1. **TanStack Query**: instalacja + `QueryClientProvider`; `useQuery` — cache, `isLoading`/`isError`,
   refetch w tle. Teoria: dlaczego lepsze niż ręczny `useState`+`useEffect`+`fetch`.
2. **Refaktor `LeagueTable`**: ręczny fetch (3× `useState` + `useEffect` + `try/catch`) → jeden `useQuery`.
3. **Wspólny klient API** w `src/api/`: rozbudowa o funkcje pobierające (np. `getStandings(leagueId)`),
   obok istniejącego `config.ts`.
4. *(drobiazg z tej sesji)* sprawdzić wygląd linków/nagłówka (domyślny styl `<a>`); ewentualnie okiełznać Tailwindem.

## Stan repo po sesji
- **Frontend — nowe pliki:** `src/pages/HomePage.tsx`, `src/pages/LeaguePage.tsx`, `src/data/leagues.ts`,
  `src/api/config.ts`, `.env` (lokalny, ignorowany), `.env.example`.
- **Frontend — zmienione:** `main.tsx` (+`BrowserRouter`), `App.tsx` (Routes + layout `header`),
  `components/LeagueTable.tsx` (prop `leagueId`, `API_BASE_URL`, deps `[leagueId]`), `package.json`
  (+`react-router-dom ^7.18.2`).
- **Jakość frontu:** `npm run build` (tsc + vite) zielony, `npm run lint` (oxlint) **0/0**,
  `npm run format` (prettier) czysty.
- **Backend:** bez zmian (uruchamiany tylko do weryfikacji; 7/7 testów nadal aktualne). **0 zapytań**
  do API-Football (dane z lokalnej bazy).
- **Commit + push:** robi właściciel (propozycja message w czacie).

## Praca domowa
### 🔴 Priorytet 1 — przed Sesją 11 (TanStack Query)
1. **TanStack Query — Overview + Quick Start** · https://tanstack.com/query/latest/docs/framework/react/overview
   — na co patrzeć: jaki problem rozwiązuje (server state: cache, deduplikacja, odświeżanie) i dlaczego
   zastępuje ręczny `useEffect`+`fetch`.
2. **`useQuery`** · https://tanstack.com/query/latest/docs/framework/react/guides/queries — `queryKey`
   (klucz cache) i `queryFn` (funkcja pobierająca); stany `isLoading` / `isError` / `data`. Porównaj z tym,
   co ręcznie napisaliśmy w `LeagueTable` (3× `useState` + `try/catch/finally`).
3. **`QueryClient` + `QueryClientProvider`** · https://tanstack.com/query/latest/docs/framework/react/quick-start
   — jak (podobnie do `BrowserRouter`) owija się aplikację, żeby `useQuery` działało.

### 🟢 Priorytet 2 — bez terminu
4. **Wzorzec „warstwa API"** — pomyśl, jak `src/api/config.ts` rozrośnie się o funkcje typu
   `getStandings(leagueId)` (fetch + zwrot typu `Standing[]`), które `useQuery` wywoła jako `queryFn`.

**Metoda:** czytaj z otwartym repo. Nasza `LeagueTable` ręcznie żongluje `loading`/`error`/`data` —
zobacz w docs, jak `useQuery` robi to za nas jednym wywołaniem i jeszcze dokłada cache. To domyka
„porządne pobieranie danych" i sprząta komponent.
