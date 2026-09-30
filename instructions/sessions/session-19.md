# Sesja 19 — 28–30 września 2026

> **DEPLOY. Projekt jest publicznie dostępny w internecie.**
> Frontend: https://football-predictor-adimilo190.vercel.app
> API: https://football-predictor-ac40.onrender.com (+ `/docs`)
> Sesja w trzech aktach: (1) przygotowanie kodu pod produkcję, (2) wielkie przejście
> dokumentacyjne — każdy plik repo po angielsku, z nagłówkiem „co tu jest i po co",
> (3) faktyczny deploy na trzy usługi + README pod CV. Kamień milowy „publiczny link"
> osiągnięty **przed** Fazą 4/5, zgodnie z decyzją z Sesji 17.

## Decyzje (i dlaczego)

- **Hosting: Render (backend) + Neon (baza) + Vercel (frontend).** Weryfikowaliśmy
  aktualne warunki na żywo, bo darmowe plany zmieniają się co kilka miesięcy.
  Kluczowe odkrycie: **darmowy PostgreSQL na Renderze wygasa po 30 dniach** (+14 dni
  łaski, potem baza jest kasowana razem z danymi) — dla linku w CV to wyrok śmierci
  w połowie października. Neon nie ma daty wygaśnięcia (0,5 GB, 100 h compute/mies.),
  więc baza idzie tam, a Render dostaje tylko proces. **Railway odpadł** — nie ma już
  stałego darmowego planu, tylko $5 kredytu na 30 dni; Fly.io i Koyeb wycofały darmowy
  compute w 2026.
- **Wszystko we Frankfurcie.** Render i Neon w tym samym regionie (`eu-central-1`).
  Baza w USA + backend w Europie = ~100 ms narzutu na każde zapytanie, a nasze
  endpointy robią ich po kilka.
- **Cron budzący zamiast płatnego planu.** Render usypia darmową usługę po 15 minutach
  (cold start ~40 s). UptimeRobot pinguje `/` co 5 minut, dzięki czemu demo jest zawsze
  ciepłe. Mieścimy się w limicie 750 h/mies., ale nazwijmy rzecz po imieniu: to
  obchodzenie mechanizmu, który Render wprowadził celowo. Alternatywa w razie zmiany
  zasad: Starter $7/mies. **Pingujemy `/`, nie `/leagues`** — health check nie dotyka
  bazy, więc Neon może spokojnie spać i nie przepala swoich 100 h compute.
- **Nie GitHub Actions do pingowania**, choć wyglądałoby lepiej w repo: harmonogramy
  bywają opóźnione o kilkanaście minut, a na publicznych repo GitHub wyłącza zaplanowane
  workflow po 60 dniach bez commita — czyli cron umarłby dokładnie wtedy, gdy projekt
  przestanie być aktywnie rozwijany.
- **Dane na produkcję przez `pg_dump`, nie przez `POST /import-*`.** Trzy zyski: zero
  zużycia limitu API, produkcja dostaje dokładnie to, co widzimy lokalnie, i brak
  zależności od subskrypcji wygasającej 1 października.
- **Rotacja sekretów tylko częściowa.** Zrzut ekranu z panelu Rendera odsłonił trzy
  wartości. `IMPORT_TOKEN` zrotowany (zweryfikowane: stary token → 401). Hasło do bazy
  — właściciel świadomie zdecydował, że zostaje (prywatny czat). Klucz API-Football
  i tak wygasa 1 października.
- **Logi sesji zostają po polsku.** Przy przechodzeniu repo na angielski właściciel
  wybrał zakres „dokumenty projektowe": przetłumaczone `ROADMAP`, `progres`,
  `project-structure`, `project-assumptions`, `tools` (1220 linii) + `CLAUDE.md`,
  `.gitignore`, oba `.env.example`. Logi sesji to dziennik nauki — tłumaczenie odebrałoby
  im funkcję. Zamiast tego angielski `sessions/README.md` wyjaśnia, czym są, i odsyła do
  `progres.md` jako angielskiego streszczenia.

## Co zostało zrobione

### Akt 1 — przygotowanie kodu pod produkcję

1. **CORS z zmiennej środowiskowej** (`config.py` + `main.py`): pole `ALLOWED_ORIGINS`
   (string rozdzielony przecinkami, bo zmienne środowiskowe to zawsze tekst) +
   `@property allowed_origins_list` rozbijający go na listę (`split` → `strip` →
   pominięcie pustych). Adres frontendu przestał być kodem, stał się konfiguracją.
