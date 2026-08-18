type LeagueCardProps = {
  name: string;
  country: string;
};

function LeagueCard({ name, country }: LeagueCardProps) {
  return (
    <article className="border border-gray-200 rounded-lg p-4 shadow-sm transition hover:shadow-md cursor-pointer">
      <h3 className="font-semibold text-lg">{name}</h3>
      <p className="text-sm text-gray-500">{country}</p>
    </article>
  );
}

export default LeagueCard;
