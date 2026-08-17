# Sesja 9 — 17 sierpnia 2026

> Interaktywny React i pierwsza tabela na żywych danych: `useState`/`useEffect`, fetch do backendu
> z typami TS, stany loading/error, Tailwind (instalacja v4 + stylowanie), rozbicie na pliki + prettier,
> logo drużyn. (Kalendarzowo Sesja 9 = „Sesja 8 — Podstawy React + Tailwind + pierwsza tabela" z ROADMAP.)

## Co zostało zrobione

### 1. Interaktywny React — `useState` + `useEffect` (rozgrzewka)
- Teoria: komponent = funkcja odpalana przy każdym renderze; zwykła zmienna nie przeżywa re-renderu
  i nie wyzwala przerysowania. `useState` = pamięć + trigger re-render (`setX` robi jedno i drugie).
  `useEffect` = efekt uboczny wg tablicy zależności (`[]` = raz po zamontowaniu), nie co render
  (inaczej pętla fetch → setState → render → fetch…).
- Rozgrzewka (napisał właściciel): komponent `Counter` z `useState` (+1 / Reset) — „poczucie" re-renderu
  przez HMR. Ominął pułapkę `onClick={() => setCount(...)}` (funkcja, nie wywołanie), sam sięgnął po `<>`.

### 2. `LeagueTable` — fetch na żywych danych + typy TS
- **Typy TS jako lustro kontraktu API** (napisał właściciel): `Team` i `Standing` odwzorowują `schemas.py`
  (snake_case 1:1 — `goals_for`; `string | null` = Pydantic `None`; zagnieżdżony `team: Team`).
- **fetch w `useEffect`** — idiom async-w-useEffect (async funkcja wewnątrz, nie `useEffect(async …)`);
  dwa `await` (odpowiedź + `res.json()`); `setStandings(data)`. `GET /leagues/39/standings` (PL 2024/25) →
  20 wierszy. **CORS zagrał na żywo** (dwa porty).
- **Render tabeli** przez `.map` + `key={s.team.id}` (Claude podał wzór na prośbę — gęsta składnia).

### 3. Stany loading / error (twardnienie na błędy)
- `loading` = `useState(true)` (bez generyka — `true` jednoznaczne) + warunkowy render „Loading…".
- `error` = `useState<string | null>(null)` (generyk konieczny — `null` niejednoznaczne) + `try/catch/finally`.
- **Pułapka `res.ok`**: `fetch` NIE rzuca przy 404/500 → ręczny `if (!res.ok) throw` = frontendowy
  `raise_for_status()`. `finally` → `setLoading(false)`. `catch (err)` → `console.error(err)` + komunikat dla usera.

### 4. Tailwind CSS
- **Instalacja (Claude, setup)**: metoda zweryfikowana przez WebFetch — **v4.3** (`@tailwindcss/vite`
  + `@import "tailwindcss"`), NIE stara v3 (PostCSS/`init`/`tailwind.config.js`). Build potwierdził wpięcie.
- **Utility-first** (teoria): styl w `className` z gotowych atomowych klas zamiast osobnego CSS;
  „gadatliwość" rozwiązywana stylowaniem na właściwym poziomie (wiersz w `.map` = raz dla 20).
- **Stylowanie tabeli** (właściciel): `border-collapse`/`mx-auto`, `border px-3 py-1`; warianty
  `hover:`/`odd:` (zebra — potem usunięta na życzenie); `text-center` na tabeli + `text-left` na nazwie
  (dziedziczenie `text-align` + nadpisywanie na komórce).

### 5. Porządek — rozbicie na pliki + prettier (Claude, na prośbę właściciela)
- `src/components/LeagueCard.tsx` + `LeagueTable.tsx` (jeden komponent = jeden plik; `export default` /
  `import`); typy `Team`/`Standing` przeniesione do `LeagueTable.tsx`; `App.tsx` = czysty szkielet
  kompozycji (bez importu reacta). `Counter` usunięty.
- **Prettier** dodany (`npm install -D prettier`, `.prettierrc`, skrypt `npm run format`) — spłata długu
  „brak auto-formattera na froncie" (frontendowy odpowiednik `ruff format`; oxlint = `ruff check`).

### 6. Logo drużyn (właściciel)
- `<img>` + warunkowy render `{s.team.logo_url && <img/>}` (obsługa `null`) + `flex items-center gap-2`.
- Poprawka po review: nowa komórka wstawiona najpierw jako **dodatkowa** (10 kolumn, duplikat nazwy) →
  podmieniona tak, by logo+nazwa **zastąpiło** komórkę nazwy (9 kolumn zgodnych z nagłówkami).

## Decyzje (i dlaczego)
- **URL backendu na sztywno** (`http://localhost:8000/…`) w komponencie — wyniesienie do wspólnego
  helpera / zmiennej środowiskowej odłożone do Sesji 10+ (klient API / TanStack Query).
- **`league_id = 39` na sztywno** — dynamiczny wybór ligi przyjdzie z routingiem (następna sesja).
- **Tailwind v4, nie v3** — nowa, prostsza metoda; świadome ostrzeżenie o starych poradnikach w necie.
- **Prettier dodany teraz** — dług ciągnął się całą sesję (kosmetyka niełapana automatycznie).
- **Zebra usunięta** (decyzja właściciela) — preferencja jednolitych wierszy.

## Czego się nauczyliśmy (do utrwalenia)
- `useState` = pamięć, która przy zmianie przerysowuje ekran; `useEffect` = efekt wg zależności, nie co render.
- `async`/`await`: `await` wstrzymuje **funkcję**, nie przeglądarkę (JS jednowątkowy, wznowienie z kolejki);
  dwa `await` w fetchu (najpierw odpowiedź, potem parsowanie ciała `res.json()`).
- `fetch` **nie rzuca** przy 404/500 → trzeba sprawdzić `res.ok` (frontendowy `raise_for_status`).
- `.map` + `key` (lista danych → lista JSX); warunkowy render (loading/error/dane; `&&` dla opcjonalnego elementu).
- Typy TS = lustro kontraktu API (`schemas.py`); generyk `useState<…>` gdy wartość startowa niejednoznaczna (`[]`, `null`).
- Tailwind utility-first; warianty `hover:`/`odd:`; dziedziczenie `text-align` + nadpisywanie na dziecku.
- `import`/`export default`, jeden komponent = jeden plik; `App` jako szkielet kompozycji.
- Tagi małą literą = HTML (ustalone nazwy), wielką = komponenty (własne); shadowing (`catch (err)` vs stan `error`).

## TODO na Sesję 10 (ROADMAP „Sesja 9 — Routing i nawigacja")
1. **React Router**: instalacja + `Routes`/`Route`; strona główna (lista 6 lig) + `/league/:id`.
2. **`useParams`**: `LeagueTable` czyta `id` z URL zamiast zahardkodowanego `39` (komponent reużywalny dla 6 lig).
3. **Nawigacja** (`Link`) między ligami + layout z nagłówkiem.
4. *(jeśli zostanie czas)* wyniesienie bazowego URL API do jednego miejsca (przygotowanie pod TanStack Query, S11).

## Stan repo po sesji
- **Frontend:** nowe `src/components/LeagueCard.tsx`, `src/components/LeagueTable.tsx`; `App.tsx` odchudzony
  do szkieletu; `.prettierrc`; `package.json` (+`tailwindcss`, `@tailwindcss/vite`, `prettier`, skrypt `format`);
  `vite.config.ts` (+plugin Tailwind); `index.css` (+`@import "tailwindcss"`); `main.tsx` (format prettier).
- **Jakość frontu:** `npm run lint` (oxlint) **0/0**, `npm run build` (tsc + vite) zielony, `npm run format` czysty.
- **Backend:** bez zmian (7/7 testów nadal aktualne); migracji nie przybyło; **0 zapytań** do API-Football
  (dane serwowane z lokalnej bazy przez istniejące endpointy).
- **Commit + push:** robi właściciel (propozycja message w czacie).

## Praca domowa
### 🔴 Priorytet 1 — przed Sesją 10 (routing)
1. **React Router — routing** · https://reactrouter.com — koncepty `Routes` / `Route`. Na co patrzeć: jak
   jedna aplikacja (SPA) pokazuje różne „strony" bez przeładowania, mapując ścieżkę URL na komponent.
2. **`useParams`** · https://reactrouter.com (sekcja hooks/API) — czytanie parametru z URL (`/league/:id`).
   Na co patrzeć: jak `:id` z adresu trafia do komponentu (zastąpi nasze zahardkodowane `39`).
3. **`Link`** · https://reactrouter.com — nawigacja między widokami bez przeładowania (zamiast `<a href>`).

### 🟢 Priorytet 2 — bez terminu
4. **Zmienne środowiskowe w Vite** · https://vite.dev/guide/env-and-mode — `import.meta.env`, prefiks `VITE_`.
   Pod wyniesienie bazowego URL API z kodu (przyda się przy kliencie API / deployu).

**Metoda:** czytaj z otwartym repo. Nasza `LeagueTable` ma na sztywno `39` — przy routingu zamienimy to
na `id` z URL; zobacz w docs, jak `useParams` to umożliwia. To domyka „pierwszą tabelę" i otwiera nawigację
po wszystkich 6 ligach.
