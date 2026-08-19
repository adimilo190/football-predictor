import Bracket from "../components/Bracket";
import { useParams } from "react-router-dom";

function BracketPage() {
  const { id } = useParams();
  if (!id) return <p>Invalid competition</p>;
  return (
    <>
      <Bracket leagueId={id} />
    </>
  );
}

export default BracketPage;
