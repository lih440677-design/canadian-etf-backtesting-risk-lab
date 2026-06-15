from dataclasses import dataclass, field
from datetime import date
from math import sqrt
from typing import Literal

import numpy as np
import pandas as pd

from backtesting.execution import LongOnlyExecutionModel
from backtesting.transaction_costs import TransactionCostModel
from models.schemas import (
    AllocationResult,
    CorrelationCell,
    PortfolioAllocation,
    PortfolioPoint,
    RebalanceRecord,
    TradeRecord,
)

TRADING_DAYS_PER_YEAR = 252
RebalancingFrequency = Literal["none", "monthly", "quarterly", "annual"]


@dataclass
class PortfolioBacktestResult:
    portfolio_curve: list[PortfolioPoint]
    trades: list[TradeRecord]
    rebalance_events: list[RebalanceRecord]
    allocation_results: list[AllocationResult]
    correlation_matrix: list[CorrelationCell]
    warnings: list[str] = field(default_factory=list)


class PortfolioRebalanceEngine:
    def __init__(
        self,
        initial_capital: float,
        allocations: list[PortfolioAllocation],
        rebalancing_frequency: RebalancingFrequency = "quarterly",
        cost_model: TransactionCostModel | None = None,
    ):
        if initial_capital <= 0:
            raise ValueError("Initial capital must be greater than zero.")
        if len(allocations) < 2:
            raise ValueError("Portfolio mode requires at least two tickers.")
        self.initial_capital = initial_capital
        self.allocations = allocations
        self.rebalancing_frequency = rebalancing_frequency
        self.execution_model = LongOnlyExecutionModel(cost_model=cost_model or TransactionCostModel())

    def run(self, price_data_by_ticker: dict[str, pd.DataFrame]) -> PortfolioBacktestResult:
        prices = _build_price_frame(price_data_by_ticker)
        target_weights = {allocation.ticker: allocation.weight for allocation in self.allocations}
        shares = {allocation.ticker: 0.0 for allocation in self.allocations}
        cash = self.initial_capital
        curve: list[PortfolioPoint] = []
        trades: list[TradeRecord] = []
        rebalance_events: list[RebalanceRecord] = []
        warnings: list[str] = []

        previous_timestamp: pd.Timestamp | None = None
        for timestamp, row in prices.iterrows():
            if previous_timestamp is None or _is_rebalance_date(
                current=timestamp,
                previous=previous_timestamp,
                frequency=self.rebalancing_frequency,
            ):
                cash = self._rebalance(
                    cash=cash,
                    shares=shares,
                    prices=row,
                    target_weights=target_weights,
                    current_date=timestamp.date(),
                    trades=trades,
                    rebalance_events=rebalance_events,
                )

            portfolio_value = _portfolio_value(cash=cash, shares=shares, prices=row)
            if cash < -1e-6:
                raise ValueError("Cash balance became negative during portfolio rebalancing.")
            if portfolio_value < -1e-6:
                raise ValueError("Portfolio value became negative during portfolio rebalancing.")
            curve.append(
                PortfolioPoint(
                    date=timestamp.date(),
                    price=round((portfolio_value / self.initial_capital) * 100, 6),
                    cash=round(cash, 6),
                    shares=round(sum(shares.values()), 8),
                    value=round(portfolio_value, 6),
                )
            )
            previous_timestamp = timestamp

        if cash > self.initial_capital * 0.02:
            warnings.append("Portfolio retained more than 2% cash after costs and rebalancing.")

        return PortfolioBacktestResult(
            portfolio_curve=curve,
            trades=trades,
            rebalance_events=rebalance_events,
            allocation_results=_calculate_allocation_results(
                prices=prices,
                shares=shares,
                cash=cash,
                target_weights=target_weights,
            ),
            correlation_matrix=_calculate_correlation_matrix(prices),
            warnings=warnings,
        )

    def _rebalance(
        self,
        cash: float,
        shares: dict[str, float],
        prices: pd.Series,
        target_weights: dict[str, float],
        current_date: date,
        trades: list[TradeRecord],
        rebalance_events: list[RebalanceRecord],
    ) -> float:
        total_value = _portfolio_value(cash=cash, shares=shares, prices=prices)
        target_values = {
            ticker: total_value * target_weight for ticker, target_weight in target_weights.items()
        }
        current_values = {ticker: shares[ticker] * float(prices[ticker]) for ticker in shares}

        for ticker in shares:
            difference = target_values[ticker] - current_values[ticker]
            if difference >= -1e-8:
                continue
            price = float(prices[ticker])
            shares_to_sell = min(shares[ticker], abs(difference) / price)
            execution = self.execution_model.sell_all(shares_to_sell, price)
            if abs(execution.shares_delta) <= 1e-12:
                continue
            shares[ticker] += execution.shares_delta
            if abs(shares[ticker]) < 1e-10:
                shares[ticker] = 0.0
            cash += execution.cash_delta
            _record_rebalance(
                records=rebalance_events,
                trades=trades,
                current_date=current_date,
                ticker=ticker,
                action="sell",
                shares_delta=execution.shares_delta,
                price=price,
                transaction_cost=execution.transaction_cost,
                target_value=target_values[ticker],
                actual_value=shares[ticker] * price,
            )

        for ticker in shares:
            price = float(prices[ticker])
            current_value = shares[ticker] * price
            difference = target_values[ticker] - current_value
            if difference <= 1e-8 or cash <= 1e-8:
                continue
            execution = self.execution_model.buy_with_cash(min(difference, cash), price)
            if execution.shares_delta <= 1e-12:
                continue
            shares[ticker] += execution.shares_delta
            cash += execution.cash_delta
            _record_rebalance(
                records=rebalance_events,
                trades=trades,
                current_date=current_date,
                ticker=ticker,
                action="buy",
                shares_delta=execution.shares_delta,
                price=price,
                transaction_cost=execution.transaction_cost,
                target_value=target_values[ticker],
                actual_value=shares[ticker] * price,
            )

        return cash


