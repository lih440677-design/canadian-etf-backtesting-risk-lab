export function AboutMethodology() {
  return (
    <div className="space-y-6">
      <section className="page-band">
        <p className="section-kicker">About Methodology</p>
        <h1 className="mt-3 text-3xl font-semibold text-ink">Backtesting With Bias Controls</h1>
        <p className="mt-4 max-w-3xl text-base leading-7 text-graphite">
          Phase 5 keeps market data, strategy signals, portfolio rebalancing, execution,
          transaction costs, risk controls, accounting, performance metrics, and robustness scans separate.
        </p>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        {[
          [
            "Backtesting",
            "A historical simulation that asks how a rule-based strategy would have behaved over a selected period.",
          ],
          [
            "Adjusted Prices",
            "Long-term returns use adjusted close data so splits and distributions are handled more consistently.",
          ],
          [
            "Look-ahead Bias",
            "Signals based on a day’s close are executed on the next available trading day.",
          ],
          [
            "Maximum Drawdown",
            "The largest decline from a prior portfolio peak, shown as a negative percentage.",
          ],
          [
            "Sharpe Ratio",
            "A risk-adjusted return estimate that compares annualized return with annualized volatility.",
          ],
          [
            "Known Data Limits",
            "Yahoo Finance data may not fully handle delisted securities, historical index membership, or survivorship bias.",
          ],
          [
            "Overfitting",
            "Robustness scans show whether nearby parameter choices produce similar results, but optimized parameters still do not guarantee future returns.",
          ],
          [
            "Transaction Costs",
            "Fixed fees, percentage fees, slippage, and bid-ask spread assumptions are deducted when trades execute.",
          ],
          [
            "Risk Controls",
            "Stop-loss and take-profit triggers are based on observed closing prices and execute on the next trading day.",
          ],
          [
            "Rolling Metrics",
            "Rolling return, volatility, and Sharpe ratio are calculated from the after-cost portfolio curve.",
          ],
          [
            "Portfolio Rebalancing",
            "Portfolio mode allocates target weights on the first overlapping date and rebalances on the selected calendar schedule.",
          ],
          [
            "Correlation and Risk Contribution",
            "Portfolio holdings are compared using daily return correlations, annualized volatility, and covariance-based risk contribution.",
          ],
          [
            "Strategy Scope",
            "RSI, Momentum, and Bollinger Bands are simple rule-based strategies for research comparison.",
          ],
          [
            "Robustness Scope",
            "Single-asset parameter scans reuse the same costs, position sizing, and risk controls as the main backtest.",
          ],
        ].map(([title, body]) => (
          <article className="panel" key={title}>
            <h2 className="text-base font-semibold text-ink">{title}</h2>
            <p className="mt-2 text-sm leading-6 text-graphite">{body}</p>
          </article>
        ))}
      </section>
    </div>
  );
}
