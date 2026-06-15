import type { MetricSummary } from "../types/backtest";
import { formatCurrency, formatNumber, formatPercent } from "../utils/formatters";

interface MetricsGridProps {
  metrics: MetricSummary;
  beforeCostMetrics?: MetricSummary;
}

export function MetricsGrid({ metrics, beforeCostMetrics }: MetricsGridProps) {
  const items = [
    ["After-cost Return", formatPercent(metrics.total_return), "total_return"],
    ["Before-cost Return", formatPercent(beforeCostMetrics?.total_return), "before_cost_total_return"],
    ["Annualized Return", formatPercent(metrics.annualized_return), "annualized_return"],
    ["Annualized Volatility", formatPercent(metrics.annualized_volatility), "annualized_volatility"],
    ["Sharpe Ratio", formatNumber(metrics.sharpe_ratio), "sharpe_ratio"],
    ["Maximum Drawdown", formatPercent(metrics.maximum_drawdown), "maximum_drawdown"],
    ["Trades", formatNumber(metrics.number_of_trades, 0), "number_of_trades"],
    ["Win Rate", formatPercent(metrics.win_rate), "win_rate"],
    ["Benchmark Return", formatPercent(metrics.benchmark_return), "benchmark_return"],
    ["Alpha", formatPercent(metrics.alpha_relative_to_benchmark), "alpha_relative_to_benchmark"],
    ["Transaction Costs", formatCurrency(metrics.total_transaction_costs), "total_transaction_costs"],
    ["Cost / Initial", formatPercent(metrics.transaction_cost_pct_of_initial), "transaction_cost_pct_of_initial"],
    ["Cost Drag", formatPercent(metrics.return_drag_from_costs), "return_drag_from_costs"],
  ] as const;

  return (
    <section className="panel">
      <h2 className="text-lg font-semibold text-ink">Core Metrics</h2>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {items.map(([label, value, key]) => (
          <div
            key={key}
            className="metric-tile"
            title={
              key === "before_cost_total_return"
                ? "Total return from the same strategy before transaction costs."
                : metrics.tooltip_explanations[key] ?? label
            }
          >
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
