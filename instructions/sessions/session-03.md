# Sesja 3 — 8 lipca 2026

## Co zostało zrobione
1. **Alembic zainstalowany i skonfigurowany** — `alembic init alembic`; w `alembic/env.py`: adres bazy brany z `settings.DATABASE_URL` (nadpisanie `sqlalchemy.url` w locie — hasło nie trafia do plików w gicie), `target_metadata = Base.metadata`, import `app.models` dla efektu ubocznego rejestracji tabel (`# noqa: F401`).
2. **Migracja bazowa (czysty start)** — istniejąca tabela `leagues` (z 46 testowymi ligami UK) skasowana; migracja `create leagues table` wygenerowana przez `--autogenerate` i wykonana `alembic upgrade head`. Historia migracji buduje bazę od zera.
3. **`create_all` usunięty z `app/main.py`** — od teraz schematem bazy zarządza WYŁĄCZNIE Alembic (jeden właściciel schematu). W bazie doszła tabelka `alembic_version` (aktualna wersja migracji).
4. **Modele `Team` i `Standing`** w `app/models.py`:
   - `Team`: id z API-Football jako PK; celowo BEZ `league_id` (drużyna gra w wielu rozgrywkach naraz — relacja wiele-do-wielu przez `standings`),
   - `Standing`: własny autoinkrementowany PK, `ForeignKey` do `leagues.id` i `teams.id` (`nullable=False`), `season` jako rok startowy (konwencja API-Football: 2024 = 2024/25), statystyki tabeli, `form` (np. "WWDLW"), `UniqueConstraint(league_id, team_id, season)` — blokada duplikatów przy wielokrotnym imporcie,
   - `relationship` + `back_populates` po obu stronach (nawigacja w Pythonie: `standing.team.name`, `league.standings`).
5. **Druga migracja** `add teams and standings tables` — wygenerowana, przejrzana (kolejność: `teams` przed `standings` przez FK), wykonana. Łańcuch migracji działa (`down_revision` wskazuje na poprzednika).
6. **`app/constants.py`** — `TARGET_LEAGUE_IDS`: 13 śledzonych rozgrywek (6 lig + 6 pucharów krajowych + Liga Mistrzów) jako dict id → czytelna nazwa.
7. **Przebudowa `/import-leagues`**: `GET` → `POST` (endpoint modyfikuje bazę — REST), jedno zapytanie o pełną listę lig + filtr lokalny po `TARGET_LEAGUE_IDS` (1 zapytanie zamiast 13 przy limicie 100/dzień), odpowiedź zwraca listę nazw zaimportowanych rozgrywek (weryfikowalność ID).
8. **Import wykonany i zweryfikowany** — 13/13 rozgrywek w bazie, nazwy zgodne z planem; `/my-leagues` zwraca je przez schemat Pydantic. Weryfikacja przez `TestClient` (bez uruchamiania uvicorna).
9. `FastAPI(title="Football Predictor API")` — tytuł w Swagger UI.
10. Ruff format + check czyste; `requirements.txt` zaktualizowany (alembic, Mako, tomli).

## Decyzje (i dlaczego)
- **Baseline Alembica = czysty start (DROP + migracja), nie `stamp head`** — dane były testowe i do wyrzucenia; zysk: `alembic upgrade head` odtwarza całą bazę od zera po sklonowaniu repo. `stamp head` to wzorzec dla produkcji z danymi, u nas byłby sztuczny.
- **`Team` bez przypisania do ligi** — Real gra w La Liga + Puchar Króla + LM jednocześnie; łącznikiem drużyna↔rozgrywki jest tabela `standings`.
- **ID rozgrywek w `app/constants.py`, nie w `config.py`** — to logika biznesowa (stała wszędzie), nie konfiguracja środowiskowa (per maszyna). Osobny plik, bo ID będą reużyte przy standings (S4) i fixtures (S6).
- **Punkty ROADMAP „test standings 2025/26+" i „decyzja o źródle"** — już rozstrzygnięte wcześniej: limity zweryfikowane w Sesji 1 (tylko 2022–2024), decyzja o źródle danych żywych odłożona do startu Fazy 2 (decyzja właściciela z 2 lip).
- **NOWA ZASADA WSPÓŁPRACY (feedback właściciela):** jeden punkt planu naraz → wyjaśnienie co się zmieniło → pytanie czy iść dalej. Nie robić całego TODO sesji hurtem. Zapisana w `CLAUDE.md` (TRYB NAUKI) i pamięci Claude.

