// src/components/MatchupCard.tsx
// The smallest reusable block of match display: two teams, their goals and the
// date. Used twice over - as a node of the bracket tree, and (through the
// fixtureToMatchup adapter in TeamPage) as a plain single-match row.
//
// It holds two components: MatchupCard (the card) and TeamRow (one team's line).
// TeamRow stays private to this file because the card is the only sensible way to
// use it - splitting it out only removes the duplication between the two rows.

import type { Team } from "../api/standings";
import type { Matchup } from "../api/bracket";

// The backend sends dates as ISO strings in UTC; toLocaleString renders them in
// the reader's own time zone. The locale is pinned to "pl-PL" for a day-month
// order (a match on 03/04 is the 3rd of April, never the 4th of March).
function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("pl-PL", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

type MatchupCardProps = {
  matchup: Matchup;
};

// One node of the bracket tree: two teams with their goals per leg. A one-off
// cup match shows a single score; a two-legged tie shows both legs plus the
// aggregate, with small "1 / 2 / Σ" column headers to tell the legs apart.
function MatchupCard({ matchup }: MatchupCardProps) {
  const isTwoLeg = matchup.legs.length > 1;

  // Aggregate = a team's goals summed across the tie. Only meaningful over two
  // legs, so we compute it only then. (null goals count as 0 in the sum.)
  const sumGoals = (pick: (leg: Matchup["legs"][number]) => number | null) =>
    matchup.legs.reduce((total, leg) => total + (pick(leg) ?? 0), 0);
  const topAggregate = isTwoLeg ? sumGoals((leg) => leg.topGoals) : null;
  const bottomAggregate = isTwoLeg ? sumGoals((leg) => leg.bottomGoals) : null;

  return (
    <div className="group bg-gray-800 border border-gray-700 rounded p-1.5 text-sm flex flex-col gap-1 transition-colors hover:text-white hover:border-white">
      {/* Column headers — only when there are two legs to label. */}
      {isTwoLeg && (
        <div className="flex items-center justify-end gap-1 text-xs text-gray-400 transition-colors group-hover:text-white">
          {matchup.legs.map((_, i) => (
            <span key={i} className="min-w-5 text-center">
              {i + 1}
            </span>
          ))}
          <span className="min-w-5 text-center font-semibold">Σ</span>
        </div>
      )}
      <TeamRow
        team={matchup.teamTop}
        goals={matchup.legs.map((leg) => leg.topGoals)}
        aggregate={topAggregate}
      />
      <TeamRow
        team={matchup.teamBottom}
        goals={matchup.legs.map((leg) => leg.bottomGoals)}
        aggregate={bottomAggregate}
      />
      <div className="text-xs text-gray-400 text-right transition-colors group-hover:text-white">
        {matchup.legs.map((leg) => formatDate(leg.date)).join(" / ")}
      </div>
    </div>
  );
}

type TeamRowProps = {
  team: Team;
  goals: (number | null)[];
  aggregate: number | null;
};

// A single team line: crest + name on the left; one box per leg on the right,
// plus a highlighted aggregate box for two-legged ties. Boxes share a fixed
// min width so both teams' scores line up under the headers.
function TeamRow({ team, goals, aggregate }: TeamRowProps) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="flex items-center gap-1">
        {team.logo_url && (
          <img src={team.logo_url} alt="" className="w-4 h-4" />
        )}
        {team.name}
      </span>
      <span className="flex items-center gap-1 font-semibold tabular-nums">
        {/* "?? -" keeps a genuine 0 visible instead of turning it into "-". */}
        {goals.map((legGoals, i) => (
          <span
            key={i}
            className="bg-gray-700 rounded px-1 min-w-5 text-center"
          >
            {legGoals ?? "-"}
          </span>
        ))}
        {aggregate !== null && (
          <span className="bg-gray-800 text-white rounded px-1 min-w-5 text-center transition-colors group-hover:text-yellow-400">
            {aggregate}
          </span>
        )}
      </span>
    </div>
  );
}

export default MatchupCard;
