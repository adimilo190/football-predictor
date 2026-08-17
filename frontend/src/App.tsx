import LeagueCard from "./components/LeagueCard";
import LeagueTable from "./components/LeagueTable";

function App() {
  return (
    <>
      <h1>⚽ Football Predictor</h1>
      <LeagueTable />
      <LeagueCard name="Premier League" country="England" />
      <LeagueCard name="La Liga" country="Spain" />
      <LeagueCard name="Serie A" country="Italy" />
      <LeagueCard name="Bundesliga" country="Germany" />
      <LeagueCard name="Ligue 1" country="France" />
    </>
  );
}

export default App;