## Czego się nauczyliśmy (do utrwalenia!)
- **Migracje bazy (Alembic)**: dlaczego `create_all` nie wystarcza (nie zmienia istniejących tabel); migracja = wersjonowana zmiana schematu; łańcuch `revision`/`down_revision` jak commity; `alembic_version` = zakładka w bazie; workflow: zmień modele → `revision --autogenerate` → PRZECZYTAJ plik → `upgrade head`; autogenerate ma ślepe punkty (np. rename kolumny widzi jako drop+add).
- **Klucz obcy (`ForeignKey`)**: kolumna wskazująca wiersz innej tabeli + spójność egzekwowana przez bazę (nie zapiszesz standing dla nieistniejącej ligi).
- **`relationship` vs `ForeignKey`**: FK = fizyczna kolumna w bazie; relationship = nawigacja tylko w Pythonie (`standing.team.name`); `back_populates` spina obie strony.
- **`UniqueConstraint`**: reguła unikalności na kombinacji kolumn — chroni przed duplikatami przy powtarzanym imporcie; wymusi upsert w Sesji 4.
- **Relacja wiele-do-wielu**: przez tabelę pośrednią (u nas `standings` łączy `teams` i `leagues`).
- **REST: GET vs POST**: GET ma być „bezpieczny" (read-only); akcje zmieniające stan = POST.
- **Limity API**: jedno tanie zapytanie + filtr po swojej stronie zamiast N drogich zapytań.
- **`TestClient`**: wywoływanie endpointów w procesie Pythona bez serwera — fundament testów pytest (Sesja 5).
- **Import dla efektu ubocznego**: modele rejestrują się w `Base.metadata` w momencie importu; `# noqa: F401` uzasadnia „nieużywany" import.

## TODO na start Sesji 4 (Import tabel lig — ETL)
1. Import **standings** dla 6 lig, sezon **2024** (2024/25 — najnowszy dostępny na darmowym planie): endpoint `standings?league={id}&season=2024` (6 zapytań), zapis drużyn do `teams` i wpisów do `standings`.
2. **Upsert** — aktualizacja istniejących wierszy zamiast wstawiania duplikatów (`UniqueConstraint uq_standing` to wymusi).
3. Strategia limitów (100 zapytań/dzień): dane trzymamy u siebie; odświeżanie świadome (endpoint admina lub skrypt).
4. Obsługa błędów HTTP z zewnętrznego API (status ≠ 200, pusta odpowiedź).
5. (opcjonalnie) schematy Pydantic dla Team/Standing; routery gdy endpointów przybędzie.
6. **PAMIĘTAĆ: nowy rytm pracy** — jeden krok naraz, wyjaśnienie, pytanie o zgodę na następny.

## Stan repo po sesji
- Gałąź `main`. Nowe: `alembic/` (2 migracje), `alembic.ini`, `app/constants.py`. Zmienione: `app/main.py` (bez `create_all`, POST import z filtrem), `app/models.py` (Team, Standing), `CLAUDE.md` (rytm pracy), `requirements.txt`.
- Baza: tabele `leagues` (13 rozgrywek), `teams` (pusta), `standings` (pusta), `alembic_version` (= head).
- Ruff czysty, smoke test OK, import zweryfikowany end-to-end.
