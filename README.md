# Canadian ETF Backtesting & Risk Lab

Canadian ETF Backtesting & Risk Lab is a full-stack educational platform for testing Canadian equity and ETF strategies under realistic backtesting rules.

> This platform is for educational and research purposes only and does not constitute investment advice.

## What It Solves

The project asks whether common retail investing strategies still look attractive after accounting for execution timing, transaction costs, risk controls, strategy choice, rolling risk behavior, benchmark comparison, portfolio allocation, and parameter sensitivity. Phase 5 adds robustness scans for parameterized strategies; later phases extend persistence and exports.

The three differentiators are:

- Realistic transaction costs and slippage architecture
- Parameter robustness and overfitting analysis path
- Canadian equity and ETF focus

## Phase 5 Features

- React + TypeScript frontend with responsive Backtest Lab
- FastAPI backend with modular data, strategy, execution, and analytics layers
- Yahoo Finance data provider adapter
- Canadian ETF and stock presets plus manual ticker input
- Multi-ETF portfolio mode with custom weights
- Monthly, quarterly, annual, or no-rebalance portfolio simulations
- Buy and Hold strategy
- Moving Average Crossover strategy
- RSI Mean Reversion strategy
- Momentum strategy
- Bollinger Bands strategy with mean-reversion and breakout modes
- Adjusted-close portfolio accounting
- Next-bar execution for close-generated signals to reduce look-ahead bias
- Long-only execution with cash and position tracking
- Fixed fee, percentage fee, slippage, and bid-ask spread settings
- Stop-loss and take-profit controls that execute on the next trading day after a close-based trigger
- Portfolio value chart comparing after-cost strategy, before-cost strategy, and buy-and-hold benchmark
- Custom benchmark ticker input
- Rolling return, rolling volatility, and rolling Sharpe chart
- Robustness scan for MA Crossover, RSI, Momentum, and Bollinger strategy parameters
- Robustness heatmap with best parameter pair, stable-zone share, positive-grid share, and overfitting warning
- Portfolio allocation analysis with target weight, ending weight, return contribution, volatility, and risk contribution
- Correlation matrix for selected portfolio holdings
- Rebalance activity table with execution costs
- Core metrics: after-cost return, before-cost return, annualized return, annualized volatility, Sharpe ratio, maximum drawdown, trades, win rate, benchmark return, alpha, total transaction costs, cost-to-initial-capital, and cost drag
- Trade log with signal, stop-loss, take-profit, and open-trade exit status
- Unit tests for metrics, transaction costs, strategies, and accounting

## Architecture

```text
frontend React app
  -> POST /api/backtests/run
  -> FastAPI route validation
  -> YahooFinanceProvider normalized OHLCV data
  -> Strategy generates target exposure signals or PortfolioRebalanceEngine allocates target weights
  -> BacktestEngine executes next-bar long-only orders or scheduled portfolio rebalances
  -> Metrics module calculates performance
  -> Robustness module scans selected parameter grids when enabled
  -> JSON response renders charts, metrics, trades, allocations, and robustness results
```

Backtesting is intentionally separated into:

- `backend/data`: replaceable market data providers
- `backend/strategies`: signal generation only
- `backend/backtesting`: execution, cash, shares, and portfolio value
- `backend/analytics`: centralized metrics
- `backend/models`: API schemas and future persistence models

## Directory Structure

```text
backend/
  api/
  analytics/
  backtesting/
  core/
  data/
  models/
  strategies/
  tests/
frontend/
  src/
    api/
    components/
    pages/
    styles/
    types/
    utils/
```

## Local Setup

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/api/health
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open `http://localhost:5173`.

## Environment Variables

Root `.env.example` and `frontend/.env.example` include:

```text
BACKEND_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
YAHOO_TIMEOUT_SECONDS=20
VITE_API_BASE_URL=http://localhost:8000/api
```

No API keys are hardcoded.

## API

### `GET /api/health`

Returns service status.

### `GET /api/assets/presets`

Returns Canadian ETF and stock presets.

### `POST /api/backtests/run`

Example request:

```json
{
  "ticker": "VFV.TO",
  "start_date": "2020-01-01",
  "end_date": "2025-12-31",
  "initial_capital": 10000,
  "position_size": 1,
  "strategy": {
    "name": "rsi_mean_reversion",
    "parameters": {
      "rsi_period": 14,
      "oversold_threshold": 30,
      "overbought_threshold": 70
    }
  },
  "benchmark_ticker": "XIU.TO",
  "transaction_costs": {
    "fixed_fee": 4.95,
    "percentage_fee": 0.001,
    "slippage_bps": 5,
    "bid_ask_spread_bps": 5
  },
  "risk_controls": {
    "stop_loss_pct": 0.1,
    "take_profit_pct": 0.25
  },
  "rolling_window": 63,
  "robustness": {
    "enabled": true,
    "metric": "sharpe_ratio"
  }
}
```

