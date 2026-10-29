# Sesja 20 — 29 października 2026

> **Faza 4 backend gotowa: Monte Carlo liczy szanse każdej drużyny na każde miejsce.**
> Sesja wyszła szersza niż punkt „symulacja" z TODO, bo zaczęła się od przypomnienia
> wizji: projekt ma obsługiwać **wiele wymiennych modeli predykcji**. Zanim więc
> powstała symulacja, powstał kontrakt modelu i rejestr — i dopiero na nich oparliśmy
> symulator, endpointy i testy. Frontend symulacji świadomie przeniesiony na Sesję 21.

## Decyzje (i dlaczego)

- **Kontrakt modelu jako `abc.ABC`, nie `typing.Protocol`.** Protocol sprawdza zgodność
  tylko w statycznej analizie typów, a projekt ma ruffa i **nie ma mypy** — brakująca
  metoda przeszłaby niezauważona aż do wywołania na produkcji. ABC z `@abstractmethod`
  wywala się przy **tworzeniu** obiektu, czyli natychmiast.
- **Rejestr jako jawny słownik `{"poisson": PoissonModel}`**, bez automatycznego
  skanowania pakietu. Dodanie modelu to jedna linijka w jednym pliku, a lista modeli
  jest czytelna dla człowieka. Metadane (`name`, `label`, `description`,
  `supports_cross_league`) jako **atrybuty klasy**, nie pola obiektu — dzięki temu
  `GET /models` czyta je bez tworzenia modelu, czyli bez ligi, sezonu i sesji bazy.
  To jedyny endpoint w projekcie bez `Depends(get_db)`.
- **Zwykłe klasy z `__init__` w całym pakiecie `prediction/`** — decyzja właściciela,
  wbrew mojej propozycji `@dataclass`. Argument: w większym projekcie jednolite
  narzędzia zmniejszają szum, a dataclass oszczędza kilka linii. Przyjęte i **zapisane
  do `CLAUDE.md`**. Koszt: tracimy darmowe `frozen=True`, więc gwarancję „symulacja nie
  modyfikuje tabeli startowej" przeniesiono do testu.
- **Pełna macierz pozycji zamiast trzech liczb.** Zamiast zwracać szanse na tytuł,
  top 4 i spadek, zwracamy dla każdej drużyny prawdopodobieństwo **każdego miejsca**
  (lista długości = liczba drużyn, sumująca się do 1). Trzy wcześniejsze liczby to
  wycinki tej listy, a pytanie „jakie są szanse na miejsca 5–7" przestaje wymagać
  zmiany w API.
- **Siły drużyn z sezonu poprzedniego, nie symulowanego.** Zapytania do bazy pokazały,
  że sezon 2026 ma rozegrane **1–2 kolejki**. Siła liczona z takich danych daje
  `attack = 0` drużynie, która jeszcze nie strzeliła — a taka drużyna nie strzeli ani
  raz w tysiącu symulacji. Endpoint domyślnie bierze więc `season - 1`, z parametrem
  `strength_season` jako wyjściem awaryjnym (pod koniec sezonu dane bieżące będą lepsze).
- **Neutralne 1.0/1.0 dla beniaminków.** Promowane drużyny nie mają wiersza w tabeli
  poprzedniego sezonu tej ligi (w PL: Hull City, Ipswich, Coventry). „Dokładnie
  przeciętna drużyna" to nieprawda — awansujący są statystycznie słabsi — ale **jedyna
  uczciwa wartość**, jaką mamy, bo ich dane leżą w nieimportowanej niższej lidze. Lepsze
  oszacowanie wymaga sił porównywalnych między ligami, czyli przyszłego modelu
  cross-league. Zapisane jako świadome uproszczenie w docstringu.
- **`match_lambdas` jako tymczasowa zaślepka, potem usunięta.** Przy przepisywaniu
  `strength.py` zostawiliśmy starą funkcję jako dwuwierszowe opakowanie na
  `LeagueStrength`, żeby krok „siły" nie musiał ruszać routera. Gdy router przeszedł na
  rejestr i funkcja straciła ostatniego wywołującego — skasowana. Funkcja z docstringiem,
  której nikt nie woła, jest gorsza niż jej brak.
