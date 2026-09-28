// src/api/standings.ts
// API layer for league tables: the types mirroring what the backend returns, plus
// the functions that fetch them. Components never call fetch themselves - they
// hand these functions to useQuery, so all knowledge about URLs, query params and
// response shapes lives in this one folder.

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
export async function getStandings(
  leagueId: string,
  season: number,
): Promise<Standing[]> {
  const res = await fetch(
    `${API_BASE_URL}/leagues/${leagueId}/standings?season=${season}`,
  );
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function getSeasons(leagueId: string): Promise<number[]> {
  const res = await fetch(`${API_BASE_URL}/leagues/${leagueId}/seasons`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
