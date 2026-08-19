# Sesja 12 — 19 sierpnia 2026

> **Drabinki pucharowe (UI) + drzewko turniejowe + nawigacja przez kraje.**
> Backend: doimport Ligi Europy i Konferencji (+ naprawa latentnego buga importu).
> Frontend: cała ścieżka drabinki (warstwa API → `useQuery` → komponent → strona),
> przebudowa na **drzewko turniejowe** (schodki, dwumecze, agregaty) i **accordion**
> krajów na HomePage. Faza 1 klika się teraz od HomePage do każdej tabeli i drabinki.
> (Kalendarzowo Sesja 12 = „Sesja 11 — Drabinki" z ROADMAP + zaczątek szlifów Fazy 1.)

## Co zostało zrobione

### 1. Backend — doimport Ligi Europy (3) i Konferencji (848)
- **`constants.py`**: dodane 2 id do `EUROPEAN_COMPETITION_IDS`. Dzięki operatorowi `**`
  (merge słowników w `TARGET_LEAGUE_IDS` i w `import-fixtures`) zmiana rozprowadziła się
  „wszędzie" z **jednego miejsca** — potwierdzenie wartości single-source-of-truth.
- **Import**: `POST /import-leagues` (1 zapytanie → +2 rozgrywki) + `POST /import-fixtures`.
  Wynik: **13 → 15 rozgrywek**, **+678 meczów** (LE 269 / Konf 409), **+137 drużyn**.

### 2. Backend — naprawa latentnego buga w `import-fixtures`
- **Objaw**: `IntegrityError: duplicate key ... teams_pkey` (Pafos, id 3403) przy pierwszym
  imporcie z nowymi rozgrywkami.
- **Przyczyna**: `seen_team_ids` (strażnik przed podwójnym `db.add` drużyny) miał zasięg
  **per rozgrywka**. Przy `autoflush=False` drużyna dodana, ale niezcommitowana, jest
  **niewidoczna** dla kolejnego `db.query`. Klub grający w kilku europejskich pucharach
  (spadek z LM do LE do Konf) był dodawany 2× → duplikat klucza głównego przy `commit`.
- **Dlaczego nie wybuchło wcześniej**: dotąd drużyny współdzielone między rozgrywkami były
  klubami z 6 lig krajowych — a te są **już w bazie** ze standings, więc `upsert_team` je
  **znajdował** (UPDATE, nie INSERT). Nowe europejskie kluby spoza tych lig obnażyły ukryte,
  błędne założenie.
- **Poprawka**: `seen_team_ids` przeniesiony o poziom wyżej — **jeden zbiór na cały import**,
  wstrzykiwany do `upsert_fixtures` jako parametr. Zachowana `autoflush=False` i transakcja
  „wszystko albo nic". Testy 7/7, Ruff czysty.

### 3. Frontend — ścieżka drabinki (bliźniak wzorca ze standings)
- **`api/bracket.ts`**: typy `Fixture`/`BracketRound` (lustro `schemas.py`) + `getBracket`
  (`fetch` + `throw` przy `!res.ok`) + parametr `knockout_only=true` (query string).
- **`components/Bracket.tsx`**: `useQuery({ queryKey: ["bracket", leagueId] })` + 3 guardy
  (`isLoading`/`isError`/`!data`) — ten sam mechanizm co `LeagueTable`.
- **`pages/BracketPage.tsx`** + trasa `/bracket/:id` w `App.tsx` (`useParams` → `<Bracket>`).

### 4. Frontend — przebudowa na drzewko turniejowe
- **Layout schodkowy** (`Bracket.tsx`): kolumny rund w `flex` + **`items-stretch`** (równe
  wysokości) + wewnętrzny `flex-col justify-around flex-1` → każda runda **wyśrodkowana** co
  do piksela względem par z poprzedniej. Efekt drzewka **bez rysowania linii**. `overflow-x-auto`.
- **Grupowanie dwumeczów** (`groupIntoMatchups` w `bracket.ts`): mecze łączone po **nieuporząd-
  kowanej parze drużyn** (leg u siebie i rewanż trafiają razem); gole mapowane na stałe drużyny
  mimo zamiany home/away. Struktura 16→8→4→2→1 domyka się czysto.
- **`components/MatchupCard.tsx`**: karta pary z herbami + wynikami legów w pudełkach; dla
  **dwumeczów** dochodzą nagłówki `1 / 2 / Σ` i **wynik zsumowany** (agregat) w wyróżnionym
  pudełku. Pojedynczy mecz → minimalizm (bez nagłówków/agregatu). Odporne na **mieszane** rundy
  (Copa del Rey: single + dwumecz w jednej drabince — zweryfikowane na żywo).
- **Zwężenie**: `min-w-52 → min-w-40`, `gap-4 → gap-2`, mniejsze pudełka → szerokość
  1152px → **910px** (mieści się bez przewijania na typowym ekranie).

### 5. Frontend — nawigacja przez kraje (accordion)
- **`data/leagues.ts`**: nowy model `COUNTRIES` (kraj → `league` + `cup`) + `EUROPEAN_COMPETITIONS`.
  Stare `League`/`LEAGUES` usunięte.
- **`pages/HomePage.tsx`**: 7 rozwijanych sekcji przez natywny **`<details>`/`<summary>`**
  (zero `useState`): 6 krajów (liga → `/leagues/:id`, puchar → `/bracket/:id`) + „European
  Competitions" (LM/LE/Konf → `/bracket/:id`). `LeagueCard.tsx` usunięty (martwy kod).

## Decyzje (i dlaczego)
- **Drabinki „na sucho" najpierw** (trasa + strona), nawigacja później — mały krok, szybki
  efekt; i tak domknęliśmy nawigację w tej samej sesji.
- **`knockout_only=true`** dla drabinki — jednym ruchem wycina kwalifikacje **i** fazę ligową,
  zostawiając czystą fazę pucharową. Zero nowej logiki (filtr istniał w backendzie).
- **Nazwa `BracketPage`, nie `CupPage`** (pomysł właściciela) — nazwa od **widoku**, nie od
  domeny: część „pucharów" (LM/LE/Konf) ma fazę ligową, więc „Cup" zaszywałoby błędne założenie.
- **Dwumecze: wariant „oba wyniki" + agregat**, bez rozstrzygania awansu (remis w dwumeczu =
  bramki wyjazdowe/karne — danych nie mamy czysto).