- **`ValueError` z `simulate_season` celowo nieobsługiwany w routerze.** `build_model`
  jest w `try` (nieznany model → 400, brak danych o lidze/sezonie → 404), ale samo
  wywołanie symulacji nie. Jego `ValueError` oznacza mecz z drużyną, której nie ma
  w tabeli — czyli niespójność **naszych** danych, a nie błąd pytającego. Ma wyjść jako
  500 z tracebackiem w logach, nie jako 404 zwalające winę na klienta.
- **Liczniki na zwykłych listach, nie w numpy.** Wbrew pierwszej intuicji — pomiar niżej.

## Co zostało zrobione

### Strona 404 (dług z Sesji 19)

1. **`frontend/src/pages/NotFoundPage.tsx`** + trasa `path="*"` w `App.tsx`. Design:
   wyszarzony numer 404 jako znak wodny, ścieżka odbita w `<code>`, przycisk powrotu.
   Przy okazji `hover:underline` na linku w nagłówku — żeby było widać, że jest klikalny.
2. Poprawki w kodzie właściciela: cała strona była zawinięta w `<h2>` (niepoprawny HTML
   z `<div>` w środku, dziedziczony rozmiar czcionki na przycisku) → layout na `<div>`,
   `<h2>` tylko na nagłówku. `path="/*"` → `path="*"`.

### Architektura wielu modeli

3. **`app/prediction/base.py`** (NOWY) — `PredictionModel(ABC)`: metadane jako atrybuty
   klasy, `__init__(db, league_id, season)`, abstrakcyjne `probabilities()` i `sample()`,
   domyślne `top_scorelines()` (pusta lista) i `sample_many()` (pętla po `sample`).
4. **`app/prediction/poisson_model.py`** (NOWY) — `PoissonModel`: składa `poisson.py`
   i `strength.py` w model spełniający kontrakt. Nadpisuje `sample_many`, bo potrafi
   wylosować wszystko jednym wywołaniem numpy.
5. **`app/prediction/registry.py`** (NOWY) — `MODELS`, `DEFAULT_MODEL`,
   `UnknownModelError`, `get_model_class`, `build_model`, `list_models`.

### Symulator

6. **`app/prediction/simulation.py`** (NOWY, 168 linii) — `TeamStart`, `TeamOutcome`,
   `final_table` (kolejność końcowa: punkty → bilans → strzelone) i `simulate_season`:
   walidacja zgodności terminarza z tabelą, jedno wywołanie `model.sample_many`, pętla
   po symulacjach ze **świeżą kopią tabeli startowej w każdym obiegu**, zliczanie pozycji
   do macierzy, na końcu sortowanie po średniej punktów.

### Siły drużyn — przepisane

7. **`LeagueStrength`** zastąpiła `league_baseline` i `team_attack_defence`: jedno
   zapytanie o całą tabelę, `base` i słownik sił policzone w konstruktorze, mecz to już
   tylko dwa odczyty ze słownika. `PoissonModel` tworzy ją raz w `__init__` (przez
   `super()`), nie raz na mecz.
8. **Cztery usterki naprawione po drodze**: `standing` mogło być `None` (beniaminek) →
   neutralne 1.0; `played` mogło być `0` → drużyna pomijana przy liczeniu sił; `base`
   mogło być `0` → `ValueError` z komunikatem przy tworzeniu obiektu; cztery zapytania
   na mecz → jedno na ligę.

### Endpointy

9. **`GET /models`** — lista modeli dla przełącznika w UI.
10. **`GET /predict` przez rejestr** — nowy parametr `?model=`, zero matematyki
    w routerze, `MAX_GOALS` przeniesione do `PoissonModel`, usunięte `float()`
    (kontrakt już to gwarantuje).
11. **`GET /leagues/{league_id}/simulate`** — parametry `season`, `model`, `iterations`
    (`Query(ge=1, le=10000)`), `strength_season`, `seed`. Odpowiedź: `SimulationResponse`
    z `model`, `iterations`, `matches_simulated` i listą drużyn posortowaną po średniej
    punktów — czyli przewidywaną tabelą końcową.
12. **Trzy nowe schematy**: `ModelInfo`, `TeamSimulationOutcome`, `SimulationResponse`.

### Testy

13. **`tests/test_simulation.py`** (NOWY) — 9 testów **bez bazy danych**, na dwóch
    atrapach modelu (`AlwaysHomeWinsModel`, `RandomGoalsModel`). Atrapy nie definiują
    `sample_many`, więc testy pokrywają też domyślną implementację z `base.py`.
