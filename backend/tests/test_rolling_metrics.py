import unittest
from datetime import date, timedelta

from analytics.rolling_metrics import calculate_rolling_metrics
from models.schemas import PortfolioPoint


class RollingMetricTests(unittest.TestCase):
    def test_rolling_metrics_return_points_after_window(self):
        curve = [
            PortfolioPoint(
                date=date(2024, 1, 1) + timedelta(days=index),
                price=100.0 + index,
                cash=0.0,
                shares=1.0,
                value=100.0 + index,
            )
            for index in range(8)
        ]

        points = calculate_rolling_metrics(curve, window=3)

        self.assertEqual(len(points), 5)
        self.assertEqual(points[0].date, date(2024, 1, 4))
        self.assertGreater(points[0].rolling_return, 0)
        self.assertGreater(points[0].rolling_volatility, 0)
        self.assertIsNotNone(points[0].rolling_sharpe)

    def test_rolling_metrics_return_empty_when_not_enough_data(self):
        curve = [
            PortfolioPoint(
                date=date(2024, 1, 1),
                price=100.0,
                cash=100.0,
                shares=0.0,
                value=100.0,
            )
        ]

        self.assertEqual(calculate_rolling_metrics(curve, window=3), [])


if __name__ == "__main__":
    unittest.main()
