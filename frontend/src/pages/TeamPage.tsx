import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { getPastMatches, getFutureMatches } from "../api/teams";
import type { Fixture, Matchup } from "../api/bracket";
import MatchupCard from "../components/MatchupCard";
import type { Team } from "../api/standings";

function fixtureToMatchup(fx: Fixture): Matchup {
  return {
    teamTop: fx.home_team,
    teamBottom: fx.away_team,
    legs: [
      { topGoals: fx.home_goals, bottomGoals: fx.away_goals, date: fx.date },
    ],
  };
}

function TeamPage() {
  const { id } = useParams();

  const {
    data: pastMatches,
    isLoading: isPastMatchesLoading,
    isError: isPastMatchesError,
  } = useQuery({
    queryKey: ["pastMatches", id],
    queryFn: () => getPastMatches(id!),
    enabled: !!id,
  });

  const {
    data: futureMatches,
    isLoading: isFutureMatchesLoading,
    isError: isFutureMatchesError,
  } = useQuery({
    queryKey: ["futureMatches", id],
    queryFn: () => getFutureMatches(id!),
    enabled: !!id,
  });

  if (!id) return <p>Invalid team</p>;
  if (isPastMatchesLoading || isFutureMatchesLoading) return <p>Loading...</p>;
  if (isPastMatchesError || isFutureMatchesError)
    return <p>Failed to load matches</p>;

  let team: Team | undefined;
  if (pastMatches && pastMatches.length > 0) {
    if (pastMatches[0].home_team.id === Number(id)) {
      team = pastMatches[0].home_team;
    } else {
      team = pastMatches[0].away_team;
    }
  }
  if (futureMatches && futureMatches.length > 0) {
    if (futureMatches[0].home_team.id === Number(id)) {
      team = futureMatches[0].home_team;
    } else {
      team = futureMatches[0].away_team;
    }
  }

  return (
    <>
      <div className="flex items-center justify-center gap-2 text-white text-4xl font-bold mb-4">
        {team?.logo_url && (
          <img src={team.logo_url} alt="" className="w-23 h-23" />
        )}
        {team?.name}
      </div>
      <div className="flex gap-8">
        <div className="flex-1">
          <div className="text-lg font-semibold mb-4">Past Matches</div>
          {pastMatches?.map((fx) => (
            <MatchupCard key={`${fx.id}`} matchup={fixtureToMatchup(fx)} />
          ))}
        </div>
        <div className="flex-1">
          <div className="text-lg font-semibold mb-4">Future Matches</div>
          {futureMatches?.map((fx) => (
            <MatchupCard key={`${fx.id}`} matchup={fixtureToMatchup(fx)} />
          ))}
        </div>
      </div>
    </>
  );
}

export default TeamPage;