14. **9 testów endpointu** w `test_main.py` + cztery funkcje pomocnicze. Najmocniejszy:
    `test_simulate_takes_strength_from_the_previous_season` — tabela 2024 jest celowo
    **płaska**, więc przewaga drużyny może pochodzić wyłącznie z sezonu 2023.
15. **Testy mutacyjne** — psuliśmy kod celowo, żeby sprawdzić, czy testy to wyłapią.
    Wyniki niżej; dwa z nich wymusiły przepisanie testów.

## Pomiary

| Co | Wynik |
|---|---|
| Losowanie 380 000 goli: numpy jednym wywołaniem vs pętla Pythona | 11 ms vs 95 ms (**8x**) |
| Pamięć tablicy (1000, 380, 2): `int16` vs listy Pythona | 1.5 MB vs 51 MB (**34x**) |
| Licznik `rank_counts` w pętli: numpy vs listy | 4.5 ms vs **1.2 ms** (numpy przegrywa) |
| `index_pairs` jako optymalizacja pętli | 22 ms zysku na pół sekundy → **odrzucone** |
| Symulacja PL (359 meczów × 1000): przed krokiem „siły" | 0.90 s (0.68 s to zapytania) |
| …po `LeagueStrength` w `match_lambdas` | 0.42 s |
| …po podłączeniu do `PoissonModel` | **0.18 s** |
| Endpoint `/leagues/39/simulate` end-to-end | 0.32 s |

## Czego się nauczyliśmy

- **Test, którego nigdy nie widziałeś na czerwono, nie jest jeszcze testem.** Dziewięć
  testów symulatora przeszło od pierwszego uruchomienia — i dopiero celowe psucie kodu
  pokazało, że **transpozycja macierzy `rank_counts` przechodziła niezauważona**.
- **Niezmienniki symetryczne nie wykryją transpozycji.** Sumy po wierszach i po kolumnach
  są dla macierzy transponowanej identyczne. Przy tabeli startowej posortowanej po
  `team_id` macierz wychodziła symetryczna, więc żadna asercja nie mogła tego złapać.
  Naprawione **danymi**: tabela ułożona cyklicznie (drużyna 3 pierwsza, 1 druga,
  2 trzecia) przestaje być symetryczna. Jedna zmiana w danych testowych zrobiła więcej
  niż dowolna liczba kolejnych asercji.
- **Test może przechodzić z niewłaściwego powodu.**
  `test_simulate_unknown_league_returns_404` przechodził po usunięciu strażnika pustej
  tabeli, bo 404 przychodziło z innego miejsca (`LeagueStrength`) i komunikat też
  zawierał numer ligi. Naprawione przez asercję na treść komunikatu + osobny test na
  przypadek, w którym strażnik jest jedyną obroną.
- **numpy jest szybkie, kiedy pętla siedzi w środku numpy.** Kiedy pętlę prowadzi Python,
  numpy jest narzutem: każdy odczyt pakuje surowe bajty w obiekt. Stąd tablica wyników
  w numpy, a liczniki na listach.
- **Dwa różne rodzaje sprawdzeń.** Walidacja danych wejściowych należy do granicy systemu
  i robi się ją raz (duplikat `team_id` pilnuje `UniqueConstraint` w bazie — sprawdzanie
  go w kodzie było zbędne). Warunek wstępny funkcji to inna rzecz: zgodność **dwóch
  niezależnych argumentów** (terminarz vs tabela) może zepsuć tylko wywołujący, więc
  sprawdzenie zostaje tam, gdzie widać oba.
- **„Jest czymś" → dziedziczenie, „ma coś" → pole.** `PoissonModel` **jest** modelem
  predykcyjnym (dziedziczy po `PredictionModel`), ale **ma** siły drużyn
  (`self.strength = LeagueStrength(...)`). Gdyby `LeagueStrength` dziedziczyła po
  kontrakcie, symulacja mogłaby zawołać na niej `sample()`.
- **Sesja bazy żyje tyle, co jedno żądanie HTTP.** `get_db` zamyka ją w `finally`, więc
  instancji modelu (trzymającej `self.db`) nie wolno cache'ować między żądaniami. Rejestr
  dlatego **tworzy** modele, a nie przechowuje gotowe.
- **`base` to gole przeciętnej drużyny w jednym meczu, nie gole w meczu.** Licznik (suma
  `goals_for`) liczy każdy gol raz, mianownik (suma `played`) liczy każdy mecz dwa razy —
  raz u każdej ze stron. Podwójne liczenie jest w mianowniku celowo: λ opisuje **jedną
  stronę jednego meczu**. Zmierzone na PL 2025: 1045/760 = 1.375, a 1.375 + 1.375 = 2.75
  gola na mecz.
