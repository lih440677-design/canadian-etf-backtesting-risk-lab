import unittest

import pandas as pd

from backtesting.engine import BacktestEngine
from backtesting.execution import LongOnlyExecutionModel
from backtesting.transaction_costs import TransactionCostModel
from strategies.buy_and_hold import BuyAndHoldStrategy
from strategies.moving_average import MovingAverageCrossoverStrategy


def sample_prices(values):
    index = pd.date_range("2024-01-01", periods=len(values), freq="B")
    return pd.DataFrame(
        {
            "open": values,
            "high": values,
            "low": values,
            "close": values,
            "adjusted_close": values,
            "volume": [1000] * len(values),
        },
        index=index,
    )


class BacktestEngineTests(unittest.TestCase):
    def test_buy_and_hold_uses_initial_capital_without_creating_money(self):
        data = sample_prices([10.0, 12.0, 15.0])
        result = BacktestEngine(initial_capital=1000.0).run(data, BuyAndHoldStrategy())

        self.assertAlmostEqual(result.portfolio_curve[0].cash, 0.0)
        self.assertAlmostEqual(result.portfolio_curve[0].shares, 100.0)
        self.assertAlmostEqual(result.portfolio_curve[-1].value, 1500.0)

        for point in result.portfolio_curve:
            self.assertAlmostEqual(point.cash + point.shares * point.price, point.value, places=4)

    def test_moving_average_executes_next_day_to_avoid_look_ahead(self):
        data = sample_prices([10.0, 11.0, 12.0, 13.0, 14.0])
        strategy = MovingAverageCrossoverStrategy(short_window=2, long_window=3)
        result = BacktestEngine(initial_capital=1200.0).run(data, strategy)

        self.assertAlmostEqual(result.portfolio_curve[2].shares, 0.0)
        self.assertGreater(result.portfolio_curve[3].shares, 0.0)

    def test_cash_and_position_accounting_on_signal_exit(self):
        data = sample_prices([5.0, 6.0, 7.0, 6.0, 5.0, 4.0])
        strategy = MovingAverageCrossoverStrategy(short_window=2, long_window=3)
        result = BacktestEngine(initial_capital=1000.0).run(data, strategy)

        for point in result.portfolio_curve:
            self.assertGreaterEqual(point.cash, -1e-6)
            self.assertGreaterEqual(point.shares, -1e-8)
            self.assertAlmostEqual(point.cash + point.shares * point.price, point.value, places=4)

        self.assertEqual(len(result.trades), 1)
        self.assertEqual(result.trades[0].exit_reason, "signal_exit")

    def test_transaction_costs_are_deducted_at_trade_time(self):
        data = sample_prices([10.0, 12.0])
        engine = BacktestEngine(
            initial_capital=1000.0,
            execution_model=LongOnlyExecutionModel(
                TransactionCostModel(fixed_fee=5.0, percentage_fee=0.01)
            ),
        )
        result = engine.run(data, BuyAndHoldStrategy())

        self.assertAlmostEqual(result.portfolio_curve[0].cash, 0.0, places=4)
        self.assertAlmostEqual(result.trades[0].transaction_cost, 14.851485, places=5)
        self.assertLess(result.portfolio_curve[0].shares, 100.0)
        self.assertAlmostEqual(
            result.portfolio_curve[0].cash
            + result.portfolio_curve[0].shares * result.portfolio_curve[0].price,
            result.portfolio_curve[0].value,
            places=4,
        )

    def test_stop_loss_exits_on_next_bar_after_trigger(self):
        data = sample_prices([10.0, 10.0, 8.9, 8.0, 8.5])
        result = BacktestEngine(initial_capital=1000.0, stop_loss_pct=0.1).run(
            data,
            BuyAndHoldStrategy(),
        )

        completed = [trade for trade in result.trades if trade.net_profit is not None]
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0].exit_reason, "stop_loss")
        self.assertEqual(completed[0].exit_date.isoformat(), "2024-01-04")
        self.assertAlmostEqual(result.portfolio_curve[3].shares, 0.0)

    def test_take_profit_exits_on_next_bar_after_trigger(self):
        data = sample_prices([10.0, 10.0, 11.1, 12.0, 11.5])
        result = BacktestEngine(initial_capital=1000.0, take_profit_pct=0.1).run(
            data,
            BuyAndHoldStrategy(),
        )

        completed = [trade for trade in result.trades if trade.net_profit is not None]
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0].exit_reason, "take_profit")
        self.assertEqual(completed[0].exit_date.isoformat(), "2024-01-04")
        self.assertAlmostEqual(result.portfolio_curve[3].shares, 0.0)


if __name__ == "__main__":
    unittest.main()