- **Tabela fazy ligowej (LM/LE/Konf) ODŁOŻONA** — wymaga policzenia tabeli z meczów (nowy
  endpoint) lub importu standings; osobny, większy kawałek (→ Sesja 13).
- **`<details>` zamiast `useState`** — natywny accordion, zero stanu, dostępny z klawiatury.

## Czego się nauczyliśmy (do utrwalenia)
- **Latentny bug**: „działa" ≠ „poprawne". Kod przechodził 6 sesji dzięki szczęśliwym danym;
  nowe dane obnażyły ukryte założenie. `autoflush=False` + zasięg zmiennej + `db.query` nie widzi
  obiektów `pending`.
- **Komponent Reacta nie jest `async`**: `getBracket` **czeka** (async), komponent tylko
  **rysuje bieżący stan** i musi oddać JSX od ręki; `useQuery` przerysowuje go po nadejściu danych.
- **Drzewko w CSS**: `items-stretch` (równe wysokości) + `justify-around` = schodkowe
  wyśrodkowanie **bez linii**. `overflow-x-auto` + `shrink-0`/`min-w` do przewijania.
- **Flexbox — skąd się uczyć**: Flexbox Froggy (gra), CSS-Tricks „Complete Guide to Flexbox"
  (cheatsheet), docs Tailwind (klasa → CSS), DevTools na własnej apce. Tailwind = skróty na CSS 1:1.
- **Grupowanie danych**: klucz z **posortowanej** pary id (nieuporządkowany), mapowanie pól do
  stałych obiektów mimo zamiany ról (home/away).
- **`?? "-"` a nie `|| "-"`**: `0` jest „falsy", ale to prawidłowy wynik — `??` reaguje tylko na
  `null`/`undefined`.
- **`key` w liście**: element **bezpośrednio** w `.map` dostaje `key`; wrapper zostaje **na
  zewnątrz** `.map`. Brak `key` = **warning** (nie error) — strona działa, ale React ostrzega.
