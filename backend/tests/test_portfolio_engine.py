import unittest

import pandas as pd

from backtesting.portfolio_engine import PortfolioRebalanceEngine
from backtesting.transaction_costs import TransactionCostModel
from models.schemas import PortfolioAllocation


def price_frame(values, start="2024-01-01"):
    index = pd.date_range(start, periods=len(values), freq="B")
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


def allocations(*pairs):
    return [PortfolioAllocation(ticker=ticker, weight=weight) for ticker, weight in pairs]


class PortfolioRebalanceEngineTests(unittest.TestCase):
    def test_buy_and_hold_portfolio_uses_target_weights(self):
        engine = PortfolioRebalanceEngine(
            initial_capital=1000.0,
            allocations=allocations(("AAA.TO", 0.6), ("BBB.TO", 0.4)),
            rebalancing_frequency="none",
        )

        result = engine.run(
            {
                "AAA.TO": price_frame([10.0, 20.0]),
                "BBB.TO": price_frame([10.0, 10.0]),
            }
        )

        self.assertAlmostEqual(result.portfolio_curve[0].value, 1000.0)
        self.assertAlmostEqual(result.portfolio_curve[-1].value, 1600.0)
        self.assertEqual(len(result.rebalance_events), 2)
        self.assertEqual(len(result.correlation_matrix), 4)

    def test_monthly_rebalance_returns_weights_to_target(self):
        index = pd.to_datetime(["2024-01-31", "2024-02-01"])
        first = price_frame([10.0, 20.0])
        second = price_frame([10.0, 10.0])
        first.index = index
        second.index = index
        engine = PortfolioRebalanceEngine(
            initial_capital=1000.0,
            allocations=allocations(("AAA.TO", 0.5), ("BBB.TO", 0.5)),
            rebalancing_frequency="monthly",
        )

        result = engine.run({"AAA.TO": first, "BBB.TO": second})

        self.assertAlmostEqual(result.portfolio_curve[-1].value, 1500.0)
        self.assertEqual(len(result.rebalance_events), 4)
        ending_weights = {allocation.ticker: allocation.ending_weight for allocation in result.allocation_results}
        self.assertAlmostEqual(ending_weights["AAA.TO"], 0.5)
        self.assertAlmostEqual(ending_weights["BBB.TO"], 0.5)

    def test_transaction_costs_reduce_initial_allocation(self):
        engine = PortfolioRebalanceEngine(
            initial_capital=1000.0,
            allocations=allocations(("AAA.TO", 0.5), ("BBB.TO", 0.5)),
            rebalancing_frequency="none",
            cost_model=TransactionCostModel(fixed_fee=5.0),
        )

        result = engine.run(
            {
                "AAA.TO": price_frame([10.0, 10.0]),
                "BBB.TO": price_frame([10.0, 10.0]),
            }
        )

        self.assertAlmostEqual(result.portfolio_curve[0].value, 990.0)
        self.assertAlmostEqual(sum(trade.transaction_cost for trade in result.trades), 10.0)
        self.assertEqual(result.trades[0].exit_reason, "rebalance_buy")


if __name__ == "__main__":
    unittest.main()
