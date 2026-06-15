import { AlertTriangle } from "lucide-react";

import { MetricsGrid } from "../components/MetricsGrid";
import { PortfolioChart } from "../components/PortfolioChart";
import { PortfolioAnalytics } from "../components/PortfolioAnalytics";
import { RobustnessHeatmap } from "../components/RobustnessHeatmap";
import { RollingMetricsChart } from "../components/RollingMetricsChart";
import { TradeLog } from "../components/TradeLog";
import type { BacktestResponse } from "../types/backtest";

interface ResultsDashboardProps {
  result: BacktestResponse;
}

export function ResultsDashboard({ result }: ResultsDashboardProps) {
  const isPortfolioResult = result.strategy_name === "portfolio_rebalance";

  return (
    <div className="min-w-0 space-y-6">
      <section className="panel">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="section-kicker">Results Dashboard</p>
            <h2 className="mt-1 text-xl font-semibold text-ink">
              {result.ticker} · {readableStrategy(result.strategy_name)}
            </h2>
          </div>
          <div className="rounded-md border border-line bg-frost px-3 py-2 text-sm text-graphite">
            Benchmark: <span className="font-medium text-ink">{result.benchmark_ticker}</span>
          </div>
        </div>
      </section>

      {result.warnings.length > 0 && (
        <section className="space-y-2">
          {result.warnings.map((warning, index) => (
            <div
              key={`${warning}-${index}`}
              className="flex items-start gap-3 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-copper"
            >
              <AlertTriangle size={18} className="mt-0.5 shrink-0" />
              <span>{warning}</span>
            </div>
          ))}
        </section>
      )}

      <MetricsGrid metrics={result.metrics} beforeCostMetrics={result.before_cost_metrics} />
      <PortfolioChart
        portfolioCurve={result.portfolio_curve}
        beforeCostCurve={result.before_cost_curve}
        benchmarkCurve={result.benchmark_curve}
      />
      {isPortfolioResult && (
        <PortfolioAnalytics
          allocations={result.portfolio_allocations}
          correlations={result.correlation_matrix}
          rebalanceEvents={result.rebalance_events}
          frequency={result.rebalancing_frequency}
        />
      )}
      {!isPortfolioResult && <RobustnessHeatmap robustness={result.robustness} />}
      <RollingMetricsChart rollingMetrics={result.rolling_metrics} />
      {!isPortfolioResult && <TradeLog trades={result.trades} />}
    </div>
  );
}

function readableStrategy(strategyName: string): string {
  if (strategyName === "moving_average_crossover") {
    return "Moving Average Crossover";
  }
  if (strategyName === "buy_and_hold") {
    return "Buy and Hold";
  }
  if (strategyName === "rsi_mean_reversion") {
    return "RSI Mean Reversion";
  }
  if (strategyName === "momentum") {
    return "Momentum";
  }
  if (strategyName === "bollinger_bands") {
    return "Bollinger Bands";
  }
  if (strategyName === "portfolio_rebalance") {
    return "Portfolio Rebalancing";
  }
  return strategyName;
}
