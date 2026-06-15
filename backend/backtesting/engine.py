from dataclasses import dataclass, field
from datetime import date

import pandas as pd

from backtesting.execution import LongOnlyExecutionModel
from backtesting.portfolio import PortfolioState
from models.schemas import PortfolioPoint, TradeRecord
from strategies.base import Strategy


class BacktestInputError(ValueError):
    """Raised when a backtest request is valid JSON but invalid financially."""


@dataclass
class BacktestResult:
    portfolio_curve: list[PortfolioPoint]
    trades: list[TradeRecord]
    warnings: list[str] = field(default_factory=list)


class BacktestEngine:
    def __init__(
        self,
        initial_capital: float,
        position_size: float = 1.0,
        stop_loss_pct: float | None = None,
        take_profit_pct: float | None = None,
        execution_model: LongOnlyExecutionModel | None = None,
    ):
        if initial_capital <= 0:
            raise BacktestInputError("Initial capital must be greater than zero.")
        if not 0 < position_size <= 1:
            raise BacktestInputError("Position size must be greater than 0 and at most 1.")
        if stop_loss_pct is not None and not 0 < stop_loss_pct < 1:
            raise BacktestInputError("Stop-loss must be greater than 0% and less than 100%.")
        if take_profit_pct is not None and take_profit_pct <= 0:
            raise BacktestInputError("Take-profit must be greater than 0%.")
        self.initial_capital = initial_capital
        self.position_size = position_size
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.execution_model = execution_model or LongOnlyExecutionModel()

    def run(self, price_data: pd.DataFrame, strategy: Strategy) -> BacktestResult:
        self._validate_price_data(price_data)
        signals = strategy.generate_signals(price_data).reindex(price_data.index).fillna(0.0)
        executable_signals = signals.shift(1).fillna(0.0)
        if strategy.execute_on_first_bar and not executable_signals.empty:
            executable_signals.iloc[0] = signals.iloc[0]

        portfolio = PortfolioState(cash=self.initial_capital)
        curve: list[PortfolioPoint] = []
        trades: list[TradeRecord] = []
        open_trade: TradeRecord | None = None
        warnings: list[str] = []
        pending_risk_exit_reason: str | None = None

        for timestamp, row in price_data.iterrows():
            current_date = timestamp.date()
            price = float(row["adjusted_close"])
            target_signal = float(executable_signals.loc[timestamp])
            exited_for_risk = False

            if pending_risk_exit_reason and portfolio.shares > 1e-12:
                open_trade = self._close_position(
                    portfolio=portfolio,
                    open_trade=open_trade,
                    trades=trades,
                    current_date=current_date,
                    price=price,
                    exit_reason=pending_risk_exit_reason,
                )
                pending_risk_exit_reason = None
                exited_for_risk = True
            elif pending_risk_exit_reason:
                pending_risk_exit_reason = None

            if not exited_for_risk and target_signal >= 1.0 and portfolio.shares <= 1e-12:
                cash_to_deploy = portfolio.cash * self.position_size
                execution = self.execution_model.buy_with_cash(cash_to_deploy, price)
                if execution.shares_delta > 0:
                    portfolio.cash += execution.cash_delta
                    portfolio.shares += execution.shares_delta
                    open_trade = TradeRecord(
                        entry_date=current_date,
                        entry_price=round(price, 6),
                        shares=round(execution.shares_delta, 8),
                        transaction_cost=round(execution.transaction_cost, 6),
                    )

            elif not exited_for_risk and target_signal <= 0.0 and portfolio.shares > 1e-12:
                open_trade = self._close_position(
                    portfolio=portfolio,
                    open_trade=open_trade,
                    trades=trades,
                    current_date=current_date,
                    price=price,
                    exit_reason="signal_exit",
                )

            current_value = portfolio.value(price)
            if portfolio.cash < -1e-6:
                raise BacktestInputError("Cash balance became negative during execution.")
            if portfolio.shares < -1e-10:
                raise BacktestInputError("Short positions are disabled in this version.")
            if current_value < -1e-6:
                raise BacktestInputError("Portfolio value became negative during execution.")
            curve.append(portfolio.snapshot(current_date=current_date, price=price))

            if open_trade is not None and portfolio.shares > 1e-12:
                pending_risk_exit_reason = self._risk_exit_reason(open_trade.entry_price, price)

        if open_trade is not None:
            warnings.append("The final trade remains open at the end of the backtest window.")
            open_trade.exit_reason = "open"
            trades.append(open_trade)

        return BacktestResult(portfolio_curve=curve, trades=trades, warnings=warnings)

    def _close_position(
        self,
        portfolio: PortfolioState,
        open_trade: TradeRecord | None,
        trades: list[TradeRecord],
        current_date: date,
        price: float,
        exit_reason: str,
    ) -> TradeRecord | None:
        execution = self.execution_model.sell_all(portfolio.shares, price)
        previous_shares = portfolio.shares
        portfolio.cash += execution.cash_delta
        portfolio.shares += execution.shares_delta
        if abs(portfolio.shares) < 1e-10:
            portfolio.shares = 0.0

        if open_trade is not None:
            gross_profit = (price - open_trade.entry_price) * previous_shares
            total_cost = open_trade.transaction_cost + execution.transaction_cost
            open_trade.exit_date = current_date
            open_trade.exit_price = round(price, 6)
            open_trade.gross_profit = round(gross_profit, 6)
            open_trade.transaction_cost = round(total_cost, 6)
            open_trade.net_profit = round(gross_profit - total_cost, 6)
            open_trade.holding_period = (current_date - open_trade.entry_date).days
            open_trade.exit_reason = exit_reason
            trades.append(open_trade)
        return None

    def _risk_exit_reason(self, entry_price: float, current_price: float) -> str | None:
        if self.stop_loss_pct is not None:
            stop_price = entry_price * (1 - self.stop_loss_pct)
            if current_price <= stop_price:
                return "stop_loss"
        if self.take_profit_pct is not None:
            take_profit_price = entry_price * (1 + self.take_profit_pct)
            if current_price >= take_profit_price:
                return "take_profit"
        return None

    @staticmethod
    def _validate_price_data(price_data: pd.DataFrame) -> None:
        if price_data.empty:
            raise BacktestInputError("Price data is empty.")
        if "adjusted_close" not in price_data.columns:
            raise BacktestInputError("Price data must contain adjusted_close.")
        if price_data["adjusted_close"].isna().any():
            raise BacktestInputError("Price data contains missing adjusted_close values.")
        if (price_data["adjusted_close"] <= 0).any():
            raise BacktestInputError("Price data contains non-positive adjusted_close values.")
