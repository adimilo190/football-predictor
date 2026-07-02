# Stack Technologiczny i Narzędzia

## Frontend (Interfejs użytkownika)
* **Język:** TypeScript (nadbudowa na JavaScript wymuszająca typowanie)[cite: 1].
* **Framework:** React.js (do budowy dynamicznej aplikacji SPA)[cite: 1].
* **Stylowanie:** Tailwind CSS (nowoczesne i szybkie stylowanie komponentów)[cite: 1].

## Backend (Logika biznesowa i API)
* **Język:** Python[cite: 1].
* **Framework:** FastAPI (nowoczesny i szybki framework webowy)[cite: 1].
* **Narzędzia pomocnicze:**
  * `httpx`: do asynchronicznej komunikacji z zewnętrznym API-Football[cite: 1].
  * `SQLAlchemy`: biblioteka ORM do zarządzania bazą danych bez surowych zapytań SQL[cite: 1].

## Baza Danych
* **Silnik:** PostgreSQL (relacyjna baza danych, osadzona w środowisku WSL/Linux)[cite: 1].

## Machine Learning & Data Science (Planowane na Fazy 4 i 5)
* **Przetwarzanie danych:** Pandas (obróbka dużych tabel z danymi historycznymi)[cite: 1].
* **Uczenie maszynowe:** Scikit-learn (tworzenie modeli AI, np. Random Forest, regresja logistyczna)[cite: 1].

## Narzędzia DevOps i Organizacja
* **Kontrola wersji:** Git & GitHub[cite: 1].
* **Testowanie API:** Postman[cite: 1].
* **Środowisko Python:** Virtualenv (venv) do izolacji paczek[cite: 1].
* **Edytor kodu:** VS Code (wyposażony w rozszerzenie SQLTools do podglądu bazy danych)[cite: 1].

---

## Uzupełnienia po przeglądzie stacku (Sesja 1, 2026-07-02)
Stack bazowy oceniony jako bardzo dobry i zgodny ze standardami branżowymi. Dodajemy:

* **python-dotenv → potem pydantic-settings** — sekrety i konfiguracja w `.env`, nigdy w kodzie. *(już wdrożone)*
* **Vite** — standardowe narzędzie budowania aplikacji React (szybki dev-server, prosty setup TS).
* **Alembic** — migracje schematu bazy; `create_all` tworzy tabele, ale nie umie ich zmieniać (od Sesji 3).
* **pytest** — testy automatyczne backendu; duży plus w CV (od Sesji 5).
* **Ruff** — bardzo szybki linter+formatter Pythona (standard 2025/26).
* **TanStack Query** — profesjonalne pobieranie danych w React (cache, stany ładowania/błędów) (Blok 2).
* **GitHub Actions** — proste CI (lint + testy przy każdym pushu); mały koszt, duży efekt w CV (Sesja 24).
* **Uwaga do Postmana:** FastAPI ma wbudowane interaktywne `/docs` (Swagger UI) — na co dzień wystarcza; Postman warto poznać przy okazji.
* **Ryzyko API-Football:** darmowy plan = 100 zapytań/dzień i możliwy brak danych bieżącego sezonu — weryfikacja w Sesji 3. Plan B: **football-data.org** (darmowo: nasze 6 lig + Liga Mistrzów, bieżący sezon; bez pucharów krajowych). Dane historyczne do ML: **football-data.co.uk** (CSV, bez limitów).
* **Stretch (jeśli będzie czas):** Docker + docker-compose, deploy (Railway/Render + Vercel), auth JWT.