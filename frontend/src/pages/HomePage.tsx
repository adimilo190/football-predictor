import { Link } from "react-router-dom";
import { COUNTRIES, EUROPEAN_COMPETITIONS } from "../data/leagues";

function HomePage() {
  return (
    <>
      <div className="max-w-2xl mx-auto p-4 flex flex-col gap-2">
        <Link
          to="/teams"
          className="border rounded-lg p-3 font-semibold hover:text-white"
        >
          🔍 Find team
        </Link>
        {/* Each country expands to its league (table) + cup (bracket) */}
        {COUNTRIES.map((country) => (
          <details
            key={country.name}
            className="border rounded-lg hover:text-white"
          >
            <summary className="cursor-pointer font-semibold p-3">
              {country.name}
            </summary>
            <div className="flex flex-col gap-1 px-3 pb-3">
              <Link
                to={`/leagues/${country.league.id}`}
                className="hover:underline"
              >
                {country.league.name}
              </Link>
              <Link
                to={`/bracket/${country.cup.id}`}
                className="hover:underline"
              >
                {country.cup.name}
              </Link>
            </div>
          </details>
        ))}
        <details className="border rounded-lg hover:text-white">
          <summary className="cursor-pointer font-semibold p-3">
            European Competitions
          </summary>
          <div className="flex flex-col gap-1 px-3 pb-3">
            {EUROPEAN_COMPETITIONS.map((comp) => (
              <Link
                key={comp.id}
                to={`/bracket/${comp.id}`}
                className="hover:underline"
              >
                {comp.name}
              </Link>
            ))}
          </div>
        </details>
      </div>
    </>
  );
}

export default HomePage;
