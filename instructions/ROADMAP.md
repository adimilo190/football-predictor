# ROADMAP — Football Predictor & Tracker

> Plan pracy od 2 lipca do 30 września 2026. Zakłada **2 sesje tygodniowo** (każda 2–4h).
> Statusy: `[ ]` do zrobienia · `[~]` w trakcie · `[x]` zrobione.
> Po każdej sesji aktualizujemy statusy tutaj + piszemy log w `instructions/sessions/`.

---

## Kamienie milowe

| Termin  | Kamień milowy                                              | Status |
|---------|------------------------------------------------------------|--------|
| 6 lip   | Repo na GitHubie, sekrety w `.env`, backend uporządkowany  | [x]    |
| 20 lip  | **Faza 1 backend**: tabele lig + puchary w bazie i API     | [x]    |
| 10 sie  | **Faza 1 komplet**: UI tabel i drabinek działa             | [x]    |
| 24 sie  | **Faza 2 komplet**: ulubione drużyny + dashboard           | [ ]    |
| 7 wrz   | **Faza 3 komplet**: predictor (model Poissona)             | [ ]    |
| 14 wrz  | **Faza 4 komplet**: symulator meczów i lig                 | [ ]    |
| 28 wrz  | **Faza 5 komplet**: model ML + porównanie z Poissonem      | [ ]    |
| 30 wrz  | README, CI, szlify — **projekt gotowy do CV**              | [ ]    |

---

## BLOK 0 — Fundamenty i porządki (tydzień 1: 2–6 lip)

### Sesja 1 — 2 lip [x] Audyt, bezpieczeństwo, plan, GitHub
- [x] Analiza projektu i ocena stacku
- [x] Sekrety (klucz API, hasło DB) przeniesione do `.env` + `.env.example`
- [x] `.gitignore` (venv, `__pycache__`, `.env`, node_modules)
- [x] `requirements.txt` (zamrożenie wersji paczek)
- [x] ROADMAP + system logów sesji + `CLAUDE.md`
- [x] Pierwszy commit na gałęzi `main`
- [x] **Zadanie domowe:** założyć repo `football-predictor` na GitHubie i wykonać push (komendy w `sessions/session-01.md`)

**Czego się uczysz:** git (staging, commit, branch, remote, push), po co jest `.env` i `.gitignore`, czym jest `requirements.txt`.

### Sesja 2 — 5 lip [x] Struktura backendu jak w prawdziwym projekcie
- [x] Restrukturyzacja: pojedynczy `main.py` → pakiet `app/` (`app/main.py`, `app/database.py`, `app/models.py`, `app/schemas.py`, `app/config.py`) — `app/routers/` odłożone, aż endpointów przybędzie
- [x] `pydantic-settings` — konfiguracja z `.env` w jednym miejscu (klasa `Settings`)
- [x] Schematy Pydantic (`response_model`) — kontrola tego, co API zwraca (`LeagueResponse` na `/my-leagues`)
- [x] Tour po Swagger UI (`/docs`) — dlaczego FastAPI generuje dokumentację za darmo
- [x] Ruff — linter/formatter Pythona + pierwsze uruchomienie (kod czysty; komentarze przełączone na angielski)

**Czego się uczysz:** jak organizuje się produkcyjny projekt FastAPI, czym jest Pydantic i walidacja danych, czym jest REST, lintowanie kodu.

---

## BLOK 1 — Faza 1 backend: dane lig i pucharów (tygodnie 2–3: 7–20 lip)

### Sesja 3 — 8 lip [x] Modele danych + migracje Alembic + docelowe rozgrywki
- [x] **KLUCZOWE:** test darmowego planu API-Football — rozstrzygnięte już w Sesji 1: standings tylko dla sezonów 2022–2024 (szczegóły w "Ryzykach")
- [x] Decyzja: źródło danych żywych odłożone do startu Fazy 2 (decyzja właściciela z 2 lip — opis w "Ryzykach"); Fazy 1/3/4 na API-Football, sezon 2024/25
- [x] Modele: `Team`, `Standing` (+ `ForeignKey` do `League`, `UniqueConstraint`, `relationship`)
- [x] **Alembic** — init + konfiguracja (URL z `.env` przez `Settings`) + DWIE migracje (`leagues`, `teams`+`standings`); `create_all` usunięty z `main.py`
- [x] Wyczyszczenie testowych danych (46 lig UK) — w bazie 13 docelowych rozgrywek (6 lig + 6 pucharów + LM), import przez `POST /import-leagues` z filtrem `TARGET_LEAGUE_IDS` (1 zapytanie do API)

