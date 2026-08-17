import LeagueTable from "../components/LeagueTable";
import { useParams } from "react-router-dom";

function LeaguePage() {
  const { id } = useParams();
  if (!id) return <p>Invalid league</p>;
  return (
    <>
      <LeagueTable leagueId={id} />
    </>
  );
}

export default LeaguePage;
