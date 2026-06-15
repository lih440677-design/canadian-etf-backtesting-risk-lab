import { FormEvent, useEffect, useMemo, useState } from "react";
import { Play, Plus, RotateCcw, Trash2 } from "lucide-react";

import { fetchAssetPresets } from "../api/client";
import type {
  AssetPreset,
  BacktestRequest,
  RebalancingFrequency,
  RobustnessMetric,
  StrategyName,
} from "../types/backtest";

interface BacktestFormProps {
  loading: boolean;
  onRun: (request: BacktestRequest) => void;
}

const CUSTOM_PRESET_VALUE = "__custom__";
type LabMode = "single" | "portfolio";

interface PortfolioRow {
  id: string;
  ticker: string;
  weight: number;
}

const DEFAULT_ASSET_PRESETS: AssetPreset[] = [
  { ticker: "XIU.TO", name: "iShares S&P/TSX 60 Index ETF", category: "Canada Equity" },
  { ticker: "XIC.TO", name: "iShares Core S&P/TSX Capped Composite ETF", category: "Canada Equity" },
  { ticker: "VCN.TO", name: "Vanguard FTSE Canada All Cap Index ETF", category: "Canada Equity" },
  { ticker: "ZCN.TO", name: "BMO S&P/TSX Capped Composite ETF", category: "Canada Equity" },
  { ticker: "VFV.TO", name: "Vanguard S&P 500 Index ETF", category: "US Equity" },
  { ticker: "ZSP.TO", name: "BMO S&P 500 Index ETF", category: "US Equity" },
  { ticker: "XUS.TO", name: "iShares Core S&P 500 Index ETF", category: "US Equity" },
  { ticker: "VUN.TO", name: "Vanguard US Total Market Index ETF", category: "US Equity" },
  { ticker: "XSP.TO", name: "iShares Core S&P 500 CAD-Hedged ETF", category: "US Equity" },
  { ticker: "QQC.TO", name: "Invesco NASDAQ 100 Index ETF", category: "Growth" },
  { ticker: "XQQ.TO", name: "iShares NASDAQ 100 CAD-Hedged ETF", category: "Growth" },
  { ticker: "HXQ.TO", name: "Global X NASDAQ 100 Index ETF", category: "Growth" },
  { ticker: "XEF.TO", name: "iShares Core MSCI EAFE IMI Index ETF", category: "International Equity" },
  { ticker: "VIU.TO", name: "Vanguard FTSE Developed All Cap ex North America ETF", category: "International Equity" },
  { ticker: "ZEA.TO", name: "BMO MSCI EAFE Index ETF", category: "International Equity" },
  { ticker: "VEE.TO", name: "Vanguard FTSE Emerging Markets All Cap Index ETF", category: "International Equity" },
  { ticker: "XEC.TO", name: "iShares Core MSCI Emerging Markets IMI Index ETF", category: "International Equity" },
  { ticker: "XBB.TO", name: "iShares Core Canadian Universe Bond Index ETF", category: "Fixed Income" },
  { ticker: "VAB.TO", name: "Vanguard Canadian Aggregate Bond Index ETF", category: "Fixed Income" },
  { ticker: "ZAG.TO", name: "BMO Aggregate Bond Index ETF", category: "Fixed Income" },
  { ticker: "XSB.TO", name: "iShares Core Canadian Short Term Bond Index ETF", category: "Fixed Income" },
  { ticker: "VDY.TO", name: "Vanguard FTSE Canadian High Dividend Yield Index ETF", category: "Dividend" },
  { ticker: "XEI.TO", name: "iShares S&P/TSX Composite High Dividend Index ETF", category: "Dividend" },
  { ticker: "ZDV.TO", name: "BMO Canadian Dividend ETF", category: "Dividend" },
  { ticker: "CDZ.TO", name: "iShares S&P/TSX Canadian Dividend Aristocrats Index ETF", category: "Dividend" },
  { ticker: "XRE.TO", name: "iShares S&P/TSX Capped REIT Index ETF", category: "Real Assets" },
  { ticker: "ZRE.TO", name: "BMO Equal Weight REITs Index ETF", category: "Real Assets" },
  { ticker: "XGD.TO", name: "iShares S&P/TSX Global Gold Index ETF", category: "Real Assets" },
  { ticker: "RY.TO", name: "Royal Bank of Canada", category: "Canadian Stocks" },
  { ticker: "TD.TO", name: "Toronto-Dominion Bank", category: "Canadian Stocks" },
  { ticker: "BNS.TO", name: "Bank of Nova Scotia", category: "Canadian Stocks" },
  { ticker: "ENB.TO", name: "Enbridge Inc.", category: "Canadian Stocks" },
  { ticker: "CNQ.TO", name: "Canadian Natural Resources", category: "Canadian Stocks" },
  { ticker: "SHOP.TO", name: "Shopify Inc.", category: "Canadian Stocks" },
];

