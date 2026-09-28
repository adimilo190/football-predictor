// src/hooks/useSeasonSelector.ts
// Custom hook holding the season-picker logic that LeaguePage and BracketPage both
// need: which seasons exist, which one the user chose, and which one is actually in
// effect. Extracted so the two pages cannot drift apart - and so the "default to
// the newest season" rule is written down exactly once.

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getSeasons } from "../api/standings";

// Manages season selection for a competition page: owns the available-seasons
// list (server data) and the user's pick (UI state), and derives the effective
// season. Shared by LeaguePage and BracketPage so the logic lives in one place.
export function useSeasonSelector(id: string | undefined) {
  // UI state: the user's explicit pick. Null until they choose one.
  const [selectedSeason, setSelectedSeason] = useState<number | null>(null);

  // Server data: the seasons available for this competition.
  const { data: seasons } = useQuery({
    queryKey: ["seasons", id],
    queryFn: () => getSeasons(id!),
    enabled: !!id,
  });

  // Effective season: the user's pick, or the newest available (seasons[0]).
  const season = selectedSeason ?? seasons?.[0] ?? null;
  return { season, seasons, setSelectedSeason };
}