- **Linter sprawdza składnię, nie intencję.** Błąd w `registry.py` —
  `f"...: ", ".join(...)"` przeczytane jako **dwa argumenty** — przeszedł przez ruffa
  i objawił się dopiero jako krotka w treści wyjątku.
- **Klucz słownika to nie to samo co klucz główny wiersza.** `self.strengths[row.id]`
  zamiast `[row.team_id]` zapisywało siły pod numerami wierszy standings. Nic nie
  wybuchało: fallback `(1.0, 1.0)` przykrywał to idealnie i symulacja zwracała ligę,
  w której dwadzieścia drużyn ma te same szanse.
- **`ORDER BY` bywa warunkiem poprawności, nie estetyki.** Pozycja meczu w `pairs`
  decyduje, która λ losuje jego gole; PostgreSQL bez `ORDER BY` nie obiecuje kolejności.
  Niestabilna kolejność znaczy, że ten sam `seed` zwraca różne tabele.
- **FastAPI zwraca 422, nie 400**, za naruszenie ograniczeń parametru (`ge`, `le`).
  To poprawne: „zrozumiałem żądanie, ale wartości są nie do przyjęcia".

## Testy mutacyjne — wyniki

| Celowo wprowadzony błąd | Wyłapany przez |
|---|---|
| Kopia tabeli startowej wyciągnięta przed pętlę | `test_team_that_wins_every_match_takes_the_title` |
| Zapis wyników do `start` | `test_starting_table_is_not_modified` |
| Transpozycja `rank_counts` | `test_no_fixtures_left_returns_the_current_table` (po poprawce danych) |
| Siły liczone z symulowanego sezonu | dwa testy endpointu |
| Usunięty strażnik pustej tabeli | dwa testy endpointu (po poprawce) |
| Usunięte `ORDER BY` przy meczach | **nikt — brak pokrycia** |

Ostatniego wiersza nie dało się naprawić: testy chodzą na SQLite, które zwraca wiersze
w stabilnej kolejności `rowid`, więc brak `ORDER BY` jest tam niewidoczny. Problem dotyczy
wyłącznie PostgreSQL-a. Odrzucone alternatywy: asercja na treść wygenerowanego SQL-a (test
implementacji, kruchy) i prawdziwy PostgreSQL w testach (łamie zasadę z `CLAUDE.md`, że
testy nie dotykają niczego poza bazą w pamięci).

## Stan repo po sesji

- **Backend NOWE**: `app/prediction/base.py`, `poisson_model.py`, `registry.py`,
  `simulation.py`.
- **Backend ZMIENIONE**: `prediction/strength.py` (przepisany na `LeagueStrength`,
  usunięte `league_baseline`, `team_attack_defence` i `match_lambdas`),
  `routers/predictions.py` (trzy endpointy, rejestr, zero matematyki), `schemas.py`
  (trzy nowe schematy).
- **Frontend NOWE**: `src/pages/NotFoundPage.tsx`. **ZMIENIONE**: `src/App.tsx`
  (trasa `*`, hover na linku nagłówka).
- **Testy NOWE**: `tests/test_simulation.py` (9 testów). **ZMIENIONE**: `test_main.py`
  (+9 testów endpointu + 4 funkcje pomocnicze).
- **Dokumentacja**: `CLAUDE.md` — nowa reguła o zwykłych klasach w `prediction/`.
- **Jakość**: pytest **37/37** (było 19), Ruff czysty na `app/` i `tests/`.
- **Dane**: bez zmian, zero zapytań do API-Football (subskrypcja Pro wygasła
  1 października — baza żyje z tego, co zaimportowaliśmy).

## Długi techniczne

- **Frontend symulacji w całości** — endpoint działa, ale nikt go nie widzi. To cała
  Sesja 21.
- **`ORDER BY` przy meczach bez pokrycia testem** (powód wyżej).
- **`DEFAULT_SEASON = 2024` w `constants.py` jest nieaktualne** razem z komentarzem
  o darmowym planie API — od Sesji 14 mamy Pro i dane do 2026.
- **Endpoint symulacji zakłada, że `points`, `goals_for` i `goals_against` nie są NULL.**
  Dla danych z importu to prawda, ale niepełny wiersz standings dałby 500. Do decyzji:
  `or 0` czy kontrakt na dane.