export function BacktestForm({ loading, onRun }: BacktestFormProps) {
  const [presets, setPresets] = useState<AssetPreset[]>(DEFAULT_ASSET_PRESETS);
  const [mode, setMode] = useState<LabMode>("single");
  const [ticker, setTicker] = useState("VFV.TO");
  const [benchmarkTicker, setBenchmarkTicker] = useState("");
  const [startDate, setStartDate] = useState("2020-01-01");
  const [endDate, setEndDate] = useState("2025-12-31");
  const [initialCapital, setInitialCapital] = useState(10000);
  const [positionSize, setPositionSize] = useState(100);
  const [strategy, setStrategy] = useState<StrategyName>("moving_average_crossover");
  const [shortWindow, setShortWindow] = useState(50);
  const [longWindow, setLongWindow] = useState(200);
  const [rsiPeriod, setRsiPeriod] = useState(14);
  const [oversoldThreshold, setOversoldThreshold] = useState(30);
  const [overboughtThreshold, setOverboughtThreshold] = useState(70);
  const [momentumLookback, setMomentumLookback] = useState(63);
  const [momentumThreshold, setMomentumThreshold] = useState(2);
  const [momentumHoldingPeriod, setMomentumHoldingPeriod] = useState(20);
  const [bollingerWindow, setBollingerWindow] = useState(20);
  const [bollingerMultiplier, setBollingerMultiplier] = useState(2);
  const [bollingerMode, setBollingerMode] = useState<"mean_reversion" | "breakout">("mean_reversion");
  const [rollingWindow, setRollingWindow] = useState(63);
  const [fixedFee, setFixedFee] = useState(0);
  const [percentageFee, setPercentageFee] = useState(0);
  const [slippageBps, setSlippageBps] = useState(0);
  const [bidAskSpreadBps, setBidAskSpreadBps] = useState(0);
  const [stopLossPct, setStopLossPct] = useState(0);
  const [takeProfitPct, setTakeProfitPct] = useState(0);
  const [robustnessEnabled, setRobustnessEnabled] = useState(false);
  const [robustnessMetric, setRobustnessMetric] = useState<RobustnessMetric>("sharpe_ratio");
  const [rebalancingFrequency, setRebalancingFrequency] = useState<RebalancingFrequency>("quarterly");
  const [portfolioRows, setPortfolioRows] = useState<PortfolioRow[]>([
    { id: "portfolio-1", ticker: "VFV.TO", weight: 40 },
    { id: "portfolio-2", ticker: "XIC.TO", weight: 30 },
    { id: "portfolio-3", ticker: "ZAG.TO", weight: 20 },
    { id: "portfolio-4", ticker: "XEF.TO", weight: 10 },
  ]);
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    fetchAssetPresets()
      .then((nextPresets) => {
        if (nextPresets.length > 0) {
          setPresets(nextPresets);
        }
      })
      .catch(() => setPresets(DEFAULT_ASSET_PRESETS));
  }, []);

  const normalizedTicker = ticker.trim().toUpperCase();
  const normalizedBenchmarkTicker = benchmarkTicker.trim().toUpperCase();
  const tickerPresetValue = presets.some((asset) => asset.ticker === normalizedTicker)
    ? normalizedTicker
    : CUSTOM_PRESET_VALUE;
  const benchmarkPresetValue =
    benchmarkTicker.trim() === ""
      ? ""
      : presets.some((asset) => asset.ticker === normalizedBenchmarkTicker)
        ? normalizedBenchmarkTicker
        : CUSTOM_PRESET_VALUE;

  const groupedPresets = useMemo(() => {
    return presets.reduce<Record<string, AssetPreset[]>>((groups, asset) => {
      groups[asset.category] = groups[asset.category] ?? [];
      groups[asset.category].push(asset);
      return groups;
    }, {});
  }, [presets]);

  const portfolioWeightTotal = portfolioRows.reduce((total, row) => total + row.weight, 0);

  function selectTickerPreset(value: string) {
    if (value !== CUSTOM_PRESET_VALUE) {
      setTicker(value);
    }
  }

  function updatePortfolioRow(id: string, updates: Partial<Pick<PortfolioRow, "ticker" | "weight">>) {
    setPortfolioRows((rows) =>
      rows.map((row) => (row.id === id ? { ...row, ...updates } : row)),
    );
  }

  function addPortfolioRow() {
    const fallbackTicker = presets.find(
      (asset) => !portfolioRows.some((row) => row.ticker.trim().toUpperCase() === asset.ticker),
    )?.ticker;
    setPortfolioRows((rows) => [
      ...rows,
      {
        id: `portfolio-${Date.now()}`,
        ticker: fallbackTicker ?? "",
        weight: 0,
      },
    ]);
  }

  function removePortfolioRow(id: string) {
    setPortfolioRows((rows) => rows.filter((row) => row.id !== id));
  }

  function selectBenchmarkPreset(value: string) {
    if (value === "") {
      setBenchmarkTicker("");
      return;
    }
    if (value !== CUSTOM_PRESET_VALUE) {
      setBenchmarkTicker(value);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    submitBacktest();
  }

  function submitBacktest() {
    setLocalError(null);

    if (new Date(startDate) >= new Date(endDate)) {
      setLocalError("Start date must be before end date.");
      return;
    }
    if (initialCapital <= 0) {
      setLocalError("Initial capital must be greater than zero.");
      return;
    }
    if (mode === "portfolio") {
      const cleanedRows = portfolioRows
        .map((row) => ({ ticker: row.ticker.trim().toUpperCase(), weight: row.weight }))
        .filter((row) => row.ticker || row.weight > 0);
      const tickers = cleanedRows.map((row) => row.ticker);
      if (cleanedRows.length < 2) {
        setLocalError("Portfolio mode needs at least two tickers.");
        return;
      }
      if (cleanedRows.some((row) => !row.ticker || row.weight <= 0)) {
        setLocalError("Each portfolio row needs a ticker and a positive weight.");
        return;
      }
      if (new Set(tickers).size !== tickers.length) {
        setLocalError("Portfolio tickers must be unique.");
        return;
      }
      const totalWeight = cleanedRows.reduce((total, row) => total + row.weight, 0);
      if (Math.abs(totalWeight - 100) > 0.01) {
        setLocalError("Portfolio weights must add up to 100%.");
        return;
      }
      if ([fixedFee, percentageFee, slippageBps, bidAskSpreadBps].some((value) => value < 0)) {
        setLocalError("Costs cannot be negative.");
        return;
      }
      onRun({
        ticker: "PORTFOLIO",
        start_date: startDate,
        end_date: endDate,
        initial_capital: initialCapital,
        position_size: 1,
        strategy: {
          name: "buy_and_hold",
          parameters: {},
        },
        benchmark_ticker: benchmarkTicker.trim() ? benchmarkTicker.trim().toUpperCase() : null,
        transaction_costs: {
          fixed_fee: fixedFee,
          percentage_fee: percentageFee / 100,
          slippage_bps: slippageBps,
          bid_ask_spread_bps: bidAskSpreadBps,
        },
        risk_controls: {
          stop_loss_pct: null,
          take_profit_pct: null,
        },
        rolling_window: rollingWindow,
        portfolio_allocations: cleanedRows.map((row) => ({
          ticker: row.ticker,
          weight: row.weight / 100,
        })),
        rebalancing_frequency: rebalancingFrequency,
        robustness: {
          enabled: false,
          metric: robustnessMetric,
        },
      });
      return;
    }
    if (strategy === "moving_average_crossover" && shortWindow >= longWindow) {
      setLocalError("Short window must be smaller than long window.");
      return;
    }
    if (strategy === "rsi_mean_reversion" && oversoldThreshold >= overboughtThreshold) {
      setLocalError("RSI oversold threshold must be below the overbought threshold.");
      return;
    }
    if (rollingWindow < 2 || rollingWindow > 252) {
      setLocalError("Rolling window must be between 2 and 252 trading days.");
      return;
    }
    if ([fixedFee, percentageFee, slippageBps, bidAskSpreadBps, stopLossPct, takeProfitPct].some((value) => value < 0)) {
      setLocalError("Costs and risk control values cannot be negative.");
      return;
    }
    if (stopLossPct >= 100) {
      setLocalError("Stop-loss must be less than 100%.");
      return;
    }

    onRun({
      ticker: ticker.trim().toUpperCase(),
      start_date: startDate,
      end_date: endDate,
      initial_capital: initialCapital,
      position_size: positionSize / 100,
      strategy: {
        name: strategy,
        parameters: buildStrategyParameters(),
      },
      benchmark_ticker: benchmarkTicker.trim() ? benchmarkTicker.trim().toUpperCase() : null,
      transaction_costs: {
        fixed_fee: fixedFee,
        percentage_fee: percentageFee / 100,
        slippage_bps: slippageBps,
        bid_ask_spread_bps: bidAskSpreadBps,
      },
      risk_controls: {
        stop_loss_pct: stopLossPct > 0 ? stopLossPct / 100 : null,
        take_profit_pct: takeProfitPct > 0 ? takeProfitPct / 100 : null,
      },
      rolling_window: rollingWindow,
      robustness: {
        enabled: robustnessEnabled && strategy !== "buy_and_hold",
        metric: robustnessMetric,
      },
    });
  }

  function buildStrategyParameters(): Record<string, number | string> {
    if (strategy === "moving_average_crossover") {
      return { short_window: shortWindow, long_window: longWindow };
    }
    if (strategy === "rsi_mean_reversion") {
      return {
        rsi_period: rsiPeriod,
        oversold_threshold: oversoldThreshold,
        overbought_threshold: overboughtThreshold,
      };
    }
    if (strategy === "momentum") {
      return {
        lookback_period: momentumLookback,
        momentum_threshold: momentumThreshold / 100,
        holding_period: momentumHoldingPeriod,
      };
    }
    if (strategy === "bollinger_bands") {
      return {
        window: bollingerWindow,
        standard_deviation_multiplier: bollingerMultiplier,
        mode: bollingerMode,
      };
    }
    return {};
  }

  function resetDefaults() {
    setMode("single");
    setTicker("VFV.TO");
    setBenchmarkTicker("");
    setStartDate("2020-01-01");
    setEndDate("2025-12-31");
    setInitialCapital(10000);
    setPositionSize(100);
    setStrategy("moving_average_crossover");
    setShortWindow(50);
    setLongWindow(200);
    setRsiPeriod(14);
    setOversoldThreshold(30);
    setOverboughtThreshold(70);
    setMomentumLookback(63);
    setMomentumThreshold(2);
    setMomentumHoldingPeriod(20);
    setBollingerWindow(20);
    setBollingerMultiplier(2);
    setBollingerMode("mean_reversion");
    setRollingWindow(63);
    setFixedFee(0);
    setPercentageFee(0);
    setSlippageBps(0);
    setBidAskSpreadBps(0);
    setStopLossPct(0);
    setTakeProfitPct(0);
    setRobustnessEnabled(false);
    setRobustnessMetric("sharpe_ratio");
    setRebalancingFrequency("quarterly");
    setPortfolioRows([
      { id: "portfolio-1", ticker: "VFV.TO", weight: 40 },
      { id: "portfolio-2", ticker: "XIC.TO", weight: 30 },
      { id: "portfolio-3", ticker: "ZAG.TO", weight: 20 },
      { id: "portfolio-4", ticker: "XEF.TO", weight: 10 },
    ]);
    setLocalError(null);
  }

  return (
    <form className="panel space-y-5" onSubmit={handleSubmit}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-ink">Backtest Lab</h2>
          <p className="mt-1 text-sm text-graphite">Canadian stocks, ETFs, and portfolio rebalancing.</p>
        </div>
        <button
          type="button"
          onClick={resetDefaults}
          className="icon-button"
          title="Reset defaults"
          aria-label="Reset defaults"
        >
          <RotateCcw size={18} />
        </button>
      </div>

      <div className="space-y-3">
        <span className="text-sm font-medium text-ink">Mode</span>
        <div className="segmented">
          <button
            type="button"
            className={mode === "single" ? "active" : ""}
            onClick={() => setMode("single")}
          >
            Single Asset
          </button>
          <button
            type="button"
            className={mode === "portfolio" ? "active" : ""}
            onClick={() => setMode("portfolio")}
          >
            Portfolio
          </button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {mode === "single" && (
          <label className="field">
            <span>Ticker</span>
            <div className="symbol-row">
              <select
                value={tickerPresetValue}
                onChange={(event) => selectTickerPreset(event.target.value)}
                aria-label="Ticker preset"
              >
                <option value={CUSTOM_PRESET_VALUE}>Custom ticker</option>
                {Object.entries(groupedPresets).map(([category, assets]) => (
                  <optgroup key={category} label={category}>
                    {assets.map((asset) => (
                      <option key={`${category}-${asset.ticker}`} value={asset.ticker}>
                        {asset.ticker} - {asset.name}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
              <input
                list="asset-presets"
                value={ticker}
                onChange={(event) => setTicker(event.target.value)}
                placeholder="VFV.TO"
                required
              />
            </div>
          </label>
        )}

        <label className="field">
          <span>Benchmark</span>
          <div className="symbol-row">
            <select
              value={benchmarkPresetValue}
              onChange={(event) => selectBenchmarkPreset(event.target.value)}
              aria-label="Benchmark preset"
            >
              <option value="">{mode === "portfolio" ? "Default: XIU.TO" : "Same as ticker"}</option>
              <option value={CUSTOM_PRESET_VALUE}>Custom benchmark</option>
              {Object.entries(groupedPresets).map(([category, assets]) => (
                <optgroup key={category} label={category}>
                  {assets.map((asset) => (
                    <option key={`${category}-${asset.ticker}`} value={asset.ticker}>
                      {asset.ticker} - {asset.name}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
            <input
              list="asset-presets"
              value={benchmarkTicker}
              onChange={(event) => setBenchmarkTicker(event.target.value)}
              placeholder={mode === "portfolio" ? "Default: XIU.TO" : "Same as ticker"}
            />
          </div>
        </label>

        <datalist id="asset-presets">
          {Object.entries(groupedPresets).flatMap(([category, assets]) =>
            assets.map((asset) => (
              <option key={`${category}-${asset.ticker}`} value={asset.ticker}>
                {asset.name}
              </option>
            )),
          )}
        </datalist>

        {mode === "single" && (
          <div className="ticker-universe md:col-span-2" data-testid="ticker-universe">
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm font-medium text-ink">Preset universe</span>
              <span className="text-xs font-semibold text-graphite">{presets.length} tickers</span>
            </div>
            <div className="preset-universe">
              {Object.entries(groupedPresets).map(([category, assets]) => (
                <section key={category} className="preset-category" aria-label={category}>
                  <h3>{category}</h3>
                  <div className="preset-chip-grid">
                    {assets.map((asset) => (
                      <button
                        key={asset.ticker}
                        type="button"
                        className={`preset-chip ${normalizedTicker === asset.ticker ? "active" : ""}`}
                        onClick={() => setTicker(asset.ticker)}
                        aria-pressed={normalizedTicker === asset.ticker}
                        title={asset.name}
                      >
                        <strong>{asset.ticker}</strong>
                        <span>{asset.name}</span>
                      </button>
                    ))}
                  </div>
                </section>
              ))}
            </div>
          </div>
        )}

        {mode === "portfolio" && (
          <div className="portfolio-builder md:col-span-2" data-testid="portfolio-builder">
            <div className="portfolio-builder-header">
              <div>
                <span className="text-sm font-medium text-ink">Portfolio allocations</span>
                <p className="mt-1 text-xs text-graphite">Weights must total 100%.</p>
              </div>
              <div className={`weight-pill ${Math.abs(portfolioWeightTotal - 100) <= 0.01 ? "ok" : "warn"}`}>
                {portfolioWeightTotal.toFixed(1)}%
              </div>
            </div>
            <div className="portfolio-rows">
              {portfolioRows.map((row) => {
                const rowTicker = row.ticker.trim().toUpperCase();
                const rowPresetValue = presets.some((asset) => asset.ticker === rowTicker)
                  ? rowTicker
                  : CUSTOM_PRESET_VALUE;
                return (
                  <div className="portfolio-row" key={row.id}>
                    <label className="field">
                      <span>Ticker</span>
                      <select
                        value={rowPresetValue}
                        onChange={(event) => {
                          if (event.target.value !== CUSTOM_PRESET_VALUE) {
                            updatePortfolioRow(row.id, { ticker: event.target.value });
                          }
                        }}
                        aria-label="Portfolio ticker preset"
                      >
                        <option value={CUSTOM_PRESET_VALUE}>Custom ticker</option>
                        {Object.entries(groupedPresets).map(([category, assets]) => (
                          <optgroup key={category} label={category}>
                            {assets.map((asset) => (
                              <option key={`${row.id}-${category}-${asset.ticker}`} value={asset.ticker}>
                                {asset.ticker} - {asset.name}
                              </option>
                            ))}
                          </optgroup>
                        ))}
                      </select>
                    </label>
                    <label className="field">
                      <span>Manual ticker</span>
                      <input
                        list="asset-presets"
                        value={row.ticker}
                        onChange={(event) => updatePortfolioRow(row.id, { ticker: event.target.value })}
                        placeholder="VFV.TO"
                      />
                    </label>
                    <label className="field">
                      <span>Weight (%)</span>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        step="0.1"
                        value={row.weight}
                        onChange={(event) => updatePortfolioRow(row.id, { weight: Number(event.target.value) })}
                      />
                    </label>
                    <button
                      type="button"
                      className="icon-button self-end"
                      onClick={() => removePortfolioRow(row.id)}
                      disabled={portfolioRows.length <= 2}
                      title="Remove allocation"
                      aria-label="Remove allocation"
                    >
                      <Trash2 size={17} />
                    </button>
                  </div>
                );
              })}
            </div>
            <button type="button" className="secondary-button" onClick={addPortfolioRow}>
              <Plus size={17} />
              Add ticker
            </button>
          </div>
        )}

        <label className="field">
          <span>Start date</span>
          <input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
        </label>

        <label className="field">
          <span>End date</span>
          <input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} />
        </label>

        <label className="field">
          <span>Initial capital</span>
          <input
            type="number"
            min="1"
            step="100"
            value={initialCapital}
            onChange={(event) => setInitialCapital(Number(event.target.value))}
          />
        </label>

        {mode === "single" && (
          <label className="field">
            <span>Position size (%)</span>
            <input
              type="number"
              min="1"
              max="100"
              step="1"
              value={positionSize}
              onChange={(event) => setPositionSize(Number(event.target.value))}
            />
          </label>
        )}
      </div>

      {mode === "single" && (
        <div className="space-y-3">
          <span className="text-sm font-medium text-ink">Strategy</span>
          <div className="segmented strategy-options">
            <button
              type="button"
              className={strategy === "buy_and_hold" ? "active" : ""}
              onClick={() => setStrategy("buy_and_hold")}
            >
              Buy & Hold
            </button>
            <button
              type="button"
              className={strategy === "moving_average_crossover" ? "active" : ""}
              onClick={() => setStrategy("moving_average_crossover")}
            >
              MA Crossover
            </button>
            <button
              type="button"
              className={strategy === "rsi_mean_reversion" ? "active" : ""}
              onClick={() => setStrategy("rsi_mean_reversion")}
            >
              RSI
            </button>
            <button
              type="button"
              className={strategy === "momentum" ? "active" : ""}
              onClick={() => setStrategy("momentum")}
            >
              Momentum
            </button>
            <button
              type="button"
              className={strategy === "bollinger_bands" ? "active" : ""}
              onClick={() => setStrategy("bollinger_bands")}
            >
              Bollinger
            </button>
          </div>
        </div>
      )}

      {mode === "single" && strategy === "moving_average_crossover" && (
        <div className="grid gap-4 md:grid-cols-2">
          <label className="field">
            <span>Short window</span>
            <input
              type="number"
              min="1"
              value={shortWindow}
              onChange={(event) => setShortWindow(Number(event.target.value))}
            />
          </label>
          <label className="field">
            <span>Long window</span>
            <input
              type="number"
              min="2"
              value={longWindow}
              onChange={(event) => setLongWindow(Number(event.target.value))}
            />
          </label>
        </div>
      )}

      {mode === "single" && strategy === "rsi_mean_reversion" && (
        <div className="grid gap-4 md:grid-cols-3">
          <label className="field">
            <span>RSI period</span>
            <input
              type="number"
              min="2"
              value={rsiPeriod}
              onChange={(event) => setRsiPeriod(Number(event.target.value))}
            />
          </label>
          <label className="field">
            <span>Oversold</span>
            <input
              type="number"
              min="1"
              max="99"
              value={oversoldThreshold}
              onChange={(event) => setOversoldThreshold(Number(event.target.value))}
            />
          </label>
          <label className="field">
            <span>Overbought</span>
            <input
              type="number"
              min="1"
              max="99"
              value={overboughtThreshold}
              onChange={(event) => setOverboughtThreshold(Number(event.target.value))}
            />
          </label>
        </div>
      )}

      {mode === "single" && strategy === "momentum" && (
        <div className="grid gap-4 md:grid-cols-3">
          <label className="field">
            <span>Lookback period</span>
            <input
              type="number"
              min="1"
              value={momentumLookback}
              onChange={(event) => setMomentumLookback(Number(event.target.value))}
            />
          </label>
          <label className="field">
            <span>Threshold (%)</span>
            <input
              type="number"
              min="0"
              step="0.1"
              value={momentumThreshold}
              onChange={(event) => setMomentumThreshold(Number(event.target.value))}
            />
          </label>
          <label className="field">
            <span>Holding period</span>
            <input
              type="number"
              min="1"
              value={momentumHoldingPeriod}
              onChange={(event) => setMomentumHoldingPeriod(Number(event.target.value))}
            />
          </label>
        </div>
      )}

      {mode === "single" && strategy === "bollinger_bands" && (
        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <label className="field">
              <span>MA window</span>
              <input
                type="number"
                min="2"
                value={bollingerWindow}
                onChange={(event) => setBollingerWindow(Number(event.target.value))}
              />
            </label>
            <label className="field">
              <span>Std multiplier</span>
              <input
                type="number"
                min="0.1"
                step="0.1"
                value={bollingerMultiplier}
                onChange={(event) => setBollingerMultiplier(Number(event.target.value))}
              />
            </label>
          </div>
          <div className="segmented">
            <button
              type="button"
              className={bollingerMode === "mean_reversion" ? "active" : ""}
              onClick={() => setBollingerMode("mean_reversion")}
            >
              Mean Reversion
            </button>
            <button
              type="button"
              className={bollingerMode === "breakout" ? "active" : ""}
              onClick={() => setBollingerMode("breakout")}
            >
              Breakout
            </button>
          </div>
        </div>
      )}

      <div className="space-y-3">
        <span className="text-sm font-medium text-ink">Transaction Costs</span>
        <div className="grid gap-4 md:grid-cols-2">
          <label className="field">
            <span>Fixed fee</span>
            <input
              type="number"
              min="0"
              step="0.01"
              value={fixedFee}
              onChange={(event) => setFixedFee(Number(event.target.value))}
            />
          </label>
          <label className="field">
            <span>Percentage fee (%)</span>
            <input
              type="number"
              min="0"
              step="0.001"
              value={percentageFee}
              onChange={(event) => setPercentageFee(Number(event.target.value))}
            />
          </label>
          <label className="field">
            <span>Slippage (bps)</span>
            <input
              type="number"
              min="0"
              step="0.1"
              value={slippageBps}
              onChange={(event) => setSlippageBps(Number(event.target.value))}
            />
          </label>
          <label className="field">
            <span>Bid-ask spread (bps)</span>
            <input
              type="number"
              min="0"
              step="0.1"
              value={bidAskSpreadBps}
              onChange={(event) => setBidAskSpreadBps(Number(event.target.value))}
            />
          </label>
        </div>
      </div>

      {mode === "single" && (
        <div className="space-y-3">
          <span className="text-sm font-medium text-ink">Risk Controls</span>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="field">
              <span>Stop-loss (%)</span>
              <input
                type="number"
                min="0"
                max="99.99"
                step="0.1"
                value={stopLossPct}
                onChange={(event) => setStopLossPct(Number(event.target.value))}
              />
            </label>
            <label className="field">
              <span>Take-profit (%)</span>
              <input
                type="number"
                min="0"
                step="0.1"
                value={takeProfitPct}
                onChange={(event) => setTakeProfitPct(Number(event.target.value))}
              />
            </label>
          </div>
        </div>
      )}

      {mode === "portfolio" && (
        <label className="field">
          <span>Rebalancing frequency</span>
          <select
            value={rebalancingFrequency}
            onChange={(event) => setRebalancingFrequency(event.target.value as RebalancingFrequency)}
          >
            <option value="none">None</option>
            <option value="monthly">Monthly</option>
            <option value="quarterly">Quarterly</option>
            <option value="annual">Annual</option>
          </select>
        </label>
      )}

      <label className="field">
        <span>Rolling metrics window</span>
        <input
          type="number"
          min="2"
          max="252"
          value={rollingWindow}
          onChange={(event) => setRollingWindow(Number(event.target.value))}
        />
      </label>

      {mode === "single" && (
        <div className="analysis-options" data-testid="robustness-options">
          <label className="toggle-row">
            <input
              type="checkbox"
              checked={robustnessEnabled}
              onChange={(event) => setRobustnessEnabled(event.target.checked)}
              disabled={strategy === "buy_and_hold"}
            />
            <span>Robustness scan</span>
          </label>
          <label className="field">
            <span>Scan metric</span>
            <select
              value={robustnessMetric}
              onChange={(event) => setRobustnessMetric(event.target.value as RobustnessMetric)}
              disabled={!robustnessEnabled || strategy === "buy_and_hold"}
            >
              <option value="sharpe_ratio">Sharpe ratio</option>
              <option value="total_return">Total return</option>
            </select>
          </label>
        </div>
      )}

      {localError && <div className="rounded-md bg-rose-50 px-3 py-2 text-sm text-wine">{localError}</div>}

      <button type="button" className="primary-button w-full" disabled={loading} onClick={submitBacktest}>
        <Play size={18} />
        {loading ? "Running..." : "Run Backtest"}
      </button>
    </form>
  );
}
