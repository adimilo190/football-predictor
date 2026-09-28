// src/api/predictions.ts
// API layer for the predictor: the types mirroring the backend's PredictionResponse
// plus the call to GET /predict.
//
// Watch the naming split here. The QUERY KEYS in the URL must be spelled exactly
// as the backend names them (home_id, away_id, league_id) - they physically travel
// in the URL, and a mismatch is an instant 422. The JS parameters (homeId, awayId)
// are local names and follow the TypeScript convention instead.

import { API_BASE_URL } from "./config";

export type ScoreLine = {
  home_goals: number;
  away_goals: number;
  probability: number;
};

export type Prediction = {
  home_win: number;
  draw: number;
  away_win: number;
  top_scores: ScoreLine[];
};

export async function getPrediction(
  homeId: number,
  awayId: number,
  leagueId: number,
  season: number,
): Promise<Prediction> {
  const res = await fetch(
    `${API_BASE_URL}/predict?home_id=${homeId}&away_id=${awayId}&league_id=${leagueId}&season=${season}`,
  );
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
