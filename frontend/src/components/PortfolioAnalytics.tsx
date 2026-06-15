import type { AllocationResult, CorrelationCell, RebalanceRecord } from "../types/backtest";
import { formatCurrency, formatNumber, formatPercent } from "../utils/formatters";

interface PortfolioAnalyticsProps {
  allocations: AllocationResult[];
  correlations: CorrelationCell[];
  rebalanceEvents: RebalanceRecord[];
  frequency: string | null;
}

export function PortfolioAnalytics({
  allocations,
  correlations,
  rebalanceEvents,
  frequency,
}: PortfolioAnalyticsProps) {
  if (allocations.length === 0) {
    return null;
  }

  const tickers = allocations.map((allocation) => allocation.ticker);
  const correlationByPair = new Map(
    correlations.map((cell) => [`${cell.row_ticker}:${cell.column_ticker}`, cell.correlation]),
  );

  return (
    <section className="panel space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-ink">Allocation Analysis</h2>
          <p className="text-sm text-graphite">
            Rebalancing: <span className="font-medium text-ink">{formatFrequency(frequency)}</span>
          </p>
        </div>
        <span className="rounded-full bg-frost px-3 py-1 text-xs font-medium text-graphite">
          {allocations.length} holdings
        </span>
      </div>

      <div className="max-w-full overflow-x-auto">
        <table className="data-table">
          <thead>
            <tr>
              <th>Ticker</th>
              <th>Target Weight</th>
              <th>Ending Weight</th>
              <th>Return Contribution</th>
              <th>Annualized Volatility</th>
              <th>Risk Contribution</th>
            </tr>
          </thead>
          <tbody>
            {allocations.map((allocation) => (
              <tr key={allocation.ticker}>
                <td className="font-semibold">{allocation.ticker}</td>
                <td>{formatPercent(allocation.target_weight)}</td>
                <td>{formatPercent(allocation.ending_weight)}</td>
                <td className={allocation.contribution_to_return >= 0 ? "text-pine" : "text-wine"}>
                  {formatPercent(allocation.contribution_to_return)}
                </td>
                <td>{formatPercent(allocation.annualized_volatility)}</td>
                <td>{formatPercent(allocation.risk_contribution)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-ink">Correlation Matrix</h3>
        <div className="mt-3 max-w-full overflow-x-auto">
          <table className="correlation-table">
            <thead>
              <tr>
                <th />
                {tickers.map((ticker) => (
                  <th key={ticker}>{ticker}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tickers.map((rowTicker) => (
                <tr key={rowTicker}>
                  <th>{rowTicker}</th>
                  {tickers.map((columnTicker) => {
                    const value = correlationByPair.get(`${rowTicker}:${columnTicker}`) ?? null;
                    return <td key={`${rowTicker}-${columnTicker}`}>{formatNumber(value, 2)}</td>;
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div>
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <h3 className="text-sm font-semibold text-ink">Rebalance Activity</h3>
          <span className="rounded-full bg-frost px-3 py-1 text-xs font-medium text-graphite">
            {rebalanceEvents.length} executions
          </span>
        </div>
        {rebalanceEvents.length === 0 ? (
          <div className="empty-state">No rebalance events in this backtest window.</div>
        ) : (
          <div className="max-w-full overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Ticker</th>
                  <th>Action</th>
                  <th>Shares</th>
                  <th>Price</th>
                  <th>Cost</th>
                  <th>Target Value</th>
                  <th>Actual Value</th>
                </tr>
              </thead>
              <tbody>
                {rebalanceEvents.map((event, index) => (
                  <tr key={`${event.date}-${event.ticker}-${event.action}-${index}`}>
                    <td>{event.date}</td>
                    <td className="font-semibold">{event.ticker}</td>
                    <td className={event.action === "buy" ? "text-pine" : "text-wine"}>
                      {event.action.toUpperCase()}
                    </td>
                    <td>{formatNumber(Math.abs(event.shares_delta), 4)}</td>
                    <td>{formatCurrency(event.price)}</td>
                    <td>{formatCurrency(event.transaction_cost)}</td>
                    <td>{formatCurrency(event.target_value)}</td>
                    <td>{formatCurrency(event.actual_value)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}

function formatFrequency(frequency: string | null): string {
  if (frequency === "monthly") {
    return "Monthly";
  }
  if (frequency === "quarterly") {
    return "Quarterly";
  }
  if (frequency === "annual") {
    return "Annual";
  }
  if (frequency === "none") {
    return "None";
  }
  return "N/A";
}
