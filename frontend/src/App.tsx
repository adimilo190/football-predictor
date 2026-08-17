import { Route, Routes, Link } from "react-router-dom";
import HomePage from "./pages/HomePage";
import LeaguePage from "./pages/LeaguePage";

function App() {
  return (
    <>
      <header>
        <Link to="/">
          <h1>⚽ Football Predictor</h1>
        </Link>
      </header>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/leagues/:id" element={<LeaguePage />} />
      </Routes>
    </>
  );
}

export default App;
