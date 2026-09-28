// src/api/teams.ts
// API layer for everything about a single team: recent results, upcoming matches
// and the name search. Types are reused from the other API modules (Team, Fixture)
// with "import type", because the backend returns the very same shapes here - one
// definition per concept, not a copy per file.

import { API_BASE_URL } from "./config";
import type { Team } from "./standings";
import type { Fixture } from "./bracket";

export async function getPastMatches(teamId: string): Promise<Fixture[]> {
  const res = await fetch(`${API_BASE_URL}/teams/${teamId}/past-matches`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function getFutureMatches(teamId: string): Promise<Fixture[]> {
  const res = await fetch(`${API_BASE_URL}/teams/${teamId}/future-matches`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function searchTeams(searchTerm: string): Promise<Team[]> {
  // encodeURIComponent escapes whatever the user typed: spaces, "&", "?" and
  // accents would otherwise break the query string or be read as extra params.
  const res = await fetch(
    `${API_BASE_URL}/teams?search=${encodeURIComponent(searchTerm)}`,
  );
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
