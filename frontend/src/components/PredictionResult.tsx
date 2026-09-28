// src/components/PredictionResult.tsx
// Visualises one prediction: three probability bars (home win / draw / away win)
// and the most likely scorelines underneath.
//
// Presentation only - it fetches nothing and holds no state. Everything it draws
// arrives as props from PredictPage, which keeps the "what to show" and the "how to
// show it" decisions in separate files.

import type { Prediction } from "../api/predictions";

// One labelled probability bar. The track (gray) is full width; the fill's width
// is the probability as a percent, set inline because the value is dynamic (a
// Tailwind class can't hold an arbitrary runtime width).
type OutcomeBarProps = { label: string; probability: number; color: string };

// The colour arrives as a COMPLETE class literal ("bg-emerald-500"), never built
// from pieces: Tailwind scans the source as text, so `bg-${color}-500` would leave
// no class for it to find and the bar would come out unpainted.
function OutcomeBar({ label, probability, color }: OutcomeBarProps) {
  const percent = probability * 100;
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span>{label}</span>
        <span>{percent.toFixed(1)}%</span>
      </div>
      <div className="bg-gray-700 rounded h-3">
        <div
          className={`${color} h-3 rounded`}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}

// The full prediction view: three 1/X/2 bars plus the most likely scorelines.
// Team names come in as props so this component stays about presentation only.
type Props = { prediction: Prediction; homeName: string; awayName: string };

function PredictionResult({ prediction, homeName, awayName }: Props) {
  return (
    <div className="mt-6 flex flex-col gap-3">
      <OutcomeBar
        label={`${homeName} win`}
        probability={prediction.home_win}
        color="bg-emerald-500"
      />
      <OutcomeBar
        label="Draw"
        probability={prediction.draw}
        color="bg-amber-500"
      />
      <OutcomeBar
        label={`${awayName} win`}
        probability={prediction.away_win}
        color="bg-sky-500"
      />

      <div className="mt-2">
        <h3 className="font-semibold mb-1">Most likely scores</h3>
        <ul className="flex flex-col gap-1">
          {prediction.top_scores.map((score) => (
            <li
              key={`${score.home_goals}-${score.away_goals}`}
              className="flex justify-between"
            >
              <span>
                {score.home_goals}:{score.away_goals}
              </span>
              <span className="text-gray-400">
                {(score.probability * 100).toFixed(1)}%
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default PredictionResult;
