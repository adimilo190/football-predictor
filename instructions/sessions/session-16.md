# Sesja 16 — 4 września 2026

> **Frontend Fazy 2 na żywych danych 2026 — cały feature end-to-end.** Rozgrzewka:
> testy 3 endpointów z S15 (pytest 8→12). Potem front: warstwa API `teams.ts`,
> własny hook `useDebounce`, `SearchPage` (kontrolowany input + debounce + `useQuery`),
> `TeamPage` (dwie kolumny past/future + nagłówek drużyny, reużyty `MatchupCard`),
> klikalne wyniki (`Link`) i wejście „Find team" z HomePage. Na koniec **wymuszony
> ciemny motyw dla wszystkich** + rozjaśnione MatchupCardy. Sesja bardzo gęsta
> konceptowo (React od podstaw) i z dużą liczbą pytań właściciela.

## Decyzje na starcie (i dlaczego)
- **ZMIANA ZAKRESU Fazy 2 — bez „ulubionych"**: właściciel doprecyzował, że NIE chce
  zapamiętywania drużyn (żadnego `localStorage`, hooka `useFavorites`, dashboardu
  „Moje drużyny"). Feature = **sama wyszukiwarka drużyn + podgląd ich meczów**.
  Świadome zawężenie MVP (mniej kodu, czystszy zakres). ROADMAP zaktualizowany.
- **Kolejność**: rozgrzewka testami (dług z S15) → dopiero potem frontend — nasz rytm.
- **Reuse `MatchupCard` w `TeamPage`** (pomysł właściciela): pojedynczy mecz to
  „dwumecz z jedną nogą", a `MatchupCard` już to obsługuje (bez agregatu, gole `null`
  → „-"). Zero zmian w karcie; potrzebny tylko adapter `Fixture → Matchup`. NIE użyto
  `groupIntoMatchups` (grupuje dom+wyjazd — złe dla listy meczów drużyny).
- **Wymuszony ciemny motyw** (prośba właściciela): wartości „dark" przeniesione do
  `:root` na stałe + `color-scheme: dark` + usunięta bramka `@media (prefers-color-scheme)`.

## Co zostało zrobione

### Rozgrzewka — testy 3 endpointów z S15 (pytest 8 → 12)
- `test_get_team_past_matches` — scenariusz **szczelny** A/B/C/D: X u siebie `FT`,
  X na wyjeździe `FT`, X u siebie `NS` (odsiew statusu), dwaj rywale bez X `FT`
  (odsiew `or_`). Asercje: `len==2`, kolejność `desc`, home/away → dowód obu gałęzi `or_`.
  Lekcja przy okazji: seed musi spełniać `NOT NULL` (`league_id`, `season`).
- `test_get_team_future_matches` — lustro (`NS` + `asc`). Review: **dane spójne z domeną**
  — mecz `NS` NIE może mieć goli (usunięte z 3 fixture'ów; `FT` dostał wynik).
- `test_search_teams` — **„zielone ≠ szczelne"**: pierwsza wersja (Manchester×2, prefiks
  „manchester" + zbiór na wynikach) przechodziła, ale przepuszczała `startswith` i sort.
  Poprawka: fraza `eSTEr` (substring w środku słowa + case-insensitive) i asercje **po
  indeksie** (bronią `order_by`). + pusty wynik (`Bayern` → `[]`, brak guardu 404).
- `test_team_not_found` — 404 dla `past` i `future` (dwa osobne guardy). Lekcja:
  `"""..."""` w środku funkcji to **nie** komentarz, tylko martwy string (docstring =
  tylko pierwsza instrukcja funkcji).

### Frontend 2.1 — warstwa API `frontend/src/api/teams.ts`
- `searchTeams(searchTerm)`, `getPastMatches(teamId)`, `getFutureMatches(teamId)` —
  wzorzec jak `standings.ts` (`fetch` → `if (!res.ok) throw` → `res.json()`).
- **Reuse typów** `Team`/`Fixture` przez `import type` (nie duplikować — jedno źródło prawdy).
- `encodeURIComponent(searchTerm)` w URL wyszukiwarki (fraza = wolny tekst).
- **Decyzja `last`/`next`** (dyskusja z właścicielem): NIE dublować domyślnej `5` na froncie
  (backend ma default) — funkcje bez tych parametrów, backend rządzi liczbą (DRY, YAGNI).
- `teamId: string` (spójność z resztą API + `useParams` zwraca string).

### Frontend 2.2 — hook `frontend/src/hooks/useDebounce.ts`
- `useDebounce<T>(value, delayMs)`: `useState` + `useEffect` z `setTimeout` i **cleanupem**
  `clearTimeout`. Sedno: przy każdym znaku React woła cleanup poprzedniego efektu → kasuje
  stary timer → tylko przerwa ≥ `delayMs` przepuszcza wartość. Nowy folder `hooks/`
  (konwencja: reużywalna logika ze stanem). Debounce prowadzony przeze mnie (umowa z S15).

### Frontend 2.3 — `frontend/src/pages/SearchPage.tsx` (+ trasa `/teams`)
- Kontrolowany `<input>` (`useState` term) → `useDebounce(term, 300)` → `useQuery`
  (`queryKey: ["teamSearch", debouncedTerm]`, `enabled: debouncedTerm.length > 0`).
- Render stanów przez **zmienną + `if`** (nie early return — input musi zostać na ekranie).
- **Weryfikacja na żywo**: „real" → 12 drużyn (substring: Montreal/Villarreal); szybkie
  wpisanie „barca" (5 znaków co 50 ms) → **1 zapytanie** `search=barca` (nie 5) — dowód debounce.

### Frontend 2.4 — `frontend/src/pages/TeamPage.tsx` (+ trasa `/teams/:id`) + klikalne wyniki
- Dwa `useQuery` (past/future), guardy **po** hookach (Reguła Hooków — złapany bug:
  drugi `useQuery` po early returnie), guard `if (!pastMatches || !futureMatches) return null`
  = **zawężenie typu** (koniec `?.`/`!` w renderze). Adapter `fixtureToMatchup` lokalnie
  w `TeamPage` (nie w karcie — karta jest prezentacyjna).
- Layout: nagłówek (logo + nazwa) z drużyny **wyłuskanej z pierwszego meczu** (brak
  endpointu `GET /teams/{id}` — użyto danych, które już mamy) + **dwie kolumny** `flex gap-8`
  (past lewo / future prawo, `flex-1`).
- `SearchPage`: wyniki jako `<Link to={`/teams/${team.id}`}>` (client-side nav).
- **Weryfikacja na żywo**: „real" → klik „Real Madrid" → `/teams/541` → mecze Realu
  (past z wynikami, future „-", cross-competition: La Liga + Liga Mistrzów).

### Wymuszony ciemny motyw + rozjaśnione MatchupCardy
- `index.css`: wartości dark w `:root`, `color-scheme: dark`, usunięta `@media
  (prefers-color-scheme: dark)`. Tło `rgb(22,23,29)` dla wszystkich (zweryfikowane).
- `MatchupCard`: karta `bg-gray-800` + `border-gray-700` (unosi się nad tłem),
  pudełka wyników `bg-gray-100` → `bg-gray-700` (czytelne jasne cyfry).
- **Świadomie odłożone**: dark-polish reszty komponentów (tabela ligowa, hovery).

### Narzędziowo
- `.vscode/settings.json` (lokalny, `.vscode/` w `.gitignore`) — format-on-save:
  Ruff (Python, 4 spacje) / Prettier (TS, 2 spacje) per język.

## Czego się nauczyliśmy (React od podstaw — bardzo dużo)
- **Hooki**: funkcja `use*` która woła inne hooki (używa mechanizmów React); reguły
  (top-level, tylko z komponentów/hooków); custom hook = wyodrębniona logika ze stanem.
- **`useEffect`**: callback odpalany PO renderze, ponownie tylko gdy zmieni się coś w
  tablicy zależności; cleanup (zwracana funkcja) woła się przed kolejnym efektem i przy
  odmontowaniu. `setTimeout(fn, ms)` — `() => ...` to funkcja „na potem" (bez `()` nie odpala się teraz).
- **`() =>`** (arrow) = funkcja jako wartość (callback); `A && B` w JSX = warunkowy render
  (React ignoruje `false`/`null`); alternatywy: ternary, `if` + zmienna. `??`/`?.` vs jawne `if`.
- **`let` vs `const`**: `const` = przypisanie raz przy deklaracji; `let` gdy wartość zapada
  później (np. w gałęzi `if`). Domyślnie `const`.
- **Render = snapshot**: komponent to funkcja wołana wielokrotnie; każdy render ma **świeży**
  komplet `const`; pamięć między renderami żyje w `useState`, nie w `const`.
- **`import type` vs zwykły import**: typ istnieje tylko przy kompilacji (wymazany w JS);
  `import { Team }` (wartość) typu → runtime crash „does not provide an export". Typy →
  `import type`. Importy są **per plik**.
- **Zawężanie typu** (`if (!x) return`): TS śledzi przepływ sterowania — guard na danych
  usuwa `undefined` z typu poniżej (`isLoading` tego NIE robi). `data` z `useQuery` = `T | undefined`.
- **CSS — warstwy Tailwind v4**: utilki są w `@layer`; **nielayerowany CSS bije layerowane
  utilki** → globalny `h1 { margin/font-size }` z szablonu `index.css` nadpisywał `mb-4`/`text-2xl`.
  Fix: użyć `<div>` zamiast `<h1>` (albo posprzątać `index.css`).
- **Flexbox — dwie osie**: `items-*` = oś poprzeczna (pionowo w rzędzie), `justify-*` = oś
  główna (poziomo). `flex` układa dzieci w rząd (kolejność w kodzie = od lewej), `flex-1` = równe szerokości.
- **Tailwind `text-*`**: przeciążone — `text-xl`/`text-[20px]` = rozmiar, `text-white` = kolor.
- **Motyw**: `prefers-color-scheme` (respektuje system) vs wymuszony (wartości w `:root`);
  klasy Tailwinda mają **sztywne** kolory (nie zmieniają się z motywem) → dark wymaga per-komponent.
- **Prettier NIE formatuje kodu z błędem składni** (parser potrzebuje poprawnego kodu);
  „nie sformatowało" = sygnał błędu składni. Formatter ≠ linter.
- **WSL/Vite**: watcher plików bywa ślepy na zapisy z Windowsa → czasem trzeba **restart
  dev-servera**, żeby złapał zmiany/wygenerował nowy CSS. VS Code bez remote-WSL widzi tylko
  „Install" (nie „Install in WSL") — wtyczki działają lokalnie na plikach z `\\wsl.localhost\`.

## Stan repo po sesji
- **Frontend Fazy 2 — KOMPLETNY (rdzeń)**: wyszukiwarka + podgląd meczów, klikalny, z HomePage.
  - `frontend/src/api/teams.ts` — **NOWY** (3 funkcje).
  - `frontend/src/hooks/useDebounce.ts` — **NOWY** (custom hook).
  - `frontend/src/pages/SearchPage.tsx` — **NOWY** (debounce + `useQuery` + `Link`).
  - `frontend/src/pages/TeamPage.tsx` — **NOWY** (dwie kolumny + nagłówek + reuse `MatchupCard`).
  - `frontend/src/App.tsx` — trasy `/teams` i `/teams/:id`.
  - `frontend/src/pages/HomePage.tsx` — karta „Find team" → `/teams`.
  - `frontend/src/components/MatchupCard.tsx` — style pod dark (`bg-gray-800`/`700`).
  - `frontend/src/index.css` — wymuszony ciemny motyw.
  - `.vscode/settings.json` — **NOWY** (format-on-save; lokalny, poza gitem).
  - `tests/test_main.py` — +4 testy (**12/12**).
- **Baza**: bez zmian danych (leagues 15, teams 1962, standings 572, fixtures 7980).
- **Jakość**: pytest **12/12** + Ruff czysty; frontend `tsc` + oxlint 0/0 + prettier czysty.
  API-Football (Pro): tylko odczyty weryfikacyjne (backend uvicorn lokalnie).

## TODO na Sesję 17
> Plan: krótki **close-out Fazy 2** → potem **START Fazy 3 (model Poissona)**.

1. **Close-out Fazy 2 (rozgrzewka, ~30-40 min):**
   - **Dark-polish komponentów**: tabela ligowa (`LeagueTable` — `bg-gray-100` w `<thead>`,
     `hover:bg-blue-50`), ewentualne inne jasne kolory/hovery → spójne z ciemnym motywem.
   - **Dług UX**: domyślny sezon = najnowszy z listy (`seasons[0]`) zamiast hardkodu
     `2026`/`2024` — wspólne dla `LeaguePage` i `BracketPage`.
2. **START Fazy 3 — model Poissona (serce projektu):**
   - Teoria krok po kroku: siła ataku/obrony z historycznych wyników → oczekiwane gole λ →
     rozkład Poissona → macierz prawdopodobieństw wyników → suma = P(1)/P(X)/P(2).
   - Szkielet `app/prediction/poisson.py` (czysty Python/numpy, **niezależny od API**).
3. (odłożone, wg ROADMAP) tabela fazy ligowej LM/LE/Konf; upiększacze drabinki;
   sprzątanie `index.css`/`App.css` (pozostałości szablonu).

## Praca domowa
> Sesja 17 zaczyna **Fazę 3 (predyktor Poissona)** — pierwszy raz statystyka/ML w projekcie.
> Główny nacisk: zrozumieć **ideę** modelu, zanim go zaimplementujemy.

### 🔴 Priorytet 1 — model Poissona (teoria pod Fazę 3)
1. **Rozkład Poissona — co to i po co** ·
   https://en.wikipedia.org/wiki/Poisson_distribution
   — skup się na intuicji: rozkład liczby zdarzeń w ustalonym czasie, gdy zdarzenia są
   rzadkie i niezależne, sterowany jednym parametrem **λ** (średnia liczba zdarzeń). Nie
   ucz się wyprowadzeń — zrozum, że dla danego λ dostajesz `P(0 goli), P(1), P(2)...`.
2. **Poisson w piłce (predykcja wyników)** · poszukaj „Poisson football prediction model"
   (np. blog dashee87 „Predicting Football Results With Statistical Modelling" albo
   dowolny tutorial). — zwróć uwagę na **łańcuch**: siła ataku i obrony drużyny (z
   historycznych goli, względem średniej ligowej) → **λ dla gospodarza i gościa** →
   dwa rozkłady Poissona → **macierz** P(wynik i:j) = P(home=i)·P(away=j) → zsumowanie
   pól macierzy w trójkąty daje P(wygrana gospodarza / remis / wygrana gościa).

### 🟢 Priorytet 2 — numpy (narzędzie do implementacji)
3. **numpy — absolutne podstawy** · https://numpy.org/doc/stable/user/absolute_beginners.html
   — tylko przejrzyj: czym jest `ndarray`, tworzenie tablic, operacje „wektorowe" (na całej
   tablicy naraz zamiast pętli), `np.outer` (iloczyn zewnętrzny — przyda się na macierz
   wyników). Bez wkuwania — implementację poprowadzę.

### 🟢 Priorytet 3 (lekko) — pod dark-polish
4. **Tailwind — tryb ciemny / spójność kolorów** · przejrzyj klasy szarości
   (`bg-gray-100…900`) w istniejących komponentach (`LeagueTable`, `MatchupCard`) i pomyśl,
   które jasne tła/hovery trzeba ściemnić, by pasowały do motywu. To rozgrzewka na start S17.
