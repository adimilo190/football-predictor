# Football Predictor — zasady współpracy

## Kontekst
Projekt portfolio (CV) — aplikacja webowa do śledzenia rozgrywek piłkarskich z predykcją wyników i ML.
Założenia: `instructions/project-assumptions.md`. Stack: `instructions/tools.md`. Plan: `instructions/ROADMAP.md`.
Deadline: koniec września 2026.

## TRYB NAUKI (najważniejsza zasada)
Właściciel projektu dopiero uczy się używanych narzędzi (FastAPI, React, TS, SQL, git, ML...).
- Odpowiadaj **po polsku**.
- Przy każdym nowym narzędziu/koncepcie: krótko wytłumacz **co to jest, po co i jak działa** — zanim go użyjesz.
- Kod pisz z pomocnymi komentarzami po polsku (jak w istniejących plikach).
- Nie rób wszystkiego za użytkownika hurtem — pracuj etapami, tłumacząc decyzje. Preferuj małe kroki, które da się zrozumieć.

## Rytuał końca sesji (OBOWIĄZKOWY)
1. Napisz log `instructions/sessions/session-NN.md`: co zrobiono, jakie decyzje i dlaczego, czego się nauczyliśmy, dokładne TODO na następną sesję.
2. Zaktualizuj statusy w `instructions/ROADMAP.md` i dopisz sekcję w `instructions/progres.md`.
3. Commit (message po angielsku, opisowy) + push na GitHub.

## Środowisko (ważne szczegóły techniczne)
- Kod żyje w WSL: `/home/micmilo190/football-predictor` (z Windows: `\\wsl.localhost\ubuntu\home\micmilo190\football-predictor`).
- **Git i Python uruchamiaj W ŚRODKU WSL**, np.:
  `wsl.exe -d ubuntu -e sh -c "cd /home/micmilo190/football-predictor && git status"`
  (git z Windows na ścieżce UNC rzuca błędem "dubious ownership" i jest wolny).
- venv: `venv/` (Python 3.10) — używaj `venv/bin/python`, `venv/bin/pip`.
- PostgreSQL działa w WSL (localhost:5432, baza `football_db`).
- Sekrety w `.env` (NIE commitować!). Wzór: `.env.example`. Po dodaniu nowej zmiennej — zaktualizuj `.env.example`.
- Po instalacji paczek: `venv/bin/pip freeze > requirements.txt`.

## Konwencje
- Backend: FastAPI + SQLAlchemy + PostgreSQL; frontend (od Bloku 2): React + TypeScript + Vite + Tailwind w folderze `frontend/`.
- Commity po angielsku, kod i komentarze mogą być po polsku.
- Testy: pytest w `tests/` (od Sesji 5).
- Zmiany schematu bazy: przez migracje Alembic (od Sesji 3), nie przez ręczne DROP/CREATE.
