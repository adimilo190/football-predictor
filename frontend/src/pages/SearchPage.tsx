// src/pages/SearchPage.tsx
// Team search ("/teams"): type a name, get matching teams, click one to open its
// page. The typing goes through useDebounce so we query the API once the user
// pauses instead of once per keystroke.

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useDebounce } from "../hooks/useDebounce";
import { searchTeams } from "../api/teams";
import { Link } from "react-router-dom";

function SearchPage() {
  // Raw text the user is typing. Controlled input: React owns this value.
  const [term, setTerm] = useState("");

  // Delayed copy of `term`: catches up 300ms after typing stops. We search on
  // this, so we don't hit the API on every keystroke.
  const debouncedTerm = useDebounce(term, 300);

  // Server data: teams matching the debounced term. `enabled` skips the request
  // while the box is empty, so we never call the API with an empty search.
  const {
    data: teams,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["teamSearch", debouncedTerm],
    queryFn: () => searchTeams(debouncedTerm),
    enabled: debouncedTerm.length > 0,
  });

  // The state of the search is collected into a VARIABLE instead of returning
  // early from the component. An early return would unmount the input while
  // loading, and the user would lose focus mid-typing; this way the box always
  // stays on screen and only the area under it changes.
  let results;
  if (isLoading) {
    results = <p className="mt-2">Searching...</p>;
  } else if (isError) {
    results = <p className="mt-2 text-red-600">Search failed</p>;
  } else if (teams?.length === 0) {
    results = <p className="mt-2">Unknown team</p>;
  } else {
    results = (
      <ul className="mt-2">
        {teams?.map((team) => (
          <li key={team.id}>
            <Link
              to={`/teams/${team.id}`}
              className="hover:underline hover:text-white"
            >
              {team.name}
            </Link>
          </li>
        ))}
      </ul>
    );
  }

  return (
    <div className="px-4 my-4">
      <input
        value={term}
        onChange={(e) => setTerm(e.target.value)}
        placeholder="Find teams..."
        className="border rounded px-2 py-1 w-full max-w-sm"
      />
      {results}
    </div>
  );
}

export default SearchPage;
