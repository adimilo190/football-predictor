// Base URL of the backend API. Read from VITE_API_URL (see .env); the fallback
// keeps the app working if the variable is missing (e.g. fresh clone with no .env).
export const API_BASE_URL =
  import.meta.env.VITE_API_URL ?? "http://localhost:8000";
