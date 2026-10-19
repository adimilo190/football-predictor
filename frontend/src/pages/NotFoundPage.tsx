// src/pages/NotFoundPage.tsx
// The catch-all page: React Router renders it for every URL that matches no
// other route. It exists because of how a single-page app is served - the
// rewrite in vercel.json sends every path to index.html, so a typo like
// "/predictt" reaches React instead of the server's own 404 page. Without this
// route nothing matches, <Routes> renders nothing, and the visitor is left
// looking at the header above an empty page.
//
// The HTTP status stays 200 OK: the response is sent long before React decides
// there is no such page. A real 404 status would require server-side rendering.
//
// The big "404" is a plain <div>, not a heading, on purpose: index.css styles
// h1/h2/p outside any cascade layer, and unlayered CSS beats Tailwind's layered
// utilities - a font size or colour set by a class there would be ignored.

import { Link, useLocation } from "react-router-dom";

function NotFoundPage() {
  // The address the visitor tried, echoed back so the message names a concrete
  // path instead of a generic "page not found".
  const { pathname } = useLocation();

  return (
    // flex-1 claims the height left over by the header, so the block lands in
    // the middle of the viewport (#root is a full-height flex column).
    <div className="flex flex-1 flex-col items-center justify-center gap-6 p-4">
      {/* Dimmed to the border colour: the number is decoration, the message
          and the way out are what should catch the eye. */}
      <div className="font-mono text-8xl tracking-tight text-[var(--border)]">
        404
      </div>
      <h2>Page not found</h2>
      <p className="max-w-sm">
        No page matches <code className="break-all">{pathname}</code> in this
        app.
      </p>
      <Link
        to="/"
        className="rounded-lg border border-[var(--border)] px-5 py-3 font-semibold text-[var(--text-h)] transition hover:border-[var(--accent-border)] hover:bg-[var(--accent-bg)] hover:text-[var(--accent)]"
      >
        ← Back to home
      </Link>
    </div>
  );
}

export default NotFoundPage;
