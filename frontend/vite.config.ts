// vite.config.ts
// Configuration for Vite, the tool that serves the app in development (with hot
// reload) and bundles it into static files for production. Two plugins: react()
// for JSX and fast refresh, tailwindcss() so Tailwind processes our stylesheet.

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
});