Supported strategy names are `buy_and_hold`, `moving_average_crossover`, `rsi_mean_reversion`, `momentum`, and `bollinger_bands`.

Portfolio-mode request:

```json
{
  "ticker": "PORTFOLIO",
  "start_date": "2020-01-01",
  "end_date": "2025-12-31",
  "initial_capital": 10000,
  "position_size": 1,
  "strategy": {
    "name": "buy_and_hold",
    "parameters": {}
  },
  "benchmark_ticker": "XIU.TO",
  "transaction_costs": {
    "fixed_fee": 4.95,
    "percentage_fee": 0,
    "slippage_bps": 5,
    "bid_ask_spread_bps": 5
  },
  "risk_controls": {
    "stop_loss_pct": null,
    "take_profit_pct": null
  },
  "rolling_window": 63,
  "portfolio_allocations": [
    { "ticker": "VFV.TO", "weight": 0.4 },
    { "ticker": "XIC.TO", "weight": 0.3 },
    { "ticker": "ZAG.TO", "weight": 0.2 },
    { "ticker": "XEF.TO", "weight": 0.1 }
  ],
  "rebalancing_frequency": "quarterly"
}
```

Response includes after-cost strategy metrics, before-cost strategy metrics, benchmark metrics, after-cost curve, before-cost curve, benchmark curve, rolling metrics, trades or rebalance events, allocation analysis, correlation matrix, robustness results, and warnings.

## Tests

The test suite uses a small artificial price series and does not require network access:

```bash
PYTHONPATH=backend python3 -m unittest discover -s backend/tests
```

If `pytest` is installed, the same tests can also be run with:

```bash
PYTHONPATH=backend pytest backend/tests
```

## Docker

```bash
docker compose up --build
```

Then open:

- Frontend: `http://localhost:8080`
- Backend: `http://localhost:8000/api/health`

## Deployment

Frontend deployment target:

- Vercel or any static hosting provider
- Set `VITE_API_BASE_URL` to the deployed backend URL before build

Backend deployment target:

- Render, Railway, Fly.io, or similar
- Build from `backend/Dockerfile`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

## Backtesting Method Notes

- Strategies generate target exposure signals.
- Close-based signals are shifted by one row before execution.
- Phase 5 is long-only and does not allow negative positions.
- Portfolio value is always cash plus current position value.
- Buy and Hold can enter on the first available bar because it does not depend on a computed closing signal.
- Moving Average Crossover requires enough data for the long moving average window.
- Adjusted close is used for signal generation, portfolio value, and portfolio rebalancing.
- Transaction costs are deducted when each buy or sell executes.
- Stop-loss and take-profit triggers are evaluated after each close and execute on the next available trading day.
- Rolling metrics are calculated from the after-cost portfolio curve using the requested rolling window.
- Portfolio mode buys target weights on the first available overlapping date and rebalances on the selected calendar boundary.
- Robustness scans reuse the same ticker, dates, costs, position size, and risk controls as the main single-asset backtest.

## Known Limits

- Yahoo Finance data can contain missing data or revisions.
- Stop-loss and take-profit are close-based approximations, not intraday stop order simulations.
- Benchmark is a full buy-and-hold comparison using the same initial capital and no strategy risk controls.
- Portfolio mode requires overlapping price history across all selected holdings.
- Stop-loss and take-profit controls are disabled in portfolio mode.
- RSI, Momentum, and Bollinger strategies are simple rule-based educational implementations, not recommendations.
- Robustness scans test a finite grid and are not a guarantee that the best observed parameters will generalize.
- The current data source may not fully address delisted stocks, historical index membership, or survivorship bias.
- Backtests are historical simulations. Past performance and optimized parameters do not guarantee future results.

## Screenshot Placeholders

Add screenshots after running the app locally:

- Backtest Lab
- Results Dashboard
- Portfolio Value Chart
- Trade Log

## Future Features

- Additional risk controls such as volatility targeting and maximum drawdown warnings
- Saved tests with SQLite, then PostgreSQL migration path
- CSV exports and downloadable strategy analysis reports

## Investment Disclaimer

This platform is for educational and research purposes only and does not constitute investment advice. Nothing in this project should be interpreted as a recommendation to buy, sell, or hold any security.
