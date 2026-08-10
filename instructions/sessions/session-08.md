# Sesja 8 — 10 sierpnia 2026

> Start frontendu: ekosystem JS, scaffold Vite (React + TypeScript), pierwszy własny
> komponent, CORS w FastAPI. Na koniec spłata długu z S6/7: filtr `knockout_only`
> w endpoincie `bracket`. (Kalendarzowo Sesja 8 = „Sesja 7 — Start frontendu" z ROADMAP.)

## Co zostało zrobione

### 1. Ekosystem JS + scaffold projektu (Kroki 1–2)
- Node.js **v20.20.2 (LTS)** już był w WSL przez `nvm` (praca domowa odrobiona), `npm` **10.8.2**.
- Fundament pojęciowy przez **analogię do Pythona**: `node`≈interpreter Pythona, `npm`≈`pip`,
  `package.json`≈`requirements.txt`, `node_modules/`≈`venv/`, `package-lock.json`≈`pip freeze`.
- `npm create vite@latest frontend -- --template react-ts` → świeży szablon **React 19 + TypeScript
  + Vite 8 + oxlint**. Potem `npm install` (27 paczek, 0 podatności).
- Tour po plikach: **przepływ startu SPA** (`index.html` z pustym `#root` → `main.tsx` montuje React
  → `App.tsx` rysuje UI), rola `vite.config.ts`, `tsconfig*.json`, `oxlint` (filozoficzny bliźniak Ruffa).

### 2. Dev-server + pierwszy komponent (Krok 3)
- `npm run dev -- --host` → dev-server Vite na `http://localhost:5173` (ready ~286 ms), **HMR** (hot reload).
  Dostęp z Windowsa przez przekierowanie `localhost` WSL2.
- **Pierwszy własny komponent — napisał właściciel** (Claude: spec + review): `LeagueCard`
  (props `{ name: string; country: string }`, typ `LeagueCardProps`, destrukturyzacja, JSX z `{}`),
  reużyty **5×** w `App` (Premier League/La Liga/Serie A/Bundesliga/Ligue 1) + `<h1>⚽ Football Predictor</h1>`,
  fragment `<>...</>`, `export default App`. Render zweryfikowany (5 kart), HMR bez błędów.
- Teoria Reacta: komponent = funkcja zwracająca JSX; props = argumenty (read-only, typowane);
  pułapki JSX (`className`, `{ }`, jeden korzeń/fragment, nazwy komponentów z wielkiej litery).

### 3. CORS w FastAPI (Krok 4)
- **Napisał właściciel** (Claude: spec z docs + review): `app.add_middleware(CORSMiddleware, ...)`
  w `app/main.py` — `allow_origins=["http://localhost:5173"]`, `allow_credentials=True`, metody/nagłówki `["*"]`.
  Jawny origin (nie `"*"` — nie łączy się z `allow_credentials=True`).
- **Weryfikacja curlem** (backend na :8000): preflight `OPTIONS` → 200 + `access-control-allow-*`;
  `GET /` z origin 5173 → nagłówek `access-control-allow-origin` obecny; `GET /` z `evil.com` → **200 ale BEZ**
  nagłówka zgody.
- Kluczowa lekcja: **CORS to ochrona po stronie przeglądarki, nie autoryzacja serwera.** `curl`/`httpx`/pytest
  CORS ignorują — dlatego backend i testy działały bez niego. Zadziała „na serio" dopiero, gdy frontend zawoła API (Sesja 9).

### 4. Dług z S6/7: filtr `knockout_only` w `bracket` (Krok 5)
- **Diagnostyka realnych rund** (skrypt jednorazowy na bazie dev): Liga Mistrzów = **17 rund**
  (kwalifikacje + League Stage 1–8 + faza pucharowa), FA Cup = **20 rund** (preliminary, kwalifikacje, replaye).
  `bracket` zwracał to wszystko → drabinki nie da się sensownie narysować.
- **Decyzja:** opt-in query param **`knockout_only: bool = False`** + kuratorowana stała **`KNOCKOUT_ROUNDS`**
  (`Round of 64/32/16`, `Quarter-finals`, `Semi-finals`, `Final`) w `app/constants.py`. Filtr w pętli budującej `result`.
- **Poprawka po review:** właściciel dał najpierw default `True` → zmienione na **`False`**
  (kompatybilność wsteczna, semantyka opt-in „filtr się włącza", pułapka pustej `[]` dla nie-pasujących rund).
- **2 testy** (napisał/przerobił właściciel): `test_get_bracket_all_stages` (default = wszystkie rundy
  + zachowany dowód sortowania po dacie), `test_get_bracket_with_knockout_only` (filtr zostawia tylko „Final").

## Decyzje (i dlaczego)
- **Frontend w WSL, nie w Windows** — spójne środowisko z resztą projektu (Python/Postgres też w WSL).
- **Szablon `react-ts`** (nie czysty JS) — typy pod kontrakty API i standard pod CV.
- **Origin CORS na sztywno w `main.py`** teraz — przeniesienie do `Settings`/`.env` przy deployu (stretch),
  dziś tylko dodałoby komplikacji.
- **`knockout_only` opt-in (default `False`)** — nie psuje istniejącego zachowania ani testów, uczy query paramów,
  bezpieczny default „pokaż wszystko"; zawężenie to świadoma decyzja wołającego (np. przyszły komponent `Bracket`).
- **Lekcja „zielony pasek ≠ poprawność":** pierwszy default `True` przeszedł 6/6 **przez przypadek** (stary test
  używał rund z whitelisty). Dlatego dopisaliśmy test z rundą **spoza** listy — dopiero on realnie pilnuje defaultu.

## Czego się nauczyliśmy (do utrwalenia)
- Ekosystem JS mapuje się **1:1 na Pythona** (node/npm/package.json/node_modules) — mniej magii, niż się wydaje.
- **SPA:** jedna strona HTML + React montuje się w pustym `#root`; przepływ `index.html` → `main.tsx` → `App.tsx`.
- **React:** komponent = funkcja → JSX; props typowane i read-only; jeden komponent, wiele użyć (reuse); pułapki JSX.
- **HMR:** zapis pliku → natychmiastowa aktualizacja UI bez pełnego przeładowania.
- **Dwa serwery, dwa porty → CORS.** Same-Origin Policy, preflight `OPTIONS`, `CORSMiddleware`; CORS chroni użytkownika w przeglądarce, nie jest kłódką na serwerze.
- **Test pinuje tylko to, co faktycznie sprawdza** — dobór danych testowych (runda spoza whitelisty) decyduje o wartości testu.
- Drobiazg operacyjny: `pkill -f "wzorzec"` potrafi dopasować **własną powłokę**, jeśli wzorzec jest w jej linii poleceń — bezpieczniej ubijać po porcie (`fuser -k PORT/tcp`).

## TODO na Sesję 9 (ROADMAP „Sesja 8 — Podstawy React + Tailwind + pierwsza tabela")
1. **React interaktywny:** `useState` (stan komponentu) i `useEffect` (efekt po zamontowaniu → pobranie danych).
2. **Pierwszy fetch z backendu:** komponent `LeagueTable` woła `GET /leagues/{id}/standings`; **typy TS**
   dla odpowiedzi (kształt `StandingResponse` z zagnieżdżoną drużyną). **Tu CORS zagra naprawdę.**
3. **Tailwind CSS:** instalacja (plugin Vite), filozofia utility-first; ostylowanie `LeagueCard`/`LeagueTable`.
4. **Porządek:** rozbicie komponentów na pliki (`src/components/LeagueCard.tsx`, `LeagueTable.tsx`) —
   konwencja „jeden komponent = jeden plik" + import/export.
5. *(opcjonalnie)* wspólny helper do fetchy / bazowy URL API (`frontend/src/api/`) — przygotowanie pod TanStack Query (Sesja 10).

## Stan repo po sesji
- Gałąź `main`. **Nowy katalog `frontend/`** (Vite React-TS; `node_modules` gitignored, ma własny `.gitignore`).
  Zmienione: `app/main.py` (+CORS), `app/routers/competitions.py` (+`knockout_only`),
  `app/constants.py` (+`KNOCKOUT_ROUNDS`), `tests/test_main.py` (2 testy bracket).
- **Backend:** `pytest` **7/7 zielone**; Ruff (`app/` + `tests/`) czysty i sformatowany.
- **Frontend:** `npm run dev` → `:5173` działa; komponent `LeagueCard` renderuje 5 kart.
- **API-Football: 0 zapytań** (diagnostyka rund z lokalnej bazy; frontend statyczny; CORS testowany curlem lokalnie).
- **Migracji nie przybyło** (zmiany w kodzie, nie w schemacie). Baza dev bez zmian.
- **Commit + push robi właściciel** (propozycja message + komend w czacie).

## Praca domowa
### 🔴 Priorytet 1 — przed Sesją 9
1. **React — State (`useState`)** · https://react.dev/learn/state-a-components-memory — kiedy komponent „pamięta"
   (to ten licznik z szablonu!); że `setState` powoduje **re-render**. Na co patrzeć: `const [x, setX] = useState(...)`.
2. **React — `useEffect`** · https://react.dev/reference/react/useEffect — efekty uboczne po renderze; **tablica
   zależności** `[]` (uruchom raz po zamontowaniu); sprzątanie. Na co patrzeć: typowy wzorzec „fetch w `useEffect`".
3. **Fetch API (async w JS)** · https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch —
   `fetch(url)`, `await res.json()`, obsługa błędów. Na co patrzeć: że `fetch` zwraca Promise (async).
4. **Tailwind + Vite** · https://tailwindcss.com/docs/installation/using-vite — instalacja pluginu, filozofia
   **utility-first** (klasy w JSX zamiast osobnego CSS). Na co patrzeć: jak podpiąć do naszego projektu Vite.

### 🟢 Priorytet 2 — bez terminu
5. **TypeScript — typy obiektów** · https://www.typescriptlang.org/docs/handbook/2/objects.html — pod typy
   odpowiedzi API (zamienimy `StandingResponse` z backendu na interfejs/typ TS po stronie frontendu).

**Metoda:** czytaj z otwartym repo. Przy `useState` pobaw się licznikiem z `App.tsx` (zmień, zapisz, patrz jak HMR
odświeża) — to najszybszy sposób, żeby „poczuć" stan. CORS zadziała „na serio", gdy `LeagueTable` faktycznie zawoła backend.
