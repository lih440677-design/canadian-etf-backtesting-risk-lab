import unittest

from analytics.metrics import (
    annualized_return,
    annualized_volatility,
    maximum_drawdown,
    sharpe_ratio,
    total_return,
)


class MetricsTests(unittest.TestCase):
    def test_total_return(self):
        self.assertAlmostEqual(total_return([100.0, 110.0, 121.0]), 0.21)

    def test_annualized_return(self):
        values = [100.0, 121.0]
        self.assertAlmostEqual(annualized_return(values, periods_per_year=1), 0.21)

    def test_volatility_is_positive_for_variable_returns(self):
        values = [100.0, 110.0, 99.0, 120.0]
        self.assertGreater(annualized_volatility(values, periods_per_year=252), 0)

    def test_sharpe_is_none_when_volatility_is_zero(self):
        self.assertIsNone(sharpe_ratio([100.0, 100.0, 100.0]))

    def test_maximum_drawdown(self):
        self.assertAlmostEqual(maximum_drawdown([100.0, 120.0, 90.0, 110.0]), -0.25)


if __name__ == "__main__":
    unittest.main()

