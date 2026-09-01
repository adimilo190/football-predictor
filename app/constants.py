# app/constants.py
# Fixed identifiers of the competitions this project tracks (Phase 1).
# The keys are API-Football league ids; the values are human-readable labels
# kept only so the code documents itself — the logic uses the keys.

# The season Phase 1 is built on, stored as its starting year (2024 = 2024/25).
# The API-Football free plan only serves seasons 2022-2024 (verified in
# Session 1), so this is the newest season available to us.
DEFAULT_SEASON: int = 2024

# Top divisions of the 6 tracked countries. These have a classic league table,
# so they are the source for the standings import (Session 4).
DOMESTIC_LEAGUE_IDS: dict[int, str] = {
    39: "Premier League (England)",
    140: "La Liga (Spain)",
    135: "Serie A (Italy)",
    78: "Bundesliga (Germany)",
    61: "Ligue 1 (France)",
    94: "Primeira Liga (Portugal)",
}

# Domestic cups of those countries — knockout format, no league table
# (bracket data comes in Session 6 via the fixtures endpoint).
DOMESTIC_CUP_IDS: dict[int, str] = {
    45: "FA Cup (England)",
    143: "Copa del Rey (Spain)",
    137: "Coppa Italia (Italy)",
    81: "DFB Pokal (Germany)",
    66: "Coupe de France (France)",
    96: "Taca de Portugal (Portugal)",
}

# European competitions.
EUROPEAN_COMPETITION_IDS: dict[int, str] = {
    2: "UEFA Champions League",
    3: "UEFA Europa League",
    848: "UEFA Conference League",
}

# Everything the project tracks, in one place. The ** operator unpacks each
# dict into this new one (a merge), so this stays in sync with the groups above
# automatically — add a competition to its group and it shows up here too.
TARGET_LEAGUE_IDS: dict[int, str] = {
    **DOMESTIC_LEAGUE_IDS,
    **DOMESTIC_CUP_IDS,
    **EUROPEAN_COMPETITION_IDS,
}

# Knockout rounds of a cup competition. Used to filter the bracket endpoint, so
# we only return rounds that are actually part of the knockout stage. It is a set
# (unordered): the bracket's column order comes from the date sort, not from here.
KNOCKOUT_ROUNDS: set[str] = {
    "Round of 64",
    "Round of 32",
    "Round of 16",
    "Quarter-finals",
    "Semi-finals",
    "Final",
}

# Fixture statuses that count as "played with a final result": full time,
# after extra time (AET), penalties (PEN). The team results endpoint filters on
# these to keep out scheduled, postponed, cancelled or in-progress matches.
FINISHED_STATUSES: set[str] = {"FT", "AET", "PEN"}