def _build_price_frame(price_data_by_ticker: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if not price_data_by_ticker:
        raise ValueError("Portfolio price data is empty.")
    price_series = []
    for ticker, price_data in price_data_by_ticker.items():
        if "adjusted_close" not in price_data.columns:
            raise ValueError(f"Price data for {ticker} must contain adjusted_close.")
        series = price_data["adjusted_close"].rename(ticker)
        price_series.append(series)
    prices = pd.concat(price_series, axis=1, join="inner").dropna()
    if len(prices) < 2:
        raise ValueError("Not enough overlapping observations for portfolio backtest.")
    if (prices <= 0).any().any():
        raise ValueError("Portfolio price data contains non-positive adjusted_close values.")
    return prices


def _is_rebalance_date(
    current: pd.Timestamp,
    previous: pd.Timestamp,
    frequency: RebalancingFrequency,
) -> bool:
    if frequency == "none":
        return False
    if frequency == "monthly":
        return current.to_period("M") != previous.to_period("M")
    if frequency == "quarterly":
        return current.to_period("Q") != previous.to_period("Q")
    if frequency == "annual":
        return current.year != previous.year
    return False


def _portfolio_value(cash: float, shares: dict[str, float], prices: pd.Series) -> float:
    return cash + sum(shares[ticker] * float(prices[ticker]) for ticker in shares)


def _record_rebalance(
    records: list[RebalanceRecord],
    trades: list[TradeRecord],
    current_date: date,
    ticker: str,
    action: Literal["buy", "sell"],
    shares_delta: float,
    price: float,
    transaction_cost: float,
    target_value: float,
    actual_value: float,
) -> None:
    records.append(
        RebalanceRecord(
            date=current_date,
            ticker=ticker,
            action=action,
            shares_delta=round(shares_delta, 8),
            price=round(price, 6),
            transaction_cost=round(transaction_cost, 6),
            target_value=round(target_value, 6),
            actual_value=round(actual_value, 6),
        )
    )
    trades.append(
        TradeRecord(
            entry_date=current_date,
            entry_price=round(price, 6),
            shares=round(abs(shares_delta), 8),
            transaction_cost=round(transaction_cost, 6),
            exit_reason=f"rebalance_{action}",
        )
    )


def _calculate_allocation_results(
    prices: pd.DataFrame,
    shares: dict[str, float],
    cash: float,
    target_weights: dict[str, float],
) -> list[AllocationResult]:
    returns = prices.pct_change().dropna()
    tickers = list(target_weights)
    if len(returns) < 2:
        covariance = pd.DataFrame(0.0, index=tickers, columns=tickers)
    else:
        covariance = returns.cov() * TRADING_DAYS_PER_YEAR
    weights = np.array([target_weights[ticker] for ticker in tickers], dtype=float)
    portfolio_variance = float(weights @ covariance.loc[tickers, tickers].to_numpy() @ weights)
    marginal_risk = covariance.loc[tickers, tickers].to_numpy() @ weights
    final_prices = prices.iloc[-1]
    final_value = _portfolio_value(cash=cash, shares=shares, prices=final_prices)

    results: list[AllocationResult] = []
    for index, ticker in enumerate(tickers):
        asset_return = float(prices[ticker].iloc[-1] / prices[ticker].iloc[0] - 1)
        contribution = target_weights[ticker] * asset_return
        annualized_volatility = float(returns[ticker].std(ddof=1) * sqrt(TRADING_DAYS_PER_YEAR))
        if not np.isfinite(annualized_volatility):
            annualized_volatility = 0.0
        risk_contribution = (
            float(weights[index] * marginal_risk[index] / portfolio_variance)
            if portfolio_variance > 0
            else 0.0
        )
        ending_weight = (shares[ticker] * float(final_prices[ticker]) / final_value) if final_value else 0.0
        results.append(
            AllocationResult(
                ticker=ticker,
                target_weight=round(target_weights[ticker], 8),
                ending_weight=round(ending_weight, 8),
                contribution_to_return=round(contribution, 8),
                annualized_volatility=round(annualized_volatility, 8),
                risk_contribution=round(risk_contribution, 8),
            )
        )
    return results


def _calculate_correlation_matrix(prices: pd.DataFrame) -> list[CorrelationCell]:
    returns = prices.pct_change().dropna()
    if len(returns) < 2:
        correlations = pd.DataFrame(
            np.eye(len(prices.columns)),
            index=prices.columns,
            columns=prices.columns,
        )
    else:
        correlations = returns.corr().replace([np.inf, -np.inf], np.nan).fillna(0.0)
    cells: list[CorrelationCell] = []
    for row_ticker in correlations.index:
        for column_ticker in correlations.columns:
            cells.append(
                CorrelationCell(
                    row_ticker=row_ticker,
                    column_ticker=column_ticker,
                    correlation=round(float(correlations.loc[row_ticker, column_ticker]), 8),
                )
            )
    return cells
