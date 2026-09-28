// src/pages/TeamPage.tsx
// One team's page ("/teams/:id"): recent results in the left column, upcoming
// matches in the right one. Matches are cross-competition, exactly as the backend
// returns them - league, cup and Europe mixed, because that is what "form" means.

import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { getPastMatches, getFutureMatches } from "../api/teams";
import type { Fixture, Matchup } from "../api/bracket";
import MatchupCard from "../components/MatchupCard";
import type { Team } from "../api/standings";

// Adapter: MatchupCard speaks Matchup (a tie of one or two legs), while this page
// has plain fixtures. A single match is simply a tie with ONE leg, so we wrap it
// instead of writing a second card component that would look identical.
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

  // Two independent queries, each with its own loading/error flags (hence the
  // renames). They run in parallel - neither waits for the other. `enabled` keeps
  // them from firing before the URL param is known, and both hooks sit above the
  // guards below, because hooks must run in the same order on every render.
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

  // There is no /teams/{id} endpoint yet, so the team's own name and crest are
  // taken from one of its matches: whichever side of the fixture carries our id.
  // Future matches are checked second on purpose, so their (fresher) data wins.
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
