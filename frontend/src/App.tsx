type LeagueCardProps = {
  name: string;
  country: string;
};
function LeagueCard({ name, country }: LeagueCardProps) {
  return (
    <article className="league-card">
      <h3>{name}</h3>
      <p>{country}</p>
    </article>
  );
}
function App() {
  return (
    <>
      <h1>⚽ Football Predictor</h1>
      <LeagueCard name="Premier League" country="England" />
      <LeagueCard name="La Liga" country="Spain" />
      <LeagueCard name="Serie A" country="Italy" />
      <LeagueCard name="Bundesliga" country="Germany" />
      <LeagueCard name="Ligue 1" country="France" />
    </>
  )
}

export default App