- **Zrzuty ekranu do README** — sekcja wciąż zakomentowana, czeka na
  `docs/screenshots/*.png`.
- **GitHub Actions** — przeniesione z TODO Sesji 20, nic nie powstało.
- Z poprzednich sesji: `TeamSelect` (duplikacja selektorów w `PredictPage`), selektory
  elementów w `index.css` bijące utilki Tailwinda, loading state drużyn, hasło do bazy
  nierotowane, te same sekrety lokalnie i na produkcji.

## TODO na Sesję 21

> Backend Fazy 4 jest gotowy. Sesja 21 to pokazanie go — i to jest kamień milowy
> „UI symulatora" z ROADMAP-y.
1. **`src/api/simulation.ts`**: typy `ModelInfo`, `TeamSimulationOutcome`, `Simulation`
   + `getModels()` i `getSimulation(leagueId, season, model)`. Uwaga:
   `SIMULATION_SEASON = 2026` (sezon trwający), bez `strength_season` — backend sam
   weźmie 2025.
2. **`src/pages/SimulatePage.tsx`**: wybór ligi i modelu (lista z `/models`),
   uruchomienie symulacji przez `useQuery`.
3. **`src/components/SimulationTable.tsx`**: tabela z przewidywanym miejscem, średnią
   punktów i szansami na tytuł / top 4 / spadek — wszystkie trzy jako **wycinki**
   `position_probabilities`.
4. **Trasa w `App.tsx`** + wejście z `HomePage`.
5. **Przełącznik modelu na `PredictPage`** — endpoint już przyjmuje `?model=`.
6. (jeśli zostanie czas) **Heatmapa pełnej macierzy 20×20** — najmocniejszy wizualnie
   element projektu, ale dopiero gdy tabela działa.
7. (jeśli zostanie czas) **Zrzuty ekranu do README** i **GitHub Actions**.

## Praca domowa

> Sesja 21 jest w całości frontendowa: dane już są, trzeba je pokazać.

### 🔴 Priorytet 1 — zapytania zależne od wyboru użytkownika
1. **TanStack Query: opcja `enabled`** —
   [dokumentacja](https://tanstack.com/query/latest/docs/framework/react/guides/dependent-queries).
   Wzorzec jest już w `PredictPage` (zapytanie o predykcję czeka, aż wybierzesz obie
   drużyny). Zwróć uwagę, **dlaczego** to lepsze niż `if` wokół `useQuery`: hooki muszą
   się wywołać przy każdym renderze, więc zapytania nie wyłącza się warunkiem, tylko
   flagą.
2. **`queryKey` jako lista zależności** — przejrzyj, jak klucze są budowane w `src/api/`
   i `src/pages/` tego projektu. Pytanie do przemyślenia: co się stanie, gdy zmienisz
   model w selektorze, a `model` nie będzie częścią `queryKey`?

### 🟡 Priorytet 2 — prezentacja macierzy
3. **Skala kolorów w Tailwindzie bez dynamicznych nazw klas** — przypomnij sobie lekcję
   z Sesji 18: `bg-${color}-500` **nie działa**, bo Tailwind skanuje kod statycznie i nie
   zobaczy takiej klasy. Poszukaj wzorca „lookup table" — słownik progów mapowany na
   **pełne literały klas**. To będzie potrzebne przy heatmapie.
4. **`toFixed` i formatowanie procentów** — `position_probabilities` to liczby 0–1.
   Zastanów się, gdzie zamieniasz je na procenty i ile miejsc po przecinku ma sens przy
   1000 iteracjach (podpowiedź z Sesji 20: błąd przy 1000 losowaniach to około
   ±1.5 punktu procentowego, więc dwie cyfry po przecinku udają precyzję, której nie ma).

### 🟢 Priorytet 3 — CI (przeniesione z Sesji 20)
5. **GitHub Actions — podstawy** —
   [dokumentacja](https://docs.github.com/en/actions/writing-workflows/quickstart).
   Struktura `.github/workflows/*.yml`: `on`, `jobs`, `steps`. Zwróć uwagę na jedną
   pułapkę tego projektu: `app/config.py` wymaga `DATABASE_URL`, `API_FOOTBALL_KEY`
   i `IMPORT_TOKEN` przy samym imporcie aplikacji, więc workflow musi podać atrapy tych
   zmiennych — inaczej `pytest` padnie przed pierwszym testem.
