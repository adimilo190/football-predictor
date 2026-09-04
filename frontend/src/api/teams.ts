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
  const res = await fetch(
    `${API_BASE_URL}/teams?search=${encodeURIComponent(searchTerm)}`,
  );
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
