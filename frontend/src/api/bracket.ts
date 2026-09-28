// src/api/bracket.ts
// API layer for cup competitions, in two parts:
//   1. types + getBracket() - the rounds and matches as the backend sends them;
//   2. groupIntoMatchups()  - reshaping those matches into the pairs a tournament
//      tree needs (see the section comment further down).
// The reshaping lives here rather than in the component because it is data work,
// not rendering: the Bracket component only draws whatever comes out of it.

import type { Team } from "./standings";
import { API_BASE_URL } from "./config";

export type Fixture = {
  id: number;
  round: string | null;
  date: string;
  status: string | null;
  home_goals: number | null;
  away_goals: number | null;
  home_team: Team;
  away_team: Team;
};

export type BracketRound = { round: string; fixtures: Fixture[] };

export async function getBracket(
  leagueId: string,
  season: number,
  knockoutOnly = true,
): Promise<BracketRound[]> {
  const res = await fetch(
    `${API_BASE_URL}/leagues/${leagueId}/bracket?knockout_only=${knockoutOnly}&season=${season}`,
  );
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// --- Bracket shaping: group a round's fixtures into matchups ----------------
// A two-legged tie (home + away) arrives as TWO fixtures with the teams
// swapped. For a tournament tree we want ONE node per tie, so we group both
// legs and pin the two teams, expressing each leg's score from the same side.

export type Matchup = {
  teamTop: Team;
  teamBottom: Team;
  // One entry per leg: 1 for a single-leg cup, 2 for a home-and-away tie.
  // Ordered as the legs were played (fixtures come date-sorted from the API).
  legs: { topGoals: number | null; bottomGoals: number | null; date: string }[];
};

export function groupIntoMatchups(fixtures: Fixture[]): Matchup[] {
  // Bucket fixtures by the UNORDERED pair of team ids, so leg 1 (A vs B) and
  // leg 2 (B vs A) land in the same bucket. Sorting the two ids makes the key
  // identical regardless of who played at home.
  const byPair = new Map<string, Fixture[]>();
  for (const fx of fixtures) {
    const key = [fx.home_team.id, fx.away_team.id]
      .sort((a, b) => a - b)
      .join("-");
    const bucket = byPair.get(key);
    if (bucket) {
      bucket.push(fx);
    } else {
      byPair.set(key, [fx]);
    }
  }

  // Turn each bucket into a matchup. Fix the two teams from the first leg, then
  // map every leg's goals onto them — in the return leg the teams are swapped,
  // so we flip home/away goals to keep them attached to the same team.
  const matchups: Matchup[] = [];
  for (const legs of byPair.values()) {
    const teamTop = legs[0].home_team;
    const teamBottom = legs[0].away_team;
    const legResults = legs.map((leg) => {
      const topIsHome = leg.home_team.id === teamTop.id;
      return {
        topGoals: topIsHome ? leg.home_goals : leg.away_goals,
        bottomGoals: topIsHome ? leg.away_goals : leg.home_goals,
        date: leg.date,
      };
    });
    matchups.push({ teamTop, teamBottom, legs: legResults });
  }
  return matchups;
}
