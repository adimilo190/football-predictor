# Sesja 18 — 13 września 2026

> **Sprint: UI predyktora (Faza 3 frontend) — KOMPLETNY.** Cała ścieżka
> front→backend: warstwa API → strona + routing → wybór ligi → wybór 2 drużyn
> → wywołanie `GET /predict` → wizualizacja (paski 1/X/2 + najbardziej
> prawdopodobne wyniki). Sesja gęsta konceptualnie mimo znanych wzorców Reacta:
> dużo dyskusji projektowych (path vs query param, konwencje nazewnictwa
> Python↔TS, jakość danych a wybór sezonu). Kamień milowy „UI predictora"
> osiągnięty — **beta z predyktorem działa lokalnie**.

## Decyzje (i dlaczego)
- **Klucze query w URL = snake_case (jak backend), zmienne JS = camelCase.**
  Rozdzieliliśmy „nazwę pojęcia" (spójna po obu stronach) od „stylu zapisu"
  (konwencja języka). Klucz w URL (`?home_id=`) MUSI pasować do backendu, bo
  fizycznie jedzie w URL; nazwa zmiennej JS (`homeId`) jest lokalna i podlega
  konwencji TS. Audyt wszystkich `api/*.ts` — tylko `predictions.ts` miał bug
  (naprawiony); `bracket.ts` był wzorcowy (`knockoutOnly` → `knockout_only`).
- **Sezon predykcji = stała `PREDICTION_SEASON = 2025` (ostatni pełny sezon).**
  Właściciel słusznie zauważył, że bieżący sezon we wrześniu ma ~5 kolejek →
  mała próbka → zaszumione siły drużyn → słaba predykcja. Ostatni zakończony
  sezon (~38 kolejek) = stabilne liczby, zero zmian w backendzie. **Bez
  selektora sezonu** — user wybiera tylko ligę + 2 drużyny.
- **Uśrednianie danych z wielu sezonów = feature modelu #2 (Dixon-Coles), nie
  baseline.** Pomysł właściciela (średnia ważona z ostatniego + bieżącego
  sezonu) jest trafny — to dokładnie wagi czasowe modelu #2. Trzymamy się
  zasady „baseline first, potem MIERZONE ulepszenia" (bez baseline nie wiadomo,
  czy ulepszenie pomogło). Dopisane do ROADMAP jako zadanie modelu #2.
- **Predyktor within-league** — drużyny wyłącznie z 6 lig krajowych (`COUNTRIES`,
  bo tylko ligi mają `standings`, których model potrzebuje). Puchary odpadają.

## Co zostało zrobione (kroki sprintu)
1. **Warstwa API `frontend/src/api/predictions.ts`** (napisał właściciel): typy
   `ScoreLine`/`Prediction` (lustro `PredictionResponse` z backendu) +
   `getPrediction(homeId, awayId, leagueId, season)`. Review złapał **realny
   bug**: klucze query w URL były camelCase (`homeId`) — backend oczekuje
   `home_id` → byłoby 422. Poprawione na snake_case; `getPredictions` →
   `getPrediction` (l. poj., zwraca jeden obiekt).
2. **Szkielet strony + routing**: `pages/PredictPage.tsx` (nowy), trasa
   `/predict` w `App.tsx`, link „🔮 Predict match" na `HomePage` (klasy reuse
   z „Find team").
3. **Wybór ligi**: `leagues = COUNTRIES.map(c => c.league)` (moduł-level, reuse
   danych z HomePage), `useState<number|null>` + kontrolowany `<select>` z
   placeholderem (wzorzec z `LeaguePage`).
4. **Wybór 2 drużyn**: `useQuery(["standings", leagueId, PREDICTION_SEASON])` z
   **`enabled: leagueId !== null`** (reuse `getStandings`), `teams =
   standings?.map(s => s.team) ?? []`, dwa selekty „Home vs Away". Reset
   `homeId`/`awayId` przy zmianie ligi (stan zależny nie pasuje do nowej ligi).
5. **Wywołanie `/predict`**: `useQuery(["prediction", ...])` z **`enabled:
   homeId!==null && awayId!==null && homeId!==awayId`** (blokada „drużyna nie
   gra sama ze sobą"), `!` non-null assertion w `queryFn`, `isLoading`/`isError`,
   komunikat „Pick two different teams". Wynik na początku surowy (dowód
   wiringu).
6. **Wizualizacja — `components/PredictionResult.tsx`** (nowy): 3 paski 1/X/2 +
   lista top wyników. Wewnętrzny `OutcomeBar` (DRY — jeden pasek × 3 z propsami
   `label`/`probability`/`color`); tor `bg-gray-700` + wypełnienie o szerokości
   `%` przez **inline style** (dynamiczna wartość); kolory pod ciemny motyw
   (emerald/amber/sky, paleta z `MatchupCard`); nazwy drużyn na etykietach
   (`teams.find` w `PredictPage` → propsy). Separacja: `PredictPage` = stan/dane,
   `PredictionResult` = tylko prezentacja.
7. **Weryfikacja end-to-end**: właściciel odpalił lokalnie — działa, wygląda
   dobrze. `npm run lint` (oxlint) **0/0**, `npx tsc -b` czysty.

## Czego się nauczyliśmy
- **Path param vs query param**: nazwa musi pasować do backendu tylko wtedy, gdy
  jedzie w URL jako klucz (query, `?season=`). Path param (`/leagues/{id}/...`)
  przekazuje samą wartość po pozycji — nazwa zmiennej JS jest wtedy dowolna.
