// src/App.tsx
// Layout + routing: the shared header (clickable title, always back to the home
// page) sits above <Routes>, which swaps in one page component depending on the
// URL. This is a single-page app - the router changes what renders without the
// browser ever reloading the page.
//
// A path segment starting with ":" is a parameter; the page reads it with
// useParams (e.g. "/leagues/39" -> id = "39").

import { Route, Routes, Link } from "react-router-dom";
import HomePage from "./pages/HomePage";
import LeaguePage from "./pages/LeaguePage";
import BracketPage from "./pages/BracketPage";
import SearchPage from "./pages/SearchPage";
import TeamPage from "./pages/TeamPage";
import PredictPage from "./pages/PredictPage";
import NotFoundPage from "./pages/NotFoundPage";
function App() {
  return (
    <>
      <header className="border-b border-gray-200">
        <Link
          to="/"
          className="inline-block transition hover:opacity-80 hover:underline"
        >
          <h1>⚽ Football Predictor</h1>
        </Link>
      </header>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/leagues/:id" element={<LeaguePage />} />
        <Route path="/bracket/:id" element={<BracketPage />} />
        <Route path="/teams" element={<SearchPage />} />
        <Route path="/teams/:id" element={<TeamPage />} />
        <Route path="/predict" element={<PredictPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </>
  );
}

export default App;
