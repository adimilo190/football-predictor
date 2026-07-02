# Sesja 1 — 2 lipca 2026

## Co zostało zrobione
1. **Audyt projektu** — analiza założeń (`project-assumptions.md`), stacku (`tools.md`), postępów (`progres.md`) i istniejącego kodu (`main.py`, `database.py`, `models.py`). Werdykt: stack bardzo dobry, kod działa, ale były 2 poważne problemy bezpieczeństwa (patrz niżej).
2. **Bezpieczeństwo — sekrety wyniesione z kodu:**
   - Klucz API-Football był na sztywno w `main.py`, hasło do bazy w `database.py`. Gdyby to trafiło na GitHuba, byłoby publiczne.
   - Utworzono `.env` (prawdziwe wartości, zostaje lokalnie) i `.env.example` (wzór, idzie do gita).
   - Kod czyta teraz sekrety przez `python-dotenv` → `os.getenv(...)`.
3. **`.gitignore`** — wykluczono: `venv/`, `__pycache__/`, `.env`, `node_modules/` (na przyszłość), `.claude/settings.local.json`.
4. **`requirements.txt`** — zamrożona lista paczek (`pip freeze`), żeby projekt dał się odtworzyć na innym komputerze.
5. **Smoke test** — `import main` przechodzi: aplikacja startuje i łączy się z bazą przez `.env`. ✅
6. **Dokumentacja i plan:**
   - `instructions/ROADMAP.md` — szczegółowy plan 24 sesji do 30 września (bloki, kamienie milowe, ryzyka).
   - `CLAUDE.md` — zasady współpracy (tryb nauki, rytuał końca sesji, szczegóły środowiska WSL).
   - Ten log + aktualizacja `progres.md` + uzupełnienia w `tools.md`.
7. **Git:** zmiana gałęzi `master` → `main` (standard GitHuba), pierwszy commit.

## Decyzje (i dlaczego)
- **Zostajemy przy API-Football NA RAZIE** — ale w Sesji 3 obowiązkowo weryfikujemy, czy darmowy plan daje tabele bieżącego sezonu. Plan B: football-data.org. Dane do ML: football-data.co.uk (CSV bez limitów).
- **Ulubione drużyny bez logowania (localStorage)** — konta użytkowników (JWT) to stretch goal. MVP ma być skończony, nie idealny.
- **Dodajemy do stacku:** Alembic (migracje), pytest (testy), Ruff (lint), Vite (build frontendu), TanStack Query (fetch), pydantic-settings (konfiguracja), GitHub Actions (CI na koniec). Uzasadnienia w `tools.md`.
- **Commity po angielsku** — repo będzie w CV, tak wygląda profesjonalnie.

## Czego się nauczyliśmy (do utrwalenia!)
- **`.env` + `.gitignore`**: sekrety nigdy nie idą do repozytorium. `python-dotenv` wczytuje plik `.env` do zmiennych środowiskowych, a kod czyta je przez `os.getenv()`. Wzór dla innych: `.env.example`.
- **`requirements.txt`**: `pip freeze > requirements.txt` zapisuje dokładne wersje paczek; `pip install -r requirements.txt` odtwarza środowisko.
- **git — pierwsze kroki**: `git add` (poczekalnia), `git commit` (zapis migawki), gałąź `main`, `git remote` + `git push` (wysyłka na GitHub).

## TODO na start Sesji 2
1. **[TY — zadanie domowe]** Załóż repo na GitHubie i wypchnij kod:
   - Wejdź na https://github.com/new (konto: adimilo190)
   - Nazwa: `football-predictor`, **Private** (upublicznisz, gdy README będzie robić wrażenie), **bez** zaznaczania "Add README/.gitignore" (mamy własne!)
   - Potem w terminalu WSL:
     ```bash
     cd ~/football-predictor
     git remote add origin https://github.com/adimilo190/football-predictor.git
     git push -u origin main
     ```
   - Git poprosi o login i hasło → jako hasła użyj **Personal Access Token** (GitHub → Settings → Developer settings → Personal access tokens → Generate new token (classic), zaznacz zakres `repo`).
2. **[SESJA 2]** Restrukturyzacja backendu do pakietu `app/` + pydantic-settings + schematy Pydantic + Ruff (szczegóły w ROADMAP).

## Stan repo po sesji
- Gałąź `main`, 1 commit, remote jeszcze nie ustawiony (czeka na założenie repo — punkt 1 powyżej).
