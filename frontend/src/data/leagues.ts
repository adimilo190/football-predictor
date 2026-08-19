// --- Navigation model (Session 12): countries and their competitions --------
// HomePage groups competitions by country: a top-division LEAGUE (shown as a
// standings table) and a domestic CUP (shown as a knockout bracket). European
// cups are supranational, so they live in their own list. All ids are
// API-Football competition ids (mirror of app/constants.py on the backend).

export type Competition = { id: number; name: string };

export type Country = {
  name: string;
  league: Competition; // top division -> table  (/leagues/:id)
  cup: Competition; // domestic cup  -> bracket (/bracket/:id)
};

export const COUNTRIES: Country[] = [
  {
    name: "England",
    league: { id: 39, name: "Premier League" },
    cup: { id: 45, name: "FA Cup" },
  },
  {
    name: "Spain",
    league: { id: 140, name: "La Liga" },
    cup: { id: 143, name: "Copa del Rey" },
  },
  {
    name: "Italy",
    league: { id: 135, name: "Serie A" },
    cup: { id: 137, name: "Coppa Italia" },
  },
  {
    name: "Germany",
    league: { id: 78, name: "Bundesliga" },
    cup: { id: 81, name: "DFB Pokal" },
  },
  {
    name: "France",
    league: { id: 61, name: "Ligue 1" },
    cup: { id: 66, name: "Coupe de France" },
  },
  {
    name: "Portugal",
    league: { id: 94, name: "Primeira Liga" },
    cup: { id: 96, name: "Taça de Portugal" },
  },
];

// European cups are shown as brackets (/bracket/:id), just like domestic cups.
export const EUROPEAN_COMPETITIONS: Competition[] = [
  { id: 2, name: "Champions League" },
  { id: 3, name: "Europa League" },
  { id: 848, name: "Conference League" },
];
