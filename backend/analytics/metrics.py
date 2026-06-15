from math import sqrt

import numpy as np
import pandas as pd

from models.schemas import MetricSummary, PortfolioPoint, TradeRecord

TRADING_DAYS_PER_YEAR = 252

METRIC_TOOLTIPS = {
    "total_return": "Total percentage gain or loss over the full backtest period.",
    "annualized_return": "Compounded yearly return implied by the backtest period.",
    "annualized_volatility": "Annualized variation in daily portfolio returns.",
    "sharpe_ratio": "Risk-adjusted return using volatility as the risk measure.",
    "maximum_drawdown": "Largest peak-to-trough portfolio decline during the test.",
    "number_of_trades": "Completed round-trip trades with both entry and exit.",
    "win_rate": "Share of completed trades that ended with a positive net profit.",
    "average_trade_return": "Average completed trade profit divided by entry value.",
    "best_trade": "Best completed trade return.",
    "worst_trade": "Worst completed trade return.",
    "total_transaction_costs": "Total fixed, percentage, slippage, and spread costs deducted during trades.",
    "transaction_cost_pct_of_initial": "Total transaction costs divided by initial capital.",
    "return_drag_from_costs": "Before-cost total return minus after-cost total return.",
    "benchmark_return": "Total return of the selected benchmark over the same period.",
    "alpha_relative_to_benchmark": "Strategy total return minus benchmark total return.",
}


def total_return(values: list[float]) -> float:
    if len(values) < 2 or values[0] == 0:
        return 0.0
    return values[-1] / values[0] - 1


def annualized_return(values: list[float], periods_per_year: int = TRADING_DAYS_PER_YEAR) -> float:
    if len(values) < 2 or values[0] <= 0 or values[-1] <= 0:
        return 0.0
    years = (len(values) - 1) / periods_per_year
    if years <= 0:
        return 0.0
    return (values[-1] / values[0]) ** (1 / years) - 1


def annualized_volatility(values: list[float], periods_per_year: int = TRADING_DAYS_PER_YEAR) -> float:
    returns = _daily_returns(values)
    if len(returns) < 2:
        return 0.0
    return float(np.std(returns, ddof=1) * sqrt(periods_per_year))


def sharpe_ratio(values: list[float], risk_free_rate: float = 0.0) -> float | None:
    ann_return = annualized_return(values)
    ann_vol = annualized_volatility(values)
    if ann_vol == 0:
        return None
    return (ann_return - risk_free_rate) / ann_vol


def maximum_drawdown(values: list[float]) -> float:
    if not values:
        return 0.0
    series = pd.Series(values, dtype=float)
    running_max = series.cummax()
    drawdowns = series / running_max - 1
    return float(drawdowns.min())


def calculate_metrics(
    equity_curve: list[PortfolioPoint],
    trades: list[TradeRecord],
    initial_capital: float,
    before_cost_total_return: float | None = None,
) -> MetricSummary:
    values = [point.value for point in equity_curve]
    completed_trades = [trade for trade in trades if trade.net_profit is not None]
    trade_returns = [_trade_return(trade) for trade in completed_trades]
    wins = [trade for trade in completed_trades if (trade.net_profit or 0) > 0]
    costs = sum(trade.transaction_cost for trade in trades)
    net_total_return = total_return(values)

    return MetricSummary(
        total_return=round(net_total_return, 8),
        annualized_return=round(annualized_return(values), 8),
        annualized_volatility=round(annualized_volatility(values), 8),
        sharpe_ratio=_round_optional(sharpe_ratio(values)),
        maximum_drawdown=round(maximum_drawdown(values), 8),
        number_of_trades=len(completed_trades),
        win_rate=round(len(wins) / len(completed_trades), 8) if completed_trades else None,
        average_trade_return=_round_optional(float(np.mean(trade_returns)) if trade_returns else None),
        best_trade=_round_optional(max(trade_returns) if trade_returns else None),
        worst_trade=_round_optional(min(trade_returns) if trade_returns else None),
        total_transaction_costs=round(costs, 6),
        transaction_cost_pct_of_initial=round(costs / initial_capital, 8) if initial_capital else 0.0,
        return_drag_from_costs=_round_optional(
            before_cost_total_return - net_total_return
            if before_cost_total_return is not None
            else None
        ),
        benchmark_return=None,
        alpha_relative_to_benchmark=None,
        tooltip_explanations=METRIC_TOOLTIPS,
    )


def _daily_returns(values: list[float]) -> np.ndarray:
    if len(values) < 2:
        return np.array([])
    series = pd.Series(values, dtype=float)
    return series.pct_change().dropna().to_numpy()


def _trade_return(trade: TradeRecord) -> float:
    if trade.exit_price is None or trade.entry_price == 0:
        return 0.0
    return trade.exit_price / trade.entry_price - 1


def _round_optional(value: float | None) -> float | None:
    if value is None:
        return None
    if not np.isfinite(value):
        return None
    return round(float(value), 8)
