// src/pages/BracketPage.tsx
// Page for one knockout competition ("/bracket/:id"): season picker plus the
// tournament tree. Deliberately the twin of LeaguePage - same shape, same hook,
// only the child component differs (Bracket instead of LeagueTable), because a cup
// has no table and a league has no bracket.

import Bracket from "../components/Bracket";
import { useParams } from "react-router-dom";
import { useSeasonSelector } from "../hooks/useSeasonSelector";

function BracketPage() {
  const { id } = useParams();

  // Called before the early return below: hooks must run in the same order on
  // every render, so no hook may sit behind an "if".
  const { season, seasons, setSelectedSeason } = useSeasonSelector(id);

  if (!id) return <p>Invalid competition</p>;
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
      {/* Wait for a season before mounting the bracket: null would mean
          fetching with "?season=null". */}
      {season !== null && <Bracket leagueId={id} season={season} />}
    </>
  );
}

export default BracketPage;