**Czego się uczysz:** relacje w bazach danych (klucze obce), migracje schematu (dlaczego `create_all` nie wystarcza), czytanie dokumentacji API.

### Sesja 4 — 9 lip [x] Import tabel lig (ETL)
- [x] Import standings 6 lig (Premier League, La Liga, Serie A, Bundesliga, Ligue 1, Primeira Liga) — `POST /import-standings`, sezon 2024/25; 114 drużyn + 114 wpisów w bazie, mistrzowie zweryfikowani
- [x] Strategia limitów: max 100 zapytań/dzień → dane trzymamy u siebie; odświeżanie = świadome wywołanie `POST /import-standings` (6 zapytań); obsługa błędów HTTP (`raise_for_status`, timeout, błąd w treści 200 OK, pusty response → `HTTPException` 502/404)
- [x] Upsert (update istniejących zamiast duplikatów) — aplikacyjny przez ORM, idempotencja przetestowana (2. przebieg: 0 insertów)

**Czego się uczysz:** wzorzec ETL, praca z limitami zewnętrznego API, upsert, obsługa błędów HTTP.

### Sesja 5 — 3 sie [x] Publiczne endpointy + pierwsze testy
- [x] Schematy Pydantic `TeamResponse`/`StandingResponse` (`StandingResponse` z zagnieżdżoną drużyną)
- [x] `GET /leagues` (rename z `/my-leagues`), `GET /leagues/{id}/standings` (path param, sezon, sort po `rank`, `joinedload` przeciw N+1)
- [x] **pytest** + `TestClient` — 4 testy API (root, `/leagues`, standings, błędne id → 404), wszystkie zielone
- [x] Struktura testów: folder `tests/` (`pytest` zainstalowany, `requirements.txt` zamrożony)
- [~] `app/routers/` — rozważone, ODŁOŻONE do Sesji 6 (`main.py` wciąż czytelny)

**Czego się uczysz:** pisanie testów automatycznych, dlaczego testy to must-have w CV.

### Sesja 6 — 5 sie [x] Puchary i drabinki
- [x] Model `Fixture` (mecz: drużyny home/away, wynik, data, runda, status) — dwa FK do `teams` + `foreign_keys=`
- [x] Import meczów pucharowych: 6 pucharów krajowych + Liga Mistrzów (`POST /import-fixtures`, 1733 mecze, sezon 2024)
- [x] Endpointy `GET /leagues/{id}/fixtures` (płaska lista) i `GET /leagues/{id}/bracket` (pogrupowane rundami, sort po dacie)
- [x] Migracja Alembic nr 3 (`create fixtures table`)
- [x] Routery (`app/routers/`) + testy — **ZROBIONE w Sesji 7** (log `sessions/session-07.md`): `competitions.py` + `imports.py`, helper `query_fixtures`, `get_db` → `database.py`, 6 testów pytest z izolowaną bazą

**Czego się uczysz:** modelowanie bardziej złożonych danych (dwa FK do jednej tabeli), grupowanie/transformacja danych pod UI, odporność ETL na braki danych.

---

## BLOK 2 — Frontend od zera + UI Fazy 1 (tygodnie 4–6: 21 lip – 10 sie)

