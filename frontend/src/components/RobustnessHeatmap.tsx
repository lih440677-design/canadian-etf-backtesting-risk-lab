import { AlertTriangle } from "lucide-react";

import type { RobustnessResult } from "../types/backtest";
import { formatNumber, formatPercent } from "../utils/formatters";

interface RobustnessHeatmapProps {
  robustness: RobustnessResult | null;
}

export function RobustnessHeatmap({ robustness }: RobustnessHeatmapProps) {
  if (!robustness || robustness.points.length === 0) {
    return null;
  }

  const xValues = uniqueSorted(robustness.points.map((point) => point.x_value));
  const yValues = uniqueSorted(robustness.points.map((point) => point.y_value)).reverse();
  const values = robustness.points
    .map((point) => point.metric_value)
    .filter((value): value is number => value !== null && Number.isFinite(value));
  const minValue = values.length ? Math.min(...values) : 0;
  const maxValue = values.length ? Math.max(...values) : 0;
  const pointByCoordinate = new Map(
    robustness.points.map((point) => [`${point.x_value}:${point.y_value}`, point]),
  );

  return (
    <section className="panel space-y-5" data-testid="robustness-results">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-ink">Robustness Scan</h2>
          <p className="text-sm text-graphite">
            {robustness.x_axis_label} x {robustness.y_axis_label} · {readableMetric(robustness.metric)}
          </p>
        </div>
        <span className="rounded-full bg-frost px-3 py-1 text-xs font-medium text-graphite">
          {robustness.tested_combinations} tests
        </span>
      </div>

      {robustness.overfit_warning && (
        <div className="flex items-start gap-3 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-copper">
          <AlertTriangle size={18} className="mt-0.5 shrink-0" />
          <span>{robustness.overfit_warning}</span>
        </div>
      )}

      <div className="grid gap-3 md:grid-cols-4">
        <div className="summary-tile">
          <span>Best</span>
          <strong>{formatMetric(robustness.best_metric_value, robustness.metric)}</strong>
        </div>
        <div className="summary-tile">
          <span>Best Params</span>
          <strong>
            {formatAxisValue(robustness.best_x_value)} / {formatAxisValue(robustness.best_y_value)}
          </strong>
        </div>
        <div className="summary-tile">
          <span>Stable Zone</span>
          <strong>{formatPercent(robustness.stable_zone_share)}</strong>
        </div>
        <div className="summary-tile">
          <span>Positive Grid</span>
          <strong>{formatPercent(robustness.positive_return_share)}</strong>
        </div>
      </div>

      <div className="max-w-full overflow-x-auto">
        <table className="heatmap-table">
          <thead>
            <tr>
              <th>{robustness.y_axis_label}</th>
              {xValues.map((xValue) => (
                <th key={xValue}>{formatAxisValue(xValue)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {yValues.map((yValue) => (
              <tr key={yValue}>
                <th>{formatAxisValue(yValue)}</th>
                {xValues.map((xValue) => {
                  const point = pointByCoordinate.get(`${xValue}:${yValue}`);
                  return (
                    <td
                      key={`${xValue}-${yValue}`}
                      style={{ backgroundColor: heatColor(point?.metric_value, minValue, maxValue) }}
                      title={
                        point
                          ? `Return ${formatPercent(point.total_return)} · Sharpe ${formatNumber(point.sharpe_ratio)} · Trades ${formatNumber(point.number_of_trades, 0)}`
                          : "Invalid combination"
                      }
                    >
                      {formatMetric(point?.metric_value ?? null, robustness.metric)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function uniqueSorted(values: number[]): number[] {
  return Array.from(new Set(values)).sort((a, b) => a - b);
}

function readableMetric(metric: string): string {
  if (metric === "total_return") {
    return "Total return";
  }
  return "Sharpe ratio";
}

function formatMetric(value: number | null | undefined, metric: string): string {
  if (metric === "total_return") {
    return formatPercent(value);
  }
  return formatNumber(value);
}

function formatAxisValue(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "N/A";
  }
  return Number.isInteger(value) ? `${value}` : value.toFixed(2);
}

function heatColor(value: number | null | undefined, minValue: number, maxValue: number): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "#f1f5f9";
  }
  if (maxValue === minValue) {
    return "#d9f99d";
  }
  const ratio = Math.max(0, Math.min(1, (value - minValue) / (maxValue - minValue)));
  const hue = 18 + ratio * 150;
  const lightness = 92 - ratio * 18;
  return `hsl(${hue} 58% ${lightness}%)`;
}