2. **Ochrona endpointów importu** — nowy `app/security.py` z zależnością
   `require_import_token`: czyta nagłówek `X-Import-Token`, porównuje przez
   `secrets.compare_digest` (stały czas → brak timing attacku), rzuca 401. Podpięta do
   **całego routera** (`APIRouter(dependencies=[...])`), więc każdy przyszły endpoint
   importu jest chroniony domyślnie.
3. **`Procfile`** (`alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port
   ${PORT:-8000}`), **`.python-version`** (3.10.12) i **walidator `DATABASE_URL`**
   w `config.py` (`postgres://` → `postgresql://`, bo SQLAlchemy 2.0 zna tylko drugą
   formę, a część hostingów podaje pierwszą).
4. **Odporność puli połączeń** (`database.py`): `pool_pre_ping=True` + `pool_recycle=300`
   — Neon usypia compute po ~5 minutach, więc połączenia w puli umierają po stronie
   serwera. Bez tego pierwsze zapytanie po przebudzeniu = `server closed the connection
   unexpectedly`.

### Akt 2 — przejście dokumentacyjne (całe repo)

5. **Nagłówki w 18 plikach, które ich nie miały** (`models.py`, `routers/teams.py`,
   `prediction/poisson.py`, `prediction/strength.py`, oba `__init__.py`, `alembic/env.py`
   + 11 plików frontendu) i rozszerzenie zbyt ubogich (`database.py`).
6. **Komentarze w 11 nieoczywistych miejscach**: klasa `Fixture` (statusy, nullowalne
   gole, `round` jako tekst), wzór na λ, `queryClient` poza komponentem, `!` przy
   `getElementById`, adapter `fixtureToMatchup`, skąd bierze się nazwa drużyny
   w `TeamPage`, dlaczego hooki stoją przed guardami, dlaczego stany lecą do zmiennej
   w `SearchPage`, sezon w `queryKey`, flexbox drzewka, pełne literały klas Tailwinda.
7. **Znalezione przy okazji**: nieaktualny komentarz w `SearchPage` („200ms" przy kodzie
   z `300`) — poprawiony; martwy `App.css` (nic go nie importowało) — usunięty; polska
   wiadomość z `GET /` przetłumaczona (+ asercja w teście).
8. **Angielski w plikach konfiguracyjnych i dokumentach** (zakres wybrany przez
   właściciela) + nowy `instructions/sessions/README.md`.

### Akt 3 — deploy

9. **Neon**: projekt `football-predictor`, region AWS Frankfurt, tylko usługa Postgres
   (reszta wyłączona), connection string bezpośredni (bez `-pooler`).
10. **Render**: Web Service z repo GitHub, Frankfurt, plan Free, build
    `pip install -r requirements.txt`, start z `Procfile`, 4 zmienne środowiskowe.
    Pierwszy deploy w 1m25s — w logach widać trzy `Running upgrade`, czyli **Alembic
    utworzył schemat na produkcji**.
11. **Migracja danych**: `pg_dump --data-only` w **dwóch przebiegach** — najpierw rodzice
    (`leagues`, `teams`), potem dzieci (`standings`, `fixtures`). Powód: `pg_dump`
    zrzuca tabele alfabetycznie, więc `fixtures` poszłyby przed `leagues` i klucze obce
    by to odrzuciły. Plus `setval` na sekwencji `standings.id` (jedyne id generowane
    przez bazę — reszta przychodzi z API).
12. **Vercel**: projekt z `Root Directory = frontend` (Vercel sam wykrył FastAPI z
    korzenia repo — trzeba było poprawić preset na Vite), jedna zmienna `VITE_API_URL`.
    Wykryte przez Vercela „4 env variables" z backendowego `.env.example` — **usunięte**,
    bo do frontendu nie trafiają sekrety (wszystko z prefiksem `VITE_` ląduje w bundlu).
13. **CORS spięty**: `ALLOWED_ORIGINS=http://localhost:5173,https://football-predictor-adimilo190.vercel.app`.
    Zmierzone przed i po: preflight z domeny Vercela dawał 400 bez nagłówka
    `access-control-allow-origin`, po zmianie 200 z nagłówkiem.
