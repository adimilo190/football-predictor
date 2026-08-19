import { Route, Routes, Link } from "react-router-dom";
import HomePage from "./pages/HomePage";
import LeaguePage from "./pages/LeaguePage";
import BracketPage from "./pages/BracketPage";
function App() {
  return (
    <>
      <header className="border-b border-gray-200">
        <Link to="/" className="inline-block transition hover:opacity-80">
          <h1>⚽ Football Predictor</h1>
        </Link>
      </header>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/leagues/:id" element={<LeaguePage />} />
        <Route path="/bracket/:id" element={<BracketPage />} />
      </Routes>
    </>
  );
}

export default App;
