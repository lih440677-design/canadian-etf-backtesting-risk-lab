import type { TradeRecord } from "../types/backtest";
import { formatCurrency, formatNumber } from "../utils/formatters";

interface TradeLogProps {
  trades: TradeRecord[];
}

export function TradeLog({ trades }: TradeLogProps) {
  const completedTrades = trades.filter((trade) => trade.net_profit !== null).length;

  return (
    <section className="panel">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">Trade Log</h2>
        <span className="rounded-full bg-frost px-3 py-1 text-xs font-medium text-graphite">
          {completedTrades} completed / {trades.length} total
        </span>
      </div>
      {trades.length === 0 ? (
        <div className="empty-state">No completed trades in this backtest window.</div>
      ) : (
        <div className="max-w-full overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Entry</th>
                <th>Entry Price</th>
                <th>Exit</th>
                <th>Exit Price</th>
                <th>Shares</th>
                <th>Gross Profit</th>
                <th>Cost</th>
                <th>Net Profit</th>
                <th>Days</th>
                <th>Reason</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((trade, index) => (
                <tr key={`${trade.entry_date}-${index}`}>
                  <td>{trade.entry_date}</td>
                  <td>{formatCurrency(trade.entry_price)}</td>
                  <td>{trade.exit_date ?? "Open"}</td>
                  <td>{formatCurrency(trade.exit_price)}</td>
                  <td>{formatNumber(trade.shares, 4)}</td>
                  <td>{formatCurrency(trade.gross_profit)}</td>
                  <td>{formatCurrency(trade.transaction_cost)}</td>
                  <td className={(trade.net_profit ?? 0) >= 0 ? "text-pine" : "text-wine"}>
                    {formatCurrency(trade.net_profit)}
                  </td>
                  <td>{formatNumber(trade.holding_period, 0)}</td>
                  <td>{trade.exit_reason ?? "Open"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
