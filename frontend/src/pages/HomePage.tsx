import LeagueCard from "../components/LeagueCard";
import { LEAGUES } from "../data/leagues";
import { Link } from "react-router-dom";

function HomePage() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
      {LEAGUES.map((league) => (
        <Link key={league.id} to={`/leagues/${league.id}`}>
          <LeagueCard name={league.name} country={league.country} />
        </Link>
      ))}
    </div>
  );
}

export default HomePage;
