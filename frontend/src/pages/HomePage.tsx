import LeagueCard from "../components/LeagueCard";
import { LEAGUES } from "../data/leagues";
import { Link } from "react-router-dom";

function HomePage() {
  return (
    <>
      {LEAGUES.map((league) => (
        <Link key={league.id} to={`/leagues/${league.id}`}>
          <LeagueCard name={league.name} country={league.country} />
        </Link>
      ))}
    </>
  );
}

export default HomePage;
