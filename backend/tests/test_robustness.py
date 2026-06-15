import unittest

from analytics.robustness import calculate_robustness
from models.schemas import (
    BacktestRequest,
    MetricSummary,
    RobustnessConfig,
    StrategyConfig,
)


def fake_metrics(parameters):
    short_window = parameters.get("short_window", 0)
    long_window = parameters.get("long_window", 0)
    score = (long_window - short_window) / 1000
    return MetricSummary(
        total_return=round(score, 8),
        annualized_return=round(score / 2, 8),
        annualized_volatility=0.12,
        sharpe_ratio=round(score * 3, 8),
        maximum_drawdown=-0.1,
        number_of_trades=2,
        win_rate=0.5,
        average_trade_return=0.01,
        best_trade=0.03,
        worst_trade=-0.01,
        total_transaction_costs=1.0,
        transaction_cost_pct_of_initial=0.0001,
        return_drag_from_costs=None,
        benchmark_return=None,
        alpha_relative_to_benchmark=None,
        tooltip_explanations={},
    )


class RobustnessTests(unittest.TestCase):
    def test_moving_average_grid_returns_best_and_summary(self):
        request = BacktestRequest(
            ticker="VFV.TO",
            start_date="2020-01-01",
            end_date="2021-01-01",
            strategy=StrategyConfig(
                name="moving_average_crossover",
                parameters={"short_window": 50, "long_window": 200},
            ),
            robustness=RobustnessConfig(enabled=True, metric="sharpe_ratio"),
        )

        result = calculate_robustness(request, fake_metrics)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.strategy_name, "moving_average_crossover")
        self.assertEqual(result.x_axis_label, "Short window")
        self.assertEqual(result.y_axis_label, "Long window")
        self.assertGreater(result.tested_combinations, 0)
        self.assertIsNotNone(result.best_metric_value)
        self.assertGreater(result.positive_return_share, 0)

    def test_disabled_scan_returns_none(self):
        request = BacktestRequest(
            ticker="VFV.TO",
            start_date="2020-01-01",
            end_date="2021-01-01",
            strategy=StrategyConfig(name="buy_and_hold", parameters={}),
        )

        self.assertIsNone(calculate_robustness(request, fake_metrics))


if __name__ == "__main__":
    unittest.main()