14. **Dwa błędy złapane testami z zewnątrz**, niewidoczne z przeglądarki właściciela:
    - **Vercel Authentication** — wszystkie ścieżki zwracały 302 na `vercel.com/sso-api`.
      Właściciel widział działającą stronę (miał sesję), **rekruter zobaczyłby ekran
      logowania**. Wyłączone w Deployment Protection.
    - **404 na głębokich linkach** (`/predict`, `/leagues/39`) — klasyczna pułapka SPA:
      routing jest po stronie Reacta, a serwer szuka pliku o tej nazwie. Naprawione
      przez `frontend/vercel.json` z rewrite `/(.*)` → `/index.html` (**rewrite**, nie
      redirect — adres w pasku musi zostać, żeby React Router widział trasę).
    - Przy okazji: tytuł zakładki to był `frontend` z szablonu Vite → `Football
      Predictor` + `meta description` pod podglądy linków.
15. **UptimeRobot**: monitor HTTP/S na `/`, co 5 minut, status Up.
16. **Odświeżenie danych na produkcji** (ostatni dzień ważnej subskrypcji): standings
    2026 (114 wierszy zaktualizowanych) + fixtures 2026 (**+233 nowe mecze**, 3145
    zaktualizowanych, +15 drużyn z Copa del Rey). 26 sekund, ~21 zapytań do API.
17. **README pod CV** (186 linii, angielski): link do dema i `/docs`, opis funkcji,
    działanie modelu Poissona krok po kroku, **sekcja „Known limitations"**, diagram
    architektury, stack z uzasadnieniem, tabela endpointów, instrukcja uruchomienia
    lokalnego, status projektu. Sekcja ze zrzutami ekranu zakomentowana — czeka na pliki.

## Czego się nauczyliśmy

- **Deploy to trzy różne rodzaje rzeczy**: statyczne pliki (CDN), żywy proces (PaaS)
  i stan, którego nie wolno zgubić (baza). Stąd trzy usługi, a nie jedna.
- **Konfiguracja ≠ kod.** To, co różni się między środowiskami (adres frontendu, adres
  bazy, port), musi przyjeżdżać ze zmiennych środowiskowych. Inaczej każda zmiana
  wymaga commita i przebudowy.
- **`$PORT` i `0.0.0.0`** — hosting narzuca port, a proces musi słuchać na wszystkich
  interfejsach, nie na `127.0.0.1`.
- **Migracje w komendzie startowej** są idempotentne (`upgrade head` na aktualnej bazie
  nic nie robi), a `&&` gwarantuje, że serwer nie wstanie na zepsutym schemacie.
- **Klasa błędów „działa lokalnie, wywala się na produkcji"**: lokalny PostgreSQL nigdy
  nie zasypia, więc `pool_pre_ping` jest niepotrzebny — aż do pierwszego deployu.
- **Klucze obce dyktują kolejność przy przenoszeniu danych.** `pg_dump` sam tego nie
  ułoży; dziecko nie może istnieć przed rodzicem.
- **Testowanie z zewnątrz jest inne niż testowanie u siebie.** Dwa najpoważniejsze błędy
  tej sesji (SSO Vercela, 404 na głębokich linkach) były **niewidoczne** w przeglądarce
  właściciela. `curl` bez sesji i bez cache widzi to, co zobaczy obca osoba.
- **Sekrety w warstwie frontendu nie istnieją.** Wszystko, co Vite wkompiluje, jedzie do
  przeglądarki — stąd prefiks `VITE_` jako jawna deklaracja „to jest publiczne".
- **`secrets.compare_digest` zamiast `==`** przy porównywaniu tokenów (stały czas,
  brak wycieku informacji przez czas odpowiedzi); `secrets` ≠ `random` (ten drugi jest
  przewidywalny — świetny do Monte Carlo w Fazie 4, nieużywalny do sekretów).
- **Ochrona „domyślnie włączona"**: zależność podpięta do routera, a nie do trzech
  endpointów, chroni też te, które dopiero powstaną.
- **Darmowe plany trzeba weryfikować na bieżąco** — warunki Rendera, Railway, Fly
  i Koyeba zmieniły się w ciągu ostatniego roku. Ukryta pułapka (30-dniowa baza)
  kosztowałaby działające demo w środku rekrutacji.

## Stan repo po sesji

- **Backend**: `app/security.py` (NOWY), zmiany w `config.py` (walidator, `IMPORT_TOKEN`,
  `ALLOWED_ORIGINS` + property), `main.py` (CORS z env, angielski komunikat),
  `database.py` (pula), `routers/imports.py` (zależność na routerze).
- **Deployment**: `Procfile` (NOWY), `.python-version` (NOWY), `frontend/vercel.json`
  (NOWY).
- **Dokumentacja**: `README.md` (NOWY, 186 linii), `instructions/sessions/README.md`
  (NOWY), 5 dokumentów `instructions/` przetłumaczonych, `CLAUDE.md` po angielsku,
  nagłówki w całym kodzie.
