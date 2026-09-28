// src/hooks/useDebounce.ts
// A custom hook - a plain function that calls other hooks and can be reused by any
// component. This one solves the search box problem: typing "Barcelona" would fire
// nine requests, one per letter. Debouncing waits for a pause in typing first.

import { useEffect, useState } from "react";

// Returns a delayed copy of `value` that only updates once `value` has stopped
// changing for `delayMs`. Lets the search hit the API on the settled value,
// not on every keystroke.
export function useDebounce<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    // Schedule pushing the latest value into `debounced` after the delay.
    const timer = setTimeout(() => setDebounced(value), delayMs);
    // Cleanup: if `value` changes before the delay elapses (another keystroke),
    // React runs THIS first and cancels the pending timer. So the update only
    // goes through after a pause longer than delayMs.
    return () => clearTimeout(timer);
  }, [value, delayMs]);

  return debounced;
}
