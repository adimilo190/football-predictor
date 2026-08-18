# Sesja 11 — 18 sierpnia 2026

> Porządne pobieranie danych: **TanStack Query** (cache i stany zamiast ręcznego
> `useState`+`useEffect`+`fetch`), warstwa API (`getStandings`), refaktor `LeagueTable`
> na jeden `useQuery`. Plus kosmetyka Fazy 1: karty lig (siatka + hover) i nagłówek.
> (Kalendarzowo Sesja 11 = „Sesja 10 — Porządne pobieranie danych" z ROADMAP.)

## Co zostało zrobione

### 1. TanStack Query — instalacja + `QueryClientProvider`
- Teoria: TanStack Query zarządza **server state** — danymi, których właścicielem jest serwer.
  Zamiast ręcznie prowadzić `loading`/`error`/`data` w każdym komponencie, deklarujesz „skąd
  i pod jakim kluczem" — a biblioteka daje cache, deduplikację i odświeżanie w tle.
- `npm install @tanstack/react-query` (v`^5.101.4`, +`query-core`) — setup zrobił Claude.
- **`QueryClient` + `QueryClientProvider`** owinięte wokół `<App/>` w `main.tsx` (właściciel) —
  dokładnie ta sama mechanika co `BrowserRouter`. Różnica: provider wymaga gotowej instancji
  (`const queryClient = new QueryClient()` na górze modułu → powstaje **raz**) podanej przez prop `client`.
  Wizualnie nic — provider bez „konsumenta" jest niewidoczny (jak router bez tras w Sesji 10).

### 2. Warstwa API — `src/api/standings.ts` (napisana wspólnie)
- **Typy `Team`/`Standing` przeniesione** z `LeagueTable` do warstwy API — modelują dane serwera,
  więc ich miejsce jest tu, nie w komponencie. Dodany `export`.
- **`getStandings(leagueId: string): Promise<Standing[]>`**: `fetch` na template literal +
  `if (!res.ok) throw new Error(...)` + `return res.json()`. Zero `useState`/`try/catch` —
  funkcja tylko pobiera i zwraca (albo rzuca).
- **Kluczowa lekcja:** `throw` przy `!res.ok` to **most do `isError`**. `fetch` nie odrzuca
  Promise'a na 4xx/5xx (tylko na awarii sieci), a TanStack Query rozpoznaje błąd po **odrzuconym
  Promisie** — bez `throw` błąd 500 zostałby uznany za „sukces z pustką".

### 3. Refaktor `LeagueTable` na `useQuery` (SEDNO sesji, właściciel)
- Jeden `useQuery({ queryKey, queryFn })` zamiast 3× `useState` + `useEffect` + `try/catch/finally`
  (~20 linii boilerplate'u mniej).
- **`queryKey: ["standings", leagueId]`** — etykieta w cache: zasób + to, co go różnicuje.
  Cache per liga; zmiana `leagueId` automatycznie pobiera nowe dane. **Zastępuje** dawną tablicę
  zależności `[leagueId]`. (Właściciel złapał to sam.)
- **`queryFn: () => getStandings(leagueId)`** — **strzałka** obowiązkowa: Query chce funkcję do
  odpalenia później, nie natychmiastowego wywołania. (Też złapane samodzielnie.)
- **Strażnik `if (!data) return null;`** — `data` to `Standing[] | undefined` (na starcie brak),
  a `isLoading`/`isError` nie zawężają jego typu. Trzeci guard w duchu `if (!id)` z Sesji 10;
  `if/else` spłaszczone do **guard clauses** (wczesne `return`, bez `else`).
- **Typ `data` wywnioskowany** z `getStandings` (→ `Promise<Standing[]>`), więc komponent
  importuje tylko `getStandings`, a `s` w `.map` jest w pełni otypowany bez słowa `Standing`.

### 4. Kosmetyka Fazy 1 — karty i nagłówek (Tailwind, Claude na prośbę właściciela)
- **`LeagueCard`**: martwa klasa `league-card` (nigdzie niezdefiniowana) → utility: `border`,
  `rounded-lg`, `p-4`, `shadow-sm`+`hover:shadow-md`, `transition`, `cursor-pointer`; nazwa
  `font-semibold text-lg`, kraj `text-sm text-gray-500`.
- **`HomePage`**: fragment `<>` → siatka `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 p-4`.
  Pierwsze **responsywne prefiksy** (mobile-first: baza = najmniejszy ekran, `sm:`/`lg:` = od breakpointa w górę).
- **`App` (nagłówek)**: `<header>` dostał `border-b` (linia oddzielająca), link-tytuł `inline-block`
  + `transition hover:opacity-80` (feedback klikalności powrotu do `/`).
- **Tailwind preflight** (odkrycie): `@import "tailwindcss"` wciąga reset, który m.in. zeruje
  domyślny niebieski/podkreślony `<a>` (`color/text-decoration: inherit`) oraz style nagłówków —
  dlatego `h3` trzeba było wyróżnić ręcznie, a linki nie były „brzydkie", tylko za mało widoczne.

## Decyzje (i dlaczego)
- **Warstwa API w osobnym pliku** (`standings.ts`, nie w `config.ts`) — inna odpowiedzialność
  (funkcje pobierające vs konfiguracja adresu). Zalążek wspólnego klienta z ROADMAP.
- **`queryFn` woła `getStandings`** (a nie `fetch` inline) — komponent nie wie „jak" się pobiera;
  ta sama funkcja da się reużyć i przetestować.
- **Guard clauses zamiast `if/else`** — każdy niepożądany stan odcinamy wcześnie, na końcu zostaje
  happy-path; TypeScript zawęża `data` do `Standing[]`.
- **Kosmetykę pisał Claude** (na wyraźną prośbę właściciela) — z wyjaśnieniem każdej klasy;
  sedno (Krok 3, `useQuery`) właściciel złożył sam.
- **Siatka responsywna od razu** — mały koszt, a to przedsmak „responsywności" (osobne zadanie
  w szlifach Fazy 1) i lepsze pierwsze wrażenie w portfolio.

## Czego się nauczyliśmy (do utrwalenia)
- **Server state vs UI state**: dane z serwera lepiej oddać bibliotece (cache/dedup/refetch)
  niż prowadzić ręcznie w każdym komponencie.
- **`useQuery`**: `queryKey` (klucz cache; wpisz to, co różnicuje dane) + `queryFn` (funkcja
  pobierająca, **strzałka**); zwraca `data`/`isLoading`/`isError` — koniec trzech `useState`.
- **`fetch` nie rzuca na 4xx/5xx** → w `queryFn` sami `throw` przy `!res.ok`, żeby powstał `isError`.
- **`data` bywa `undefined`** — dodaj strażnik przed `.map` (zawężenie typu).
- **Typy „płyną" z warstwy API** — `useQuery` wnioskuje typ `data` z `queryFn`.
- **Tailwind preflight** resetuje style przeglądarki (linki, nagłówki) — buduj wygląd wyłącznie klasami.
- **Responsywne prefiksy** (`sm:`/`md:`/`lg:`) — mobile-first, włączają klasę od danej szerokości w górę.
- **Praktyka (VS Code):** gdy narzędzie zapisuje plik „od spodu", a masz go otwartego z niezapisanym
  buforem — przy przeładowaniu wybierz **Don't Save** (wersja z dysku jest tą właściwą).

## Nowa wizja UX (zanotowana w ROADMAP → „Wizja docelowego UX")
- HomePage jako **rozwijana lista krajów** + puchary europejskie (LM/LE/Liga Konferencji) jako
  osobne pozycje; klik w kraj → accordion (liga + puchar krajowy); klik w rozgrywkę → tabela/drabinka.
- **Selektor roku** na stronie rozgrywek (przeglądanie sezonów).
- **Zakładka predyktorów** na HomePage — dalszy etap.
- Implikacje: wybór roku wymaga danych wielosezonowych (API Free: 2022/23–2024/25); LE i Liga
  Konferencji do **doimportowania** (w bazie jest tylko LM); accordion + selektor to nowe komponenty.

## TODO na Sesję 12 (ROADMAP „Sesja 11 — Drabinki pucharowe (UI)")
> Rekomendacja: domknąć Fazę 1 **drabinkami** (backend gotowy: `GET /leagues/{id}/bracket`, dane
> LM + puchary krajowe w bazie) i przy okazji **utrwalić `useQuery`** na drugim typie danych.
1. **Wspólny klient API — rozbudowa**: `src/api/bracket.ts` z `getBracket(leagueId)` + typy
   `Fixture`/`BracketRound` (lustro `schemas.py`); ewentualnie `getFixtures`.
2. **`useQuery` dla drabinki** (`queryKey: ["bracket", leagueId]`) — ten sam wzorzec co standings.
3. **Komponent `Bracket`**: rundy jako **kolumny** (CSS grid/flex, `overflow-x-auto` przy wielu
   rundach), mecze w rundzie; backend już grupuje i sortuje rundy po dacie.
4. **Dojście do drabinki** (trasa/nawigacja do pucharu) — do przemyślenia razem z nową wizją
   (accordion krajów). Decyzja na starcie sesji: drabinki „na sucho" vs start przebudowy nawigacji.

## Stan repo po sesji
- **Frontend — nowy plik:** `src/api/standings.ts` (typy + `getStandings`).
- **Frontend — zmienione:** `main.tsx` (+`QueryClientProvider`), `components/LeagueTable.tsx`
  (ręczny fetch → `useQuery`, -~20 linii), `components/LeagueCard.tsx` (Tailwind), `pages/HomePage.tsx`
  (siatka), `App.tsx` (nagłówek), `package.json` + `package-lock.json` (+`@tanstack/react-query`).
- **Instrukcje:** `ROADMAP.md` (sekcja „Wizja docelowego UX" + status Sesji 10 fazowej), ten log,
  wpis w `progres.md`.
- **Jakość:** `npm run build` (tsc+vite) zielony, `npm run lint` (oxlint) **0/0**, `npm run format` czysty.
- **Backend:** bez zmian (7/7 testów aktualne). **0 zapytań** do API-Football (dane z lokalnej bazy).
- **Commit + push:** propozycja message w czacie; wykonuje właściciel.

## Praca domowa
### 🔴 Priorytet 1 — przed Sesją 12 (drabinki + `useQuery` na drugim zasobie)
1. **TanStack Query — Queries (utrwalenie)** · https://tanstack.com/query/latest/docs/framework/react/guides/queries
   — bo drabinka pójdzie **tym samym** wzorcem co standings. Zwróć uwagę na `queryKey` z parametrami
   (dlaczego `["bracket", leagueId]`, a nie samo `"bracket"`).
2. **Tailwind — Flexbox & Grid** · https://tailwindcss.com/docs/flex + https://tailwindcss.com/docs/grid-template-columns
   — do ułożenia rund jako kolumn obok siebie. Zwróć uwagę na `overflow-x-auto` (przewijanie w poziomie,
   gdy rund jest dużo — np. Liga Mistrzów).
3. **CSS-Tricks — A Complete Guide to Flexbox** · https://css-tricks.com/snippets/css/a-guide-to-flexbox/
   — fundament pod `Bracket`: oś główna (`flex-direction: row/column`), `justify-content`, `align-items`,
   `gap`. Na co patrzeć: różnica „kierunek wiersz vs kolumna" (rundy w wierszu, mecze w kolumnie).

### 🟢 Priorytet 2 — bez terminu (pod nową wizję)
4. **HTML `<details>` / accordion** · https://developer.mozilla.org/en-US/docs/Web/HTML/Element/details
   — najprostszy natywny „rozwijany" element pod listę krajów; alternatywa to `useState` + toggle.

**Metoda:** czytaj z otwartym repo. Zobacz, jak `getStandings` + `useQuery` z Kroku 2–3 przełożą się
1:1 na `getBracket` — cała maszyneria data-fetchingu jest już gotowa, dojdzie tylko **nowy komponent
UI** (`Bracket`). To domyka Fazę 1 (UI tabel **i drabinek**).
