# Sesja 17 — 12 września 2026

> **Close-out Fazy 2 → START Fazy 3 (model Poissona) — backend kompletny.**
> Rozgrzewka: dark-polish komponentów pod ciemny motyw, wspólny hook
> `useSeasonSelector` (domyślny sezon = najnowszy), empty states. Potem serce
> projektu: **cała teoria Poissona krok po kroku** + backend predyktora
> (`poisson.py` czysta matematyka + `strength.py` λ z danych + endpoint
> `GET /predict` + testy). Sesja bardzo długa i gęsta konceptowo (statystyka od
> zera). Zmiana celu na starcie Bloku B: **beta z predyktorem do 13 wrz**,
> deploy + CV po powrocie (~26 wrz).

## Decyzje na starcie (i dlaczego)
- **Nowy harmonogram (deadline właściciela)**: beta z prostym predyktorem Poissona
  **do 13 wrz** (backend dziś, UI jutro) → wyjazd → **od 26 wrz** deploy (publiczny
  link) + README + CV. Priorytet: **MVP na deploy PRZED Fazą 4/5** ("wystaw
  wcześnie, ulepszaj publicznie" — świeży, aktywny projekt wygląda lepiej na CV).
- **Wizja 3 modeli** (cel właściciela): #1 **bazowy** Poisson (standings) → #2
  **ulepszony** (Dixon-Coles: wagi czasowe = forma + korekta niskich wyników;
  fixtures dom/wyjazd) → #3 **ML** (forma, H2H...). Porównanie na końcu (Faza 5).
  Pomysły właściciela (forma, H2H) = cechy modelu #2/#3, **nie** bazy — najpierw
  baseline, potem mierzone ulepszenia.
- **Źródło λ = `standings`** (nie `fixtures`): diagnostyka bazy pokazała, że
  fixtures LIGOWE są tylko dla 2026 i jest ich mało (10–34 mecze/liga); standings
  mają **pełne** sezony 2022–2025 z GF/GA. Split dom/wyjazd (z fixtures) odłożony
  do modelu #2.
- **Predyktor WITHIN-LEAGUE** (nie cross-league): siła jest względna do ligi
  (atak 1,4 w La Lidze ≠ w Ligue 1), więc Barca vs PSG jest matematycznie
  niespójne. Beta = mecz w ramach jednej ligi. Cross-league (kalibracja siły lig
  z pucharów EU) → po CV.
- **`GET /predict`** (nie `POST` z ROADMAP): predykcja to czysty odczyt/obliczenie
  (nic nie zapisuje) → spójne z resztą API (same GET-y) + cache w TanStack Query.

## Co zostało zrobione

### Blok A — close-out Fazy 2
- **Dark-polish `LeagueTable`**: nagłówek `bg-gray-100`→`bg-gray-800`, hover
  `hover:bg-blue-50`→`hover:bg-gray-800`, ramki `border`→`border border-gray-700`.
  Lekcja: sztywne kolory klas Tailwinda NIE reagują na motyw — trzeba je podmieniać
  ręcznie, spójnie z paletą `MatchupCard`.
- **Hover `MatchupCard`** (wzorzec `group`): `group` na kontenerze + `group-hover:`
  na dzieciach z własnym kolorem + `transition-colors`. Na hover: tekst i ramka na
  biało, sumaryczny wynik (Σ) na żółto (`group-hover:text-yellow-400`). Kluczowe:
  bez `group` na rodzicu `group-hover:` na dzieciach jest martwe.
- **Domyślny sezon = najnowszy** — nowy hook **`useSeasonSelector`** (DRY: logika
  sezonu z `LeaguePage`+`BracketPage` w jednym miejscu). Wzorzec **derived state**:
  `selectedSeason ?? seasons?.[0]` (nie kopiować danych serwera do `useState` —
  trzymać tylko wybór usera, resztę obliczyć). Guard `season !== null`. Bug review:
  `useState<string|null>`→`number|null` (sezony to liczby; HTML `value` jest zawsze
  stringiem, ale my konwertujemy `Number(...)`).
- **Empty states**: `Bracket` ("No knockout stage for this season yet" gdy
  `data.length===0` — np. LM 2026 w fazie ligowej, brak knockoutu) + `SearchPage`
  ("Unknown team" gdy `teams?.length===0`). Lekcja: **`!data`** (undefined) vs
  **`data.length===0`** (pusta tablica jest truthy! `![]===false`).

### Blok B — Faza 3 backend (model Poissona)
- **Teoria krok po kroku**: rozkład Poissona + parametr λ (średnia → P(0),P(1)...);
  siła ataku/obrony **względem bazy ligowej**; `λ = baza × atak × obrona`; dwa
  rozkłady → **macierz** (`np.outer`) → **trójkąty** → `P(1)/P(X)/P(2)`. Baza jest
  konieczna: uwzględnia RYWALA (sama średnia drużyny go ignoruje) i utrzymuje skalę.
- **numpy 2.2.6** zainstalowane (`requirements.txt` zaktualizowany). Nowy pakiet
  `app/prediction/`.
- **`app/prediction/poisson.py`** (5 funkcji, czysta matematyka, niezależna od API):
  `poisson_pmf` (wzór `λ^k·e^-λ/k!`), `goal_distribution` (wektor), `score_matrix`
  (`np.outer` + **normalizacja** `matrix/matrix.sum()` — obcięcie ogona na
  `max_goals`), `match_outcome_probabilities` (`np.tril(-1)`/`trace`/`triu(1)`),
  `top_scorelines`. Weryfikacja: λ 1,96/0,95 → **61/21/18** (zgodne z teorią).
- **`app/prediction/strength.py`** (3 funkcje, λ z danych): `league_baseline`
  (`sum(GF)/sum(played)`, `func.sum`/`.scalar()`), `team_attack_defence`
  (`(GF/played)/baza` itd.), `match_lambdas` (składa + `HOME_ADVANTAGE=1,3` z
  `constants.py`). Weryfikacja: Barcelona atak **1,86**/obrona **0,70**, Oviedo
  0,51/1,17; baza PL **1,375**/Bundesliga **1,618** (golowa — realizm z danych).
- **Endpoint `GET /predict`** (`routers/predictions.py` + rejestracja w `main.py`):
  `home_id/away_id/league_id/season` → walidacja **404** (obie drużyny muszą mieć
  standing) → `match_lambdas` → `score_matrix` → `match_outcome_probabilities` +
  `top_scorelines` → `PredictionResponse` (**`float()` fix** na `np.float64` pod
  JSON). Schematy `PredictionResponse`/`ScoreLine`. Weryfikacja: Barca vs Oviedo
  **92,7/5,3/1,8%**, top wynik 3:0.
- **Testy**: `tests/test_poisson.py` (5, czysta matematyka, known-values) + 2 w
  `test_main.py` (`/predict` 200 + suma 1/X/2 ≈ 1 + 404). **pytest 12 → 19**. Test
  **złapał realny problem**: przy wysokim λ suma wychodziła 0,999 (obcięcie ogona)
  → naprawa **normalizacją macierzy** (1/X/2 sumują do 100%, ważne dla pasków UI).

## Czego się nauczyliśmy
- **Poisson**: λ (średnia) → cały rozkład P(k); kształt (szczyt, ogon); gole ≈
  zdarzenia rzadkie/niezależne. Wzór `λ^k·e^-λ/k!`.
- **Model siły**: baza (średnia ligi) = punkt odniesienia; siła = `gole/baza`
  (bezwymiarowy współczynnik, 1,0 = przeciętny, porównywalny); `λ=baza×atak×obrona`
  (mnożniki względem przeciętnej; baza utrzymuje jednostki [gole/mecz]). Sama
  średnia drużyny **ignoruje rywala** — baza to naprawia.
- **Within-league**: siła względna do ligi → cross-league niespójne bez kalibracji.
- **numpy**: `ndarray`, `np.outer` (macierz), `np.tril/triu(k=±1)/trace` (trójkąty;
  `k` wyklucza przekątną, żeby nie liczyć remisów podwójnie); normalizacja po obcięciu.
- **SQLAlchemy**: `func.sum` (agregacja SQL) + `.scalar()` (jedna wartość) vs
  `.all()` (lista krotek `[(x,)]`) vs `.one()`; `.first()` (obiekt lub None).
- **Python**: `list` (klasa) vs `[]`/`list()` (instancja → `list.append(x)` na
  klasie = TypeError); shadowing (zmienna o nazwie funkcji); `pow` vs `math.exp`;
  nazwy zmiennych `snake_case` (PEP8, nie `P`).
- **React**: derived state (`?? seasons[0]`) zamiast kopiowania stanu serwera;
  `!data` vs `.length===0` (pusta tablica truthy); `group`/`group-hover:` +
  `transition-colors`.
- **Testy**: known-value unit testy; test złapał realny problem (obcięcie →
  normalizacja) — dowód wartości testów.
- **Architektura**: separacja `poisson.py` (czysta matematyka, bez DB) ↔
  `strength.py` (DB→λ) ↔ endpoint (API); `GET` dla odczytu/obliczenia.

## Stan repo po sesji
- **Faza 2 — DOMKNIĘTA** (dark-polish + `useSeasonSelector` + empty states).
- **Faza 3 backend — KOMPLETNY** (model Poissona + endpoint + testy).
  - `app/prediction/` — **NOWY** pakiet: `poisson.py`, `strength.py`, `__init__.py`
  - `app/routers/predictions.py` — **NOWY** (`GET /predict`)
  - `app/schemas.py` — +`PredictionResponse`, +`ScoreLine`
  - `app/constants.py` — +`HOME_ADVANTAGE = 1.3`
  - `app/main.py` — rejestracja routera `predictions`
  - `frontend/src/hooks/useSeasonSelector.ts` — **NOWY**
  - `frontend/src/pages/LeaguePage.tsx`, `BracketPage.tsx` — używają hooka
  - `frontend/src/components/LeagueTable.tsx`, `MatchupCard.tsx`, `Bracket.tsx`,
    `pages/SearchPage.tsx` — dark-polish / empty states
  - `tests/test_poisson.py` — **NOWY** (5 testów); `tests/test_main.py` — +2 testy
  - `requirements.txt` — +`numpy==2.2.6`
- **Baza**: bez zmian (leagues 15, teams 1962, standings 572, fixtures 7980).
- **Jakość**: pytest **19/19**, Ruff czysty; frontend `tsc` + oxlint **0/0**.
  API-Football: **0 zapytań** (tylko odczyty z lokalnej bazy).

## TODO na Sesję 18 (sprint — do 13 wrz wieczór)
> Cel: **działający predyktor na stronie** (lokalnie). Backend gotowy — zostaje UI.
1. **UI predyktora**:
   - warstwa API `frontend/src/api/predictions.ts` (`getPrediction(home, away, league, season)`),
   - wybór **ligi → dwie drużyny z tej ligi** (within-league; drużyny z `getStandings`),
   - komponent/strona: **paski 1/X/2** + lista **top wyników**,
   - trasa `/predict` + wejście z HomePage.
2. Weryfikacja end-to-end na żywo (backend uvicorn + front).

## Po powrocie (od 26 wrz)
- **Deploy**: backend + PostgreSQL (Railway/Render) + frontend (Vercel) → link.
- **README pro**: opis, screenshoty, stack, link do dema, „within-league v1;
  cross-league + ML planned".
- Potem: Faza 4 (symulator Monte Carlo), Faza 5 (ML) — modele #2/#3 + porównanie.

## Praca domowa
> Sesja 18 to frontend predyktora (znane wzorce Reacta) — mało nowej teorii,
> głównie praktyka. Przejrzyj też materiały pod deploy (przyda się od 26 wrz).

### 🔴 Priorytet 1 — pod UI predyktora
1. Przypomnij **`useQuery` z parametrami** + **kontrolowane `<select>`** (mamy w
   `LeaguePage`/`SearchPage`) — UI predyktora to zasadniczo dwa selecty drużyn +
   wywołanie `/predict` + wyświetlenie wyniku.
2. **Paski procentowe w CSS/Tailwind** — pomyśl, jak pokazać 1/X/2: proste `div`-y
   z szerokością ustawioną na `%` (inline style `width` albo klasy). To będzie
   wizualizacja wyniku predykcji.

### 🟢 Priorytet 2 — pod deploy (po powrocie)
3. **Railway** lub **Render** — jak wdraża się FastAPI **z PostgreSQL**: zmienne
   środowiskowe (`DATABASE_URL`, `API_FOOTBALL_KEY`), migracje Alembic na
   produkcji, port z `$PORT`.
4. **Vercel** — jak zbudować i wystawić aplikację Vite/React oraz jak ustawić
   `VITE_API_URL` na produkcyjny adres backendu (CORS na backendzie trzeba będzie
   rozszerzyć o domenę Vercela).