> **Postęp (5 sie):** backend Fazy 1 domknięty dodatkową sesją porządkową — routery + testy pytest (log `sessions/session-07.md`). Numery sesji poniżej to **fazy**; kalendarzowo ruszają o jedną później (doszła sesja porządkowa). Nie przenumerowujemy — plan służy nam (ryzyko #4).
>
> **Postęp (10 sie):** „Start frontendu" zrobiony (kalendarzowo Sesja 8, log `sessions/session-08.md`) — Vite + React + TS, pierwszy komponent `LeagueCard`, CORS; spłacony dług `bracket` (filtr `knockout_only`). Milestone „UI tabel i drabinek działa" przesuwa się (frontend dopiero wystartował) — zgodnie z ryzykiem #4.
>
> **Postęp (17 sie):** „Podstawy React + Tailwind + pierwsza tabela" zrobione (kalendarzowo Sesja 9, log `sessions/session-09.md`) — `useState`/`useEffect`, `LeagueTable` z fetchem + typy TS, stany loading/error, Tailwind v4, rozbicie na pliki + prettier, logo drużyn. Działa tabela ligowa (PL 2024/25). Dalej: routing i nawigacja po 6 ligach.
>
> **Postęp (17 sie, Sesja 10):** „Routing i nawigacja" zrobione (kalendarzowo Sesja 10, log `sessions/session-10.md`) — React Router v7, strony `Home`/`League`, `useParams` (jeden `LeagueTable` dla wszystkich 6 lig), `Link` + layout z nagłówkiem, bazowy URL API w `.env` (`import.meta.env`). Nawigacja po 6 ligach działa (klikalne karty ⇄ tabela ligi). Dalej: TanStack Query (porządne pobieranie danych).
>
> **Postęp (18 sie, Sesja 11):** „Porządne pobieranie danych" zrobione (kalendarzowo Sesja 11, log `sessions/session-11.md`) — TanStack Query (`QueryClientProvider`, `useQuery`: cache/`isLoading`/`isError`), warstwa API `src/api/standings.ts` (`getStandings` + typy), refaktor `LeagueTable` (ręczny `useState`+`useEffect` → jeden `useQuery`, ~20 linii mniej). Plus kosmetyka: karty lig (siatka responsywna + hover) i nagłówek. Zanotowana nowa wizja UX (nawigacja przez kraje + selektor roku) — sekcja „Wizja docelowego UX". Dalej: drabinki pucharowe (UI).
>
> **Postęp (19 sie, Sesja 12):** „Drabinki pucharowe (UI)" zrobione (log `sessions/session-12.md`) — cała ścieżka drabinki (`api/bracket.ts` + `useQuery` + `Bracket` + `BracketPage`, trasa `/bracket/:id`), przebudowa na **drzewko turniejowe** (schodki przez `items-stretch`+`justify-around`, grupowanie dwumeczów, nagłówki `1/2/Σ` + agregat, zwężenie). Backend: doimport **Ligi Europy + Konferencji** (13→15 rozgrywek) + naprawa latentnego buga importu (`seen_team_ids` per-import). **Nawigacja**: HomePage jako accordion krajów (`<details>`) + puchary europejskie — Faza 1 klika się w całości. Dalej: tabela fazy ligowej (LM/LE/Konf) / szlify Fazy 1.

### Sesja 7 — [x] Start frontendu — ZROBIONE kalendarzowo w Sesji 8 (log `sessions/session-08.md`)
- [x] Node.js w WSL (przez `nvm`, v20.20.2 LTS), npm 10.8.2; ekosystem JS przez analogię do Pythona
- [x] `npm create vite@latest frontend -- --template react-ts` → React 19 + TypeScript + Vite 8 + oxlint; tour po plikach
- [x] Uruchomienie dev-servera (`npm run dev`, :5173, HMR), pierwszy własny komponent `LeagueCard` (props + reuse 5×)
- [x] **CORS** w FastAPI (`CORSMiddleware`, origin 5173) — zweryfikowane curlem (preflight + dozwolony/obcy origin)
- [x] (dług z S6/7) filtr `knockout_only` w `GET /leagues/{id}/bracket` + stała `KNOCKOUT_ROUNDS` + 2 testy

**Czego się uczysz:** ekosystem JS (node/npm/Vite), czym jest SPA, jak frontend rozmawia z backendem, CORS.

### Sesja 8 — [x] Podstawy React + Tailwind + pierwsza tabela — ZROBIONE kalendarzowo w Sesji 9 (log `sessions/session-09.md`)
- [x] Fundamenty React: komponenty, props, `useState`, `useEffect`
- [x] Tailwind CSS — instalacja (v4, plugin `@tailwindcss/vite`) i filozofia utility-first
- [x] Komponent `LeagueTable`: fetch z `GET /leagues/{id}/standings` + typy TS dla odpowiedzi API
- [x] (dodatkowo) stany loading/error (`res.ok`), rozbicie na `src/components/` + prettier, logo drużyn

**Czego się uczysz:** rdzeń Reacta, typowanie odpowiedzi API w TypeScript, Tailwind.

### Sesja 9 — [x] Routing i nawigacja — ZROBIONE kalendarzowo w Sesji 10 (log `sessions/session-10.md`)
- [x] React Router (v7): strona główna (lista 6 lig), `/leagues/:id`, layout z nagłówkiem
- [x] Nawigacja: klikalne karty lig (`<Link>`) + nagłówek jako powrót do `/` *(logo lig — opcjonalnie później)*
- [x] (dodatkowo) `useParams` — jeden `LeagueTable` dla wszystkich lig; bazowy URL API w `.env` (`src/api/config.ts`)

**Czego się uczysz:** routing w SPA, parametry URL, kompozycja layoutu.

### Sesja 10 — [x] Porządne pobieranie danych — ZROBIONE kalendarzowo w Sesji 11 (log `sessions/session-11.md`)
- [x] **TanStack Query**: `QueryClientProvider` + `useQuery` (cache, `isLoading`/`isError`, refetch w tle)
- [x] Refaktor `LeagueTable`: ręczny `useState`+`useEffect`+`try/catch` → jeden `useQuery`
- [x] Wspólny klient API (`frontend/src/api/standings.ts` — `getStandings` + typy `Team`/`Standing`)
- [x] (dodatkowo) kosmetyka Fazy 1: karty lig (siatka `grid` responsywna + `hover`/cień) i nagłówek (`border-b`, hover)

**Czego się uczysz:** profesjonalne wzorce data-fetchingu (to samo robi się w firmach).

### Sesja 11 — [x] Drabinki pucharowe (UI) — ZROBIONE kalendarzowo w Sesji 12 (log `sessions/session-12.md`)
- [x] Komponent `Bracket` — rundy jako kolumny, przebudowa na **drzewko turniejowe** (schodki + dwumecze + agregaty)
- [x] Strony pucharów krajowych + Ligi Mistrzów (trasa `/bracket/:id`, `BracketPage`)
- [x] (dodatkowo) doimport **Ligi Europy + Konferencji** (+ bug fix importu); **nawigacja** — accordion krajów na HomePage

**Czego się uczysz:** budowa niestandardowego, złożonego komponentu UI.

### Sesja 12 — [ ] Szlify Fazy 1 ✦ KAMIEŃ MILOWY (10 sie)
- [ ] Responsywność (mobile), stany błędów, loading skeletons
- [ ] Przegląd całości, porządki, aktualizacja README

---

## BLOK 3 — Faza 2: ulubione drużyny (tygodnie 7–8: 11–24 sie)
> Sezon 2026/27 właśnie startuje — pojawiają się żywe dane!

### Sesja 13 — [ ] Backend: wyniki i terminarz drużyn
- [ ] Import fixtures ligowych (przeszłe + przyszłe kolejki)
- [ ] `GET /teams/{id}/results?last=5`, `GET /teams/{id}/fixtures?next=5`
- [ ] `GET /teams?search=...` (wyszukiwarka)

**Czego się uczysz:** parametry zapytań, filtrowanie i sortowanie w SQLAlchemy, indeksy.

### Sesja 14 — [ ] Frontend: wybór ulubionych
- [ ] Wyszukiwarka drużyn + dodawanie/usuwanie ulubionych
- [ ] Zapis w `localStorage` (bez logowania — świadoma decyzja MVP; konta = stretch goal)

**Czego się uczysz:** localStorage, formularze kontrolowane, custom hook (`useFavorites`).

### Sesja 15 — [ ] Dashboard "Moje drużyny" ✦ KAMIEŃ MILOWY (24 sie)
- [ ] Widok: ostatnie wyniki + nadchodzące mecze ulubionych drużyn
- [ ] Tydzień 8 ma zapas — nadganiamy ewentualne zaległości

---

## BLOK 4 — Faza 3: Predictor (tygodnie 9–10: 25 sie – 7 wrz)

### Sesja 16 — [ ] Model Poissona (serce projektu!)
- [ ] Teoria (na spokojnie, krok po kroku): siła ataku/obrony drużyny liczona z historycznych wyników → oczekiwane gole λ (lambda) → rozkład Poissona → macierz prawdopodobieństw wszystkich wyników → suma = P(wygrana/remis/porażka)
- [ ] Implementacja w czystym Pythonie/numpy jako osobny moduł `app/prediction/poisson.py` (niezależny od API!)

**Czego się uczysz:** jak działa realny model statystyczny bukmacherów, numpy, separacja logiki biznesowej od warstwy API.

### Sesja 17 — [ ] Endpoint predykcji + testy
- [ ] `POST /predict` (dowolne 2 drużyny) → { P(1), P(X), P(2), top 5 wyników }
- [ ] Testy jednostkowe algorytmu (znane dane → oczekiwane wyniki)

### Sesja 18 — [ ] UI predictora ✦ KAMIEŃ MILOWY (7 wrz)
- [ ] Wybór 2 drużyn (selecty z wyszukiwarką)
- [ ] Wizualizacja: paski procentowe 1/X/2 + najbardziej prawdopodobne wyniki

---

## BLOK 5 — Faza 4: Symulator (tydzień 11: 8–14 wrz)

### Sesja 19 — [ ] Monte Carlo
- [ ] Symulacja meczu = losowanie wyniku z rozkładów Poissona
- [ ] Symulacja ligi: pozostałe mecze × 1000 iteracji od aktualnej tabeli → % szans na mistrzostwo / top 4 / spadek dla każdej drużyny

**Czego się uczysz:** metoda Monte Carlo, myślenie o wydajności (wektoryzacja numpy).

### Sesja 20 — [ ] UI symulatora ✦ KAMIEŃ MILOWY (14 wrz)
- [ ] Przycisk "Symuluj sezon" + tabela prawdopodobieństw z kolorami
- [ ] (opcjonalnie) symulacja drabinki pucharu

---

## BLOK 6 — Faza 5: Machine Learning (tygodnie 12–13: 15–28 wrz)

### Sesja 21 — [ ] Dataset i feature engineering
- [ ] Dane historyczne: **football-data.co.uk** (darmowe CSV, wiele sezonów wstecz, zero limitów — idealne do treningu)
- [ ] pandas: wczytanie, czyszczenie, cechy (forma z ostatnich 5 meczów, średnie goli, dom/wyjazd, H2H)
- [ ] Podział train/test (chronologicznie — nie losowo!)

**Czego się uczysz:** pandas, feature engineering, dlaczego dane czasowe dzieli się chronologicznie.

### Sesja 22 — [ ] Trening i ewaluacja modeli
- [ ] scikit-learn: regresja logistyczna + Random Forest
- [ ] Metryki: accuracy, log-loss, macierz pomyłek
- [ ] **Porównanie: model ML vs Poisson vs "zawsze typuj gospodarza"** (baseline)

**Czego się uczysz:** pełny cykl ML: dane → trening → ewaluacja → wnioski; czemu baseline jest ważny.

### Sesja 23 — [ ] Integracja ML z aplikacją
- [ ] Zapis wytrenowanego modelu (`joblib`), `POST /predict-ml`
- [ ] UI: porównanie predykcji obu modeli obok siebie

### Sesja 24 — [ ] FINISZ ✦ projekt gotowy do CV (do 30 wrz)
- [ ] README PRO: opis, screenshoty, diagram architektury, instrukcja uruchomienia, wnioski z porównania modeli
- [ ] GitHub Actions: CI uruchamiające ruff + pytest przy każdym pushu
- [ ] Ostatnie porządki w kodzie

---

## Stretch goals (jeśli zostanie czas / październik)
- Konta użytkowników (JWT) zamiast localStorage
- Docker + docker-compose (backend + frontend + Postgres jedną komendą)
- Deploy na darmowym hostingu (Railway/Render + Vercel) — link w CV robi robotę
- Głębsza analityka ML (xG, kalibracja prawdopodobieństw)

---

## Wizja docelowego UX (pomysły właściciela — do rozplanowania w sesjach)

> Zanotowane w Sesji 11 (2026-08-18). Docelowy kształt nawigacji i funkcji; realizacja
> rozłożona na kolejne sesje. Zastępuje obecną „płaską" listę 6 lig na HomePage.

**HomePage — nawigacja przez kraje (rozwijana lista):**
- Lista **krajów** (Anglia, Hiszpania, Włochy, Niemcy, Francja, Portugalia), a obok nich —
  na tym samym poziomie — **puchary europejskie** jako osobne pozycje: Liga Mistrzów,
  Liga Europy, Liga Konferencji (są ponadnarodowe, więc nie „siedzą" pod żadnym krajem).
- Kliknięcie w kraj **rozwija** (accordion) rozgrywki należące do niego: **liga** + **puchar krajowy**.
- Kliknięcie w konkretną rozgrywkę → przejście do jej **tabeli** (liga) lub **drabinki** (puchar).
- Osobna **zakładka z predyktorami** na HomePage — *dalszy etap* (dopiero po zbudowaniu modelu, Faza 3+).

**Strona rozgrywek — wybór sezonu:**
- Na widoku tabeli/drabinki **selektor roku** z dostępnych sezonów, by przeglądać różne edycje.

**⚠️ Implikacje do rozważenia przy planowaniu (nie blokują, ale trzeba je ogarnąć):**
- *Wybór roku* wymaga danych wielosezonowych. API-Football (Free) daje **2022/23–2024/25** —
  import kolejnych sezonów = dodatkowe zapytania (limit 100/dobę) + wpisy w bazie. Do zaplanowania.
- *Puchary europejskie:* obecnie w bazie jest tylko **Liga Mistrzów**; **Liga Europy** i
  **Liga Konferencji** to nowe rozgrywki do doimportowania (`TARGET_LEAGUE_IDS` + `POST /import-fixtures`).
- *Accordion + selektor roku* to nowe komponenty UI — naturalnie wpasują się w Blok 2 (szlify Fazy 1)
  i Fazę 2; przy najbliższym rytuale końca sesji zmapujemy je na konkretne sesje.

---

## Ryzyka i plany awaryjne

1. **Limity API-Football — ZWERYFIKOWANE 2026-07-02 (test na naszym kluczu).**
   - Plan: **Free**, aktywny do 2027-03, **100 zapytań/dobę**.
   - **Dostęp do sezonów: TYLKO 2022/23, 2023/24, 2024/25.** Brak dostępu do 2025/26 (zakończony) i 2026/27 (nadchodzący). Najnowszy dostępny = **2024/25**.
   - **Decyzja:** Fazy 1, 3, 4 budujemy na sezonie **2024/25** (kompletne, realne dane — w zupełności OK dla portfolio). Faza 5 (ML) niezależna — dane z CSV football-data.co.uk.
   - **Faza 2 (ulubione: nadchodzące mecze)** to jedyna faza wymagająca żywych danych. Decyzję o źródle podejmujemy przy jej starcie (~24 sie, gdy ruszy sezon 2026/27).
   - **Preferencja właściciela (ustalona 2026-07-02):** chce mieć **bieżący sezon ORAZ historię z kilku poprzednich**. Opcja "demo tylko na 2024/25" ODPADA. Do wyboru dwie pełne drogi:
     - **A) Darmowa hybryda:** [football-data.co.uk](https://www.football-data.co.uk) (CSV: 20+ sezonów historii + bieżący sezon, wyniki → tabele liczymy sami) + [football-data.org](https://www.football-data.org) (darmowe API: terminarz + tabele live dla 6 lig + LM). 0 zł, więcej pracy, brak pucharów krajowych. **← rekomendacja dla CV.**
     - **B) API-Football premium:** jedno źródło, wszystko (bieżący + historia + puchary + logo), ~19 €/mies.
     - Wybór: **odłożony na decyzję właściciela** (Sesja 3 / start Fazy 2).
2. **Kalendarz piłkarski:** lipiec to przerwa między sezonami — budujemy na zakończonym sezonie 2025/26, a żywe dane wskoczą naturalnie w sierpniu (start 2026/27) — akurat na Fazę 2.
3. **Wakacje/mniej czasu:** bufor w tygodniu 8 i na końcu; w razie poślizgu tniemy: symulację pucharów (S20), część szlifów UI — nigdy nie tniemy testów i README.
4. **Spuchnięte sesje:** jeśli sesja się nie mieści w 2–4h, przenosimy resztki do następnej i aktualizujemy ROADMAP — plan służy nam, nie odwrotnie.
