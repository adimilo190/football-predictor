// src/pages/LeaguePage.tsx
// Page for one league ("/leagues/:id"): the season picker plus the standings table.
// The page owns the season choice, the LeagueTable component owns fetching and
// rendering the rows - a page wires things together, a component does one job.

import { useParams } from "react-router-dom";
import LeagueTable from "../components/LeagueTable";
import { useSeasonSelector } from "../hooks/useSeasonSelector";

function LeaguePage() {
  const { id } = useParams();

  // Season list, the user's pick and the effective season, all in one reusable
  // hook. Called before the early return so its inner hooks run every render.
  const { season, seasons, setSelectedSeason } = useSeasonSelector(id);

  if (!id) return <p>Invalid league</p>;

  return (
    <>
      <div className="flex justify-start px-4 my-4">
        <select
          value={season ?? ""}
          onChange={(e) => setSelectedSeason(Number(e.target.value))}
          className="border rounded px-2 py-1"
        >
          {seasons?.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>
      {season !== null && <LeagueTable leagueId={id} season={season} />}
    </>
  );
}

export default LeaguePage;