- **Konwencje nazewnictwa**: to samo pojęcie, ale styl per język — Python
  `snake_case`, TS `camelCase` (zmienne/funkcje) / `PascalCase` (typy,
  komponenty) / `UPPER_SNAKE_CASE` (stałe modułu). Dlaczego camelCase: tak
  wygląda język (`getElementById`) i ekosystem (React/TanStack), lintery tego
  pilnują. **PascalCase dla komponentów to wymóg JSX** (`<predictPage/>` = tag
  HTML, `<PredictPage/>` = komponent).
- **React**: kontrolowany `<select>` (`value`+`onChange`+`Number(...)`);
  **`enabled` w `useQuery`** (zapytanie zależne — nie strzela z `null`); reset
  stanu zależnego przy zmianie nadrzędnego; **non-null assertion `!`** (gwarancja
  z `enabled`); komponent + propsy; wyodrębnienie wewnętrznego komponentu dla DRY
  (`OutcomeBar`).
- **Tailwind**: dynamiczna szerokość paska przez **inline `style`**, nie klasę
  (klasy są stałe); przekazuj **pełne literały klas** (`"bg-emerald-500"`) —
  Tailwind skanuje kod po tekście, `bg-${x}-500` NIE zadziała.
- **Model/dane**: siła drużyny liczona z **tabeli konkretnego sezonu** — nie ma
  „ogólnej" siły; mała próbka (bieżący sezon) → zaszumione statystyki; stąd
  baseline na ostatnim pełnym sezonie. Baseline first, potem mierzone ulepszenia.
- **WSL**: lint/`tsc` trzeba odpalać z jawnie załadowanym nvm
  (`. $NVM_DIR/nvm.sh`) — domyślna powłoka bierze systemowego, starego Node
  (v12, wywala się na `??`/`?.`).

## Stan repo po sesji
- **Faza 3 — KOMPLETNA (backend z S17 + UI z S18)**. Predyktor działa
  end-to-end lokalnie.
  - `frontend/src/api/predictions.ts` — **NOWY** (typy + `getPrediction`)
  - `frontend/src/pages/PredictPage.tsx` — **NOWY** (wybór ligi + 2 drużyn)
  - `frontend/src/components/PredictionResult.tsx` — **NOWY** (paski + top wyniki)
  - `frontend/src/App.tsx` — +trasa `/predict`
  - `frontend/src/pages/HomePage.tsx` — +link „Predict match"
- **Backend**: bez zmian. **Baza**: bez zmian (leagues 15, teams 1962,
  standings 572, fixtures 7980).
- **Jakość**: frontend oxlint **0/0**, `tsc` czysty; backend pytest **19/19**
  (nietknięty), Ruff czysty. API-Football: **0 zapytań** (same odczyty z bazy).

## Długi techniczne (do sprzątnięcia)
- **`TeamSelect`** — dwa selekty drużyn to duplikacja; do wyodrębnienia w komponent.
- **`index.css`/`App.css`** — pozostałości szablonu Vite (globalne `h1/h2`
  bijące utilki; nieużywany `App.css`) — dług z S16/17.
- **Loading state drużyn** — świadomie pominięty (dane z lokalnej bazy błyskawiczne).
- **Uśrednianie sezonów** — feature modelu #2 (Dixon-Coles), nie baseline.

## TODO na Sesję 19 (po powrocie, ~26 wrz) — priorytet: DEPLOY + CV
> Zgodnie z harmonogramem z S17: beta gotowa (dziś), teraz publiczny link + CV
> PRZED Fazą 4/5. Kolejność: najpierw postawić apkę w sieci, potem README.
1. **Deploy backendu + PostgreSQL** (Railway lub Render): zmienne środowiskowe
   (`DATABASE_URL`, `API_FOOTBALL_KEY`), migracje Alembic na produkcji, port z
   `$PORT`. Import danych na produkcyjną bazę.
2. **Deploy frontendu** (Vercel): build Vite, `VITE_API_URL` na produkcyjny
   backend, **rozszerzyć CORS** w backendzie o domenę Vercela.
3. **README pro** (pod CV): opis, screenshoty, stack, link do dema, nota
   „within-league v1; blending sezonów + cross-league + ML planned".
4. (opcjonalnie, jeśli czas przed deployem) drobne długi: `TeamSelect`,
   sprzątnięcie `index.css`/`App.css`.

## Po powrocie / dalej
- Po deployu: **Faza 4** (symulator Monte Carlo), **Faza 5** (ML) — model #2
  (Dixon-Coles: wagi czasowe = uśrednianie sezonów + korekta niskich wyników)
  i #3 (ML), na końcu porównanie modeli.

## Praca domowa
> Sesja 19 to deploy — najwięcej NOWEGO tu, bo dotąd wszystko chodziło lokalnie.
> Przejrzyj, zanim usiądziemy (materiały powiązane z TODO powyżej).

### 🔴 Priorytet 1 — deploy backendu z bazą
1. **Railway** (lub Render) — jak wdrożyć FastAPI: podpięcie repo, `Procfile`/
   start command (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`), zmienne
   środowiskowe w panelu. Zwróć uwagę: skąd wziąć produkcyjny `DATABASE_URL`
   (managed PostgreSQL od hostingu) i jak odpalić **migracje Alembic** na starcie
   (release command / `alembic upgrade head`).
2. **PostgreSQL na produkcji** — czym różni się od lokalnej bazy w WSL: connection
   string, SSL, że dane trzeba **zaimportować od nowa** (nasze `POST /import-*`).

### 🟢 Priorytet 2 — deploy frontendu
3. **Vercel** — jak wystawić apkę Vite/React: import repo, build command
   (`npm run build`), katalog `dist`, ustawienie `VITE_API_URL` na adres backendu.
   Zwróć uwagę, że po deployu frontu trzeba **dodać jego domenę do CORS**
   backendu (inaczej przeglądarka zablokuje zapytania — pamiętasz CORS z S8).
