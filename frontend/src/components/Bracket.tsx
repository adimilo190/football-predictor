// src/components/Bracket.tsx
// Draws a cup competition as a tournament tree: one COLUMN per round (left to
// right, earliest round first), and inside it one MatchupCard per tie.
//
// The layout is plain flexbox: items-stretch makes every column as tall as the
// tallest one and justify-around spreads the ties evenly inside it, which is what
// makes later rounds look centred against the earlier ones. overflow-x-auto lets a
// long competition scroll sideways instead of squashing the columns.

import { useQuery } from "@tanstack/react-query";
import { getBracket, groupIntoMatchups } from "../api/bracket";
import MatchupCard from "./MatchupCard";

type BracketProps = {
  leagueId: string;
  season: number;
};

function Bracket({ leagueId, season }: BracketProps) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["bracket", leagueId, season],
    queryFn: () => getBracket(leagueId, season),
  });

  if (isLoading) return <p>Loading...</p>;
  if (isError) return <p>Failed to load bracket</p>;
  if (!data) return null;
  if (data.length === 0) return <p>No knockout stage for this season yet</p>;
  return (
    <div className="flex gap-2 overflow-x-auto p-2 items-stretch">
      {data.map((round) => (
        <div key={round.round} className="flex flex-col shrink-0 min-w-40">
          <h3 className="font-semibold text-center mb-2">{round.round}</h3>
          <div className="flex flex-col justify-around flex-1 gap-2">
            {groupIntoMatchups(round.fixtures).map((m) => (
              <MatchupCard
                key={`${m.teamTop.id}-${m.teamBottom.id}`}
                matchup={m}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export default Bracket;
