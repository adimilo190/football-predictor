// src/main.tsx
// The app's entry point: the one place that attaches React to the page. Vite
// loads this file from index.html, and it mounts <App/> into <div id="root">.
//
// It is also where the app-wide providers are set up. Order matters only in the
// sense that a provider must sit ABOVE any component that uses it:
//   StrictMode          - development-only double-render that surfaces bugs
//                         caused by impure components or missing cleanups
//   BrowserRouter       - makes routing (useParams, <Link>, <Routes>) available
//   QueryClientProvider - holds the TanStack Query cache shared by every useQuery
//
// index.css is imported here (not in a component) so Tailwind and the theme are
// loaded once for the whole app.

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "./index.css";
import App from "./App.tsx";

// Created once, outside the component tree: a new QueryClient on every render
// would throw the cache away each time.
const queryClient = new QueryClient();

// The "!" is a non-null assertion: TypeScript cannot know the element exists,
// but index.html always ships <div id="root">, so we vouch for it.
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </BrowserRouter>
  </StrictMode>,
);