- **Usunięte**: `frontend/src/App.css` (martwy plik z szablonu Vite).
- **Jakość**: pytest **19/19**, Ruff czysty, oxlint **0/0**, `tsc` czysty,
  `npm run build` zielony.
- **Produkcja**: leagues 15, teams **1977**, standings 572, fixtures **8213**.
- **API-Football**: ~21 zapytań (odświeżenie danych). Subskrypcja Pro wygasa
  **1 października 2026**.

## Długi techniczne

- **Brak trasy `*` w React Routerze** — po dodaniu rewrite'u każda nieistniejąca ścieżka
  zwraca `index.html` i pokazuje nagłówek nad pustką. Potrzebna strona 404 z linkiem
  do startu.
- **Zrzuty ekranu do README** — sekcja czeka zakomentowana na `docs/screenshots/*.png`.
- **Hasło do bazy** nie zostało zrotowane (świadoma decyzja właściciela).
- **Te same sekrety lokalnie i na produkcji** — docelowo środowiska nie powinny dzielić
  wartości.
- Z poprzednich sesji: `TeamSelect` (duplikacja dwóch selektów w `PredictPage`),
  selektory elementów w `index.css` bijące utilki Tailwinda, loading state drużyn.

## TODO na Sesję 20

> Deploy zamknięty, wracamy do funkcji. Kolejność wg ROADMAP po przenumerowaniu.
1. **Zrzuty ekranu do README** + odkomentowanie sekcji (5 minut, duży efekt wizualny).
2. **Strona 404** (trasa `*` w `App.tsx`) — domknięcie długu z rewrite'u Vercela.
3. **Faza 4, Monte Carlo (backend)**: symulacja pojedynczego meczu przez losowanie
   z rozkładów Poissona (`numpy.random.poisson`), potem symulacja pozostałych meczów
   sezonu × 1000 iteracji od aktualnej tabeli → % szans na mistrzostwo / top 4 / spadek.
4. (jeśli zostanie czas) **GitHub Actions**: CI z `ruff check` + `pytest` przy każdym
   pushu — mały koszt, dobrze wygląda w repo.

## Praca domowa

> Sesja 20 to powrót do matematyki, ale innej niż w Fazie 3: tam liczyliśmy
> prawdopodobieństwa wzorem, tu będziemy je **szacować przez losowanie**.

### 🔴 Priorytet 1 — metoda Monte Carlo
1. **Czym jest symulacja Monte Carlo** — poszukaj wyjaśnienia na prostym przykładzie
   (klasyk: szacowanie liczby π przez losowanie punktów w kwadracie). Zwróć uwagę na
   **główną ideę**: zamiast liczyć prawdopodobieństwo wzorem, powtarzamy losowy
   eksperyment tysiące razy i liczymy, jak często dany wynik wypadł. Pytanie do
   przemyślenia: dlaczego przy symulacji **całego sezonu** wzór by nie wystarczył?
   (podpowiedź: 380 meczów, każdy wpływa na tabelę, a interesuje nas rozkład **pozycji
   końcowych**, nie pojedynczego meczu).
2. **`numpy.random.poisson`** —
   [dokumentacja](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.poisson.html).
   To będzie nasze narzędzie: mając λ z `strength.py`, losujemy liczbę goli zamiast
   liczyć prawdopodobieństwo każdego wyniku. Zwróć uwagę na parametr `size` — pozwala
   wylosować od razu **całą tablicę** wyników jednym wywołaniem.

### 🟡 Priorytet 2 — wektoryzacja (wydajność)
3. **Dlaczego w numpy unika się pętli po elementach** — poszukaj hasła „numpy
   vectorization". 1000 symulacji × 380 meczów to 380 000 losowań; w pętli Pythona
   potrwa to sekundy, w jednej operacji na tablicy — milisekundy. Zwróć uwagę na to,
   **dlaczego** tak jest (operacje wykonuje skompilowany kod C, nie interpreter).

### 🟢 Priorytet 3 — CI (jeśli wejdzie punkt 4)
4. **GitHub Actions — podstawy** —
   [dokumentacja](https://docs.github.com/en/actions/writing-workflows/quickstart).
   Zwróć uwagę na strukturę pliku `.github/workflows/*.yml`: `on` (kiedy się uruchamia),
   `jobs`, `steps`. Nasz workflow będzie prosty: zainstaluj Pythona, zainstaluj paczki,
   odpal `ruff check` i `pytest`.
