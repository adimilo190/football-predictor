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

export default LeagueCard;
