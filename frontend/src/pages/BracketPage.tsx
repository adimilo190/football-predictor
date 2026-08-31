import Bracket from "../components/Bracket";
import { useParams } from "react-router-dom";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getSeasons } from "../api/standings";

function BracketPage() {

  const { id } = useParams();

  const [season, setSeason] = useState(2026);

  const { data: seasons } = useQuery({
    queryKey: ["seasons", id],
    queryFn: () => getSeasons(id!),
    enabled: !!id,
  });

  if (!id) return <p>Invalid competition</p>;
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
      <Bracket leagueId={id} season={season} />
    </>
  );
}

export default BracketPage;
