import { API_BASE_URL } from "./config";

// These types describe the shape of the standings API response. They live in the
// API layer (not the component) because they model server data, not the UI.
export type Team = {
  id: number;
  name: string;
  country: string | null;
  logo_url: string | null;
};

export type Standing = {
  rank: number;
  team: Team;
  played: number;
  wins: number;
  draws: number;
  losses: number;
  points: number;
  goals_for: number;
  goals_against: number;
  form: string | null;
};

// Fetch the standings table for a single league.
// Returns the rows on success. Throws on a non-OK response so that TanStack Query
// treats it as an error: fetch only rejects on network failures, never on 4xx/5xx.
export async function getStandings(leagueId: string): Promise<Standing[]> {
  const res = await fetch(`${API_BASE_URL}/leagues/${leagueId}/standings`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
