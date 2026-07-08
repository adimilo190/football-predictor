# app/constants.py
# Fixed identifiers of the competitions this project tracks (Phase 1).
# The keys are API-Football league ids; the values are human-readable labels
# kept only so the code documents itself — the logic uses the keys.

TARGET_LEAGUE_IDS: dict[int, str] = {
    # Top divisions of the 6 tracked countries.
    39: "Premier League (England)",
    140: "La Liga (Spain)",
    135: "Serie A (Italy)",
    78: "Bundesliga (Germany)",
    61: "Ligue 1 (France)",
    94: "Primeira Liga (Portugal)",
    # Domestic cups of those countries.
    45: "FA Cup (England)",
    143: "Copa del Rey (Spain)",
    137: "Coppa Italia (Italy)",
    81: "DFB Pokal (Germany)",
    66: "Coupe de France (France)",
    96: "Taca de Portugal (Portugal)",
    # European competition.
    2: "UEFA Champions League",
}
