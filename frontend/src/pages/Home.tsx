import { BarChart3, ShieldCheck, SlidersHorizontal } from "lucide-react";

import { Disclaimer } from "../components/Disclaimer";

export function Home() {
  return (
    <div className="space-y-6">
      <section className="page-band">
        <div className="max-w-4xl">
          <p className="section-kicker">Canadian ETF Backtesting & Risk Lab</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-normal text-ink md:text-5xl">
            Test investment strategies under realistic costs, risk constraints, and parameter uncertainty.
          </h1>
          <p className="mt-4 max-w-3xl text-base leading-7 text-graphite">
            Phase 5 compares single-asset strategies and multi-ETF portfolios with costs,
            rebalancing, custom benchmarks, rolling risk, allocation diagnostics, and parameter robustness.
          </p>
        </div>
      </section>

      <Disclaimer />

      <section className="grid gap-4 md:grid-cols-3">
        <div className="panel">
          <BarChart3 className="text-pine" size={24} />
          <h2 className="mt-3 text-base font-semibold text-ink">Backtest Core</h2>
          <p className="mt-2 text-sm leading-6 text-graphite">
            Signals are separated from execution, and close-based strategy signals trade on the next bar.
          </p>
        </div>
        <div className="panel">
          <ShieldCheck className="text-copper" size={24} />
          <h2 className="mt-3 text-base font-semibold text-ink">Risk Metrics</h2>
          <p className="mt-2 text-sm leading-6 text-graphite">
            Returns, volatility, Sharpe ratio, drawdown, rolling risk, benchmark return, alpha, and portfolio risk contribution.
          </p>
        </div>
        <div className="panel">
          <SlidersHorizontal className="text-wine" size={24} />
          <h2 className="mt-3 text-base font-semibold text-ink">Built to Extend</h2>
          <p className="mt-2 text-sm leading-6 text-graphite">
            The data provider, strategy interface, execution model, metrics module, and robustness scan are independently replaceable.
          </p>
        </div>
      </section>
    </div>
  );
}
