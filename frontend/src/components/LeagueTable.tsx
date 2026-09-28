// src/components/LeagueTable.tsx
// Renders one league table. It receives the league id and season as props and does
// its own fetching, so any page can drop it in without wiring queries itself.

import { useQuery } from "@tanstack/react-query";
import { getStandings } from "../api/standings";

type LeagueTableProps = {
  leagueId: string;
  season: number;
};

function LeagueTable({ leagueId, season }: LeagueTableProps) {
  // The season is part of the queryKey, so each season is cached separately:
  // switching back to a season already viewed shows it instantly, with no refetch.
  const { data, isLoading, isError } = useQuery({
    queryKey: ["standings", leagueId, season],
    queryFn: () => getStandings(leagueId, season),
  });

  if (isLoading) return <p>Loading...</p>;
  if (isError) return <p>Failed to load standings</p>;
  if (!data) return null;

  return (
    <table className="border-collapse mx-auto text-center">
      <thead>
        <tr className="bg-gray-800">
          <th className="border border-gray-700 px-3 py-1">#</th>
          <th className="border border-gray-700 px-3 py-1 text-left">Team</th>
          <th className="border border-gray-700 px-3 py-1">P</th>
          <th className="border border-gray-700 px-3 py-1">W</th>
          <th className="border border-gray-700 px-3 py-1">D</th>
          <th className="border border-gray-700 px-3 py-1">L</th>
          <th className="border border-gray-700 px-3 py-1">GF</th>
          <th className="border border-gray-700 px-3 py-1">GA</th>
          <th className="border border-gray-700 px-3 py-1">Pts</th>
        </tr>
      </thead>
      <tbody>
        {data.map((s) => (
          <tr key={s.team.id} className="hover:bg-gray-800">
            <td className="border border-gray-700 px-3 py-1">{s.rank}</td>
            <td className="border border-gray-700 px-3 py-1 text-left">
              <div className="flex items-center gap-2">
                {s.team.logo_url && (
                  <img src={s.team.logo_url} alt="" className="w-6 h-6" />
                )}
                {s.team.name}
              </div>
            </td>
            <td className="border border-gray-700 px-3 py-1">{s.played}</td>
            <td className="border border-gray-700 px-3 py-1">{s.wins}</td>
            <td className="border border-gray-700 px-3 py-1">{s.draws}</td>
            <td className="border border-gray-700 px-3 py-1">{s.losses}</td>
            <td className="border border-gray-700 px-3 py-1">{s.goals_for}</td>
            <td className="border border-gray-700 px-3 py-1">
              {s.goals_against}
            </td>
            <td className="border border-gray-700 px-3 py-1">{s.points}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default LeagueTable;
