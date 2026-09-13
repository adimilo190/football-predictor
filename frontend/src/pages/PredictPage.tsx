// Prediction page: pick a league, then two teams from it, and show the Poisson
// model's 1/X/2 outcome plus the most likely scorelines.

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { COUNTRIES } from "../data/leagues";
import { getStandings } from "../api/standings";
import { getPrediction } from "../api/predictions";
import PredictionResult from "../components/PredictionResult";

// Only league competitions have a standings table, which is what the Poisson
// model needs — so the predictor picks teams from a league, never a cup.
const leagues = COUNTRIES.map((country) => country.league);

// Baseline uses the last completed season: full ~38-round data = stable team
// strengths. Blending seasons is a model #2 (Dixon-Coles) feature, planned later.
const PREDICTION_SEASON = 2025;

function PredictPage() {
  const [leagueId, setLeagueId] = useState<number | null>(null);
  const [homeId, setHomeId] = useState<number | null>(null);
  const [awayId, setAwayId] = useState<number | null>(null);

  // Teams for the two pickers come from the chosen league's standings table.
  // `enabled` skips the request until a league is picked, so we never call the
  // API with a null id.
  const { data: standings } = useQuery({
    queryKey: ["standings", leagueId, PREDICTION_SEASON],
    queryFn: () => getStandings(String(leagueId), PREDICTION_SEASON),
    enabled: leagueId !== null,
  });

  // Turn standings rows into a plain team list for the <option>s. `?? []` keeps
  // it an array while data is still loading or no league is chosen yet.
  const teams = standings?.map((standing) => standing.team) ?? [];

  // The two chosen teams, looked up by id — used for the result labels.
  const homeTeam = teams.find((team) => team.id === homeId);
  const awayTeam = teams.find((team) => team.id === awayId);

  // The prediction itself. Runs only once BOTH teams are chosen and they differ
  // (a team can't play itself). The `!` tells TypeScript these aren't null here,
  // which `enabled` guarantees at runtime.
  const {
    data: prediction,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["prediction", leagueId, homeId, awayId, PREDICTION_SEASON],
    queryFn: () => getPrediction(homeId!, awayId!, leagueId!, PREDICTION_SEASON),
    enabled: homeId !== null && awayId !== null && homeId !== awayId,
  });

  return (
    <div className="max-w-2xl mx-auto p-4">
      <h2>Predict a match</h2>
      <div className="flex flex-col gap-2">
        <select
          value={leagueId ?? ""}
          onChange={(e) => {
            setLeagueId(Number(e.target.value));
            // Teams from the old league no longer apply — reset both picks.
            setHomeId(null);
            setAwayId(null);
          }}
          className="border rounded px-2 py-1"
        >
          <option value="" disabled>
            Select a league
          </option>
          {leagues.map((league) => (
            <option key={league.id} value={league.id}>
              {league.name}
            </option>
          ))}
        </select>

        {teams.length > 0 && (
          <div className="flex gap-2 items-center">
            <select
              value={homeId ?? ""}
              onChange={(e) => setHomeId(Number(e.target.value))}
              className="border rounded px-2 py-1"
            >
              <option value="" disabled>
                Home team
              </option>
              {teams.map((team) => (
                <option key={team.id} value={team.id}>
                  {team.name}
                </option>
              ))}
            </select>
            <span>vs</span>
            <select
              value={awayId ?? ""}
              onChange={(e) => setAwayId(Number(e.target.value))}
              className="border rounded px-2 py-1"
            >
              <option value="" disabled>
                Away team
              </option>
              {teams.map((team) => (
                <option key={team.id} value={team.id}>
                  {team.name}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {homeId !== null && homeId === awayId && (
        <p className="mt-4">Pick two different teams.</p>
      )}
      {isLoading && <p className="mt-4">Calculating…</p>}
      {isError && <p className="mt-4 text-red-600">Prediction failed</p>}
      {prediction && homeTeam && awayTeam && (
        <PredictionResult
          prediction={prediction}
          homeName={homeTeam.name}
          awayName={awayTeam.name}
        />
      )}
    </div>
  );
}

export default PredictPage;