- **error vs warning**: error = nie kompiluje/wywala; warning = działa, ale „dałoby się czyściej".
- **Query param w `fetch`**: `?knockout_only=${...}` — `bool` w URL staje się tekstem, FastAPI
  parsuje z powrotem.
- **Środowisko (WSL)**: `npm run dev` wymaga **jawnego** załadowania nvm
  (`. ~/.nvm/nvm.sh && nvm use default`) — `bash -l` NIE aktywuje nvm, a systemowy `node` to
  stary **v12**, który wywala Vite (`SyntaxError` na `?.`).

## TODO na Sesję 13 (decyzja kierunku na starcie)
Faza 1 (UI tabel + drabinek + nawigacja) domknięta. Do wyboru na start:
1. **Tabela fazy ligowej** (LM/LE/Konf) — dokończenie pomysłu właściciela: backend liczy tabelę
   z meczów fazy ligowej (agregacja: punkty, bramki, sort) **lub** import standings; front pokazuje
   ją zamiast/obok drabinki dla rozgrywek z fazą ligową.
2. **Szlify Fazy 1** — responsywność (mobile), loading skeletons, dopracowanie stanów pustych/błędów.
3. **Upiększacze drabinki** — linie łączące pary; rozszerzenie `KNOCKOUT_ROUNDS` o rundy pucharów
   krajowych (żeby FA Cup pokazywał więcej niż QF→Final).
Rekomendacja: **1** (najciekawsza technicznie i domyka pomysł), potem **2** przy okazji.

## Stan repo po sesji
- **Backend — zmienione**: `app/constants.py` (+2 europejskie), `app/routers/imports.py`
  (współdzielony `seen_team_ids`). Baza: 15 rozgrywek, +678 fixtures, +137 teams.
- **Frontend — nowe**: `api/bracket.ts`, `components/Bracket.tsx`, `components/MatchupCard.tsx`,
  `pages/BracketPage.tsx`.
- **Frontend — zmienione**: `App.tsx` (trasa `/bracket/:id`), `data/leagues.ts` (model `COUNTRIES`
  + europejskie, usunięte `LEAGUES`), `pages/HomePage.tsx` (accordion).
- **Frontend — usunięte**: `components/LeagueCard.tsx`, `components/MatchCard.tsx` (przejściowy).
- **Jakość**: `npm run build` zielony, `npm run lint` (oxlint) **0/0**, format czysty; pytest **7/7**,
  Ruff czysty.
- **Zapytania do API-Football**: ~19 (1 import-leagues + 9 import-fixtures ×2 przez bug/retry).

## Praca domowa
> Metoda: czytaj z otwartym repo. Zobacz, jak drabinka (S12) 1:1 powtórzyła wzorzec ze standings.

### 🔴 Priorytet 1 — pod tabelę fazy ligowej (jeśli wybierzemy kierunek 1)
1. **SQLAlchemy — agregacje (`func`, `group_by`)** ·
   https://docs.sqlalchemy.org/en/20/orm/queryguide/columns.html#aggregate-functions
   — bo tabelę fazy ligowej policzymy **z meczów** (suma punktów/bramek per drużyna). Zwróć uwagę
   na `func.sum`, `func.count` i `group_by`.
2. **Reguły punktacji ligowej** (przypomnienie): zwycięstwo = 3 pkt, remis = 1, porażka = 0;
   sortowanie: punkty → różnica bramek → bramki zdobyte. Przemyśl, jak policzyć to z listy meczów
   (gospodarz/gość, gole) — to fundament pod predyktor i symulator (Fazy 3–4).

### 🟢 Priorytet 2 — pod szlify Fazy 1 (kierunek 2)
3. **Tailwind — responsywność (breakpoints)** · https://tailwindcss.com/docs/responsive-design
   — mobile-first, prefiksy `sm:`/`md:`/`lg:`. Na co patrzeć: jak zwęzić drabinkę i accordion na
   telefonie.
4. **Wzorzec „loading skeleton"** — zamiast „Loading…" pokazać szary szkielet układu. Pomyśl, jak
   to wpiąć w stan `isLoading` z `useQuery`.
