import unittest

from backtesting.transaction_costs import TransactionCostModel


class TransactionCostTests(unittest.TestCase):
    def test_zero_cost_model(self):
        model = TransactionCostModel()
        self.assertEqual(model.calculate(1000.0), 0.0)
        self.assertEqual(model.calculate(0.0), 0.0)

    def test_fixed_and_percentage_costs(self):
        model = TransactionCostModel(fixed_fee=4.95, percentage_fee=0.001)
        self.assertAlmostEqual(model.calculate(1000.0), 5.95)

    def test_slippage_and_spread_costs(self):
        model = TransactionCostModel(slippage_bps=10, bid_ask_spread_bps=5)
        self.assertAlmostEqual(model.calculate(1000.0), 1.5)


if __name__ == "__main__":
    unittest.main()
