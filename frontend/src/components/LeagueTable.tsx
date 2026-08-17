import { useState, useEffect } from "react";

type Team = {
  id: number;
  name: string;
  country: string | null;
  logo_url: string | null;
};

type Standing = {
  rank: number;
  team: Team;
  played: number;
  wins: number;
  draws: number;
  losses: number;
  points: number;
  goals_for: number;
  goals_against: number;
  form: string | null;
};

function LeagueTable() {
  const [standings, setStandings] = useState<Standing[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadStandings() {
      try {
        const res = await fetch("http://localhost:8000/leagues/39/standings");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setStandings(data);
      } catch (err) {
        console.error(err);
        setError("Failed to load standings");
      } finally {
        setLoading(false);
      }
    }
    loadStandings();
  }, []);

  if (loading) {
    return <p>Loading...</p>;
  } else if (error) {
    return <p>{error}</p>;
  } else {
    return (
      <table className="border-collapse mx-auto text-center">
        <thead>
          <tr className="bg-gray-100">
            <th className="border px-3 py-1">#</th>
            <th className="border px-3 py-1 text-left">Team</th>
            <th className="border px-3 py-1">P</th>
            <th className="border px-3 py-1">W</th>
            <th className="border px-3 py-1">D</th>
            <th className="border px-3 py-1">L</th>
            <th className="border px-3 py-1">GF</th>
            <th className="border px-3 py-1">GA</th>
            <th className="border px-3 py-1">Pts</th>
          </tr>
        </thead>
        <tbody>
          {standings.map((s) => (
            <tr key={s.team.id} className="hover:bg-blue-50">
              <td className="border px-3 py-1">{s.rank}</td>
              <td className="border px-3 py-1 text-left">
                <div className="flex items-center gap-2">
                  {s.team.logo_url && (
                    <img src={s.team.logo_url} alt="" className="w-6 h-6" />
                  )}
                  {s.team.name}
                </div>
              </td>
              <td className="border px-3 py-1">{s.played}</td>
              <td className="border px-3 py-1">{s.wins}</td>
              <td className="border px-3 py-1">{s.draws}</td>
              <td className="border px-3 py-1">{s.losses}</td>
              <td className="border px-3 py-1">{s.goals_for}</td>
              <td className="border px-3 py-1">{s.goals_against}</td>
              <td className="border px-3 py-1">{s.points}</td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  }
}

export default LeagueTable;
