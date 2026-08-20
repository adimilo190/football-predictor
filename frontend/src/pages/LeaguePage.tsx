import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import LeagueTable from "../components/LeagueTable";
import { getSeasons } from "../api/standings";

function LeaguePage() {
  const { id } = useParams();

  // UI state: which season the user picked. This is a local interface choice,
  // not server data, so it belongs in useState (not useQuery).
  const [season, setSeason] = useState(2024);

  // Server data: the seasons we actually have for this league. useQuery handles
  // the fetch, cache and loading/error for us. enabled=false skips the request
  // until we have an id, so id! below is safe (the query never runs without one).
  const { data: seasons } = useQuery({
    queryKey: ["seasons", id],
    queryFn: () => getSeasons(id!),
    enabled: !!id,
  });

  // Rules of hooks: every hook above must run on each render, so this early
  // return has to sit AFTER them, never before.
  if (!id) return <p>Invalid league</p>;

  return (
    <>
      <div className="flex justify-start px-4 my-4">
        <select
          value={season}
          onChange={(e) => setSeason(Number(e.target.value))}
          className="border rounded px-2 py-1"
        >
          {seasons?.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>
      <LeagueTable leagueId={id} season={season} />
    </>
  );
}

export default LeaguePage;
