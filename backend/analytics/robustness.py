from collections.abc import Callable
from statistics import median
from typing import Any

import numpy as np

from models.schemas import BacktestRequest, MetricSummary, RobustnessPoint, RobustnessResult

MetricRunner = Callable[[dict[str, Any]], MetricSummary]


def calculate_robustness(
    request: BacktestRequest,
    metric_runner: MetricRunner,
) -> RobustnessResult | None:
    if not request.robustness.enabled:
        return None

    grid = _parameter_grid(request)
    if grid is None:
        return None

    x_axis_label, y_axis_label, parameter_sets = grid
    points: list[RobustnessPoint] = []
    for x_value, y_value, parameters in parameter_sets:
        metrics = metric_runner(parameters)
        points.append(
            RobustnessPoint(
                x_value=float(x_value),
                y_value=float(y_value),
                parameters=parameters,
                metric_value=_metric_value(metrics, request.robustness.metric),
                total_return=metrics.total_return,
                annualized_volatility=metrics.annualized_volatility,
                sharpe_ratio=metrics.sharpe_ratio,
                maximum_drawdown=metrics.maximum_drawdown,
                number_of_trades=metrics.number_of_trades,
            )
        )

    finite_metric_values = [
        point.metric_value for point in points if point.metric_value is not None and np.isfinite(point.metric_value)
    ]
    if not finite_metric_values:
        return RobustnessResult(
            strategy_name=request.strategy.name,
            metric=request.robustness.metric,
            x_axis_label=x_axis_label,
            y_axis_label=y_axis_label,
            best_x_value=None,
            best_y_value=None,
            best_metric_value=None,
            median_metric_value=None,
            positive_return_share=0.0,
            stable_zone_share=0.0,
            tested_combinations=len(points),
            overfit_warning="None of the tested parameter combinations produced a finite robustness metric.",
            points=points,
        )

    best_point = max(
        points,
        key=lambda point: point.metric_value if point.metric_value is not None else float("-inf"),
    )
    best_metric = best_point.metric_value
    median_metric = float(median(finite_metric_values))
    positive_return_share = sum(1 for point in points if point.total_return > 0) / len(points)
    stable_zone_share = _stable_zone_share(points, best_metric)

    return RobustnessResult(
        strategy_name=request.strategy.name,
        metric=request.robustness.metric,
        x_axis_label=x_axis_label,
        y_axis_label=y_axis_label,
        best_x_value=best_point.x_value,
        best_y_value=best_point.y_value,
        best_metric_value=_round_optional(best_metric),
        median_metric_value=round(median_metric, 8),
        positive_return_share=round(positive_return_share, 8),
        stable_zone_share=round(stable_zone_share, 8),
        tested_combinations=len(points),
        overfit_warning=_overfit_warning(
            best_metric=best_metric,
            stable_zone_share=stable_zone_share,
            positive_return_share=positive_return_share,
        ),
        points=points,
    )


def _parameter_grid(
    request: BacktestRequest,
) -> tuple[str, str, list[tuple[float, float, dict[str, Any]]]] | None:
    params = request.strategy.parameters
    if request.strategy.name == "moving_average_crossover":
        current_short = int(params.get("short_window", 50))
        current_long = int(params.get("long_window", 200))
        short_values = _with_current([20, 50, 75, 100], current_short)
        long_values = _with_current([100, 150, 200, 250], current_long)
        parameter_sets = [
            (short_window, long_window, {"short_window": int(short_window), "long_window": int(long_window)})
            for short_window in short_values
            for long_window in long_values
            if short_window < long_window
        ]
        return "Short window", "Long window", parameter_sets

    if request.strategy.name == "rsi_mean_reversion":
        current_period = int(params.get("rsi_period", 14))
        current_oversold = float(params.get("oversold_threshold", 30))
        overbought = float(params.get("overbought_threshold", 70))
        period_values = _with_current([7, 14, 21, 28], current_period)
        oversold_values = _with_current([20, 25, 30, 35], current_oversold)
        parameter_sets = [
            (
                period,
                oversold,
                {
                    "rsi_period": int(period),
                    "oversold_threshold": float(oversold),
                    "overbought_threshold": overbought,
                },
            )
            for period in period_values
            for oversold in oversold_values
            if 0 < oversold < overbought < 100
        ]
        return "RSI period", "Oversold", parameter_sets

    if request.strategy.name == "momentum":
        current_lookback = int(params.get("lookback_period", 63))
        current_threshold = float(params.get("momentum_threshold", 0.02))
        holding_period = int(params.get("holding_period", 20))
        lookback_values = _with_current([21, 63, 126, 189], current_lookback)
        threshold_values = _with_current([0.0, 0.01, 0.02, 0.05], current_threshold)
        parameter_sets = [
            (
                lookback,
                threshold * 100,
                {
                    "lookback_period": int(lookback),
                    "momentum_threshold": float(threshold),
                    "holding_period": holding_period,
                },
            )
            for lookback in lookback_values
            for threshold in threshold_values
        ]
        return "Lookback period", "Threshold (%)", parameter_sets

    if request.strategy.name == "bollinger_bands":
        current_window = int(params.get("window", 20))
        current_multiplier = float(params.get("standard_deviation_multiplier", 2.0))
        mode = str(params.get("mode", "mean_reversion"))
        window_values = _with_current([10, 20, 40, 60], current_window)
        multiplier_values = _with_current([1.5, 2.0, 2.5, 3.0], current_multiplier)
        parameter_sets = [
            (
                window,
                multiplier,
                {
                    "window": int(window),
                    "standard_deviation_multiplier": float(multiplier),
                    "mode": mode,
                },
            )
            for window in window_values
            for multiplier in multiplier_values
        ]
        return "MA window", "Std multiplier", parameter_sets

    return None


def _metric_value(metrics: MetricSummary, metric_name: str) -> float | None:
    if metric_name == "total_return":
        return metrics.total_return
    if metric_name == "sharpe_ratio":
        return metrics.sharpe_ratio
    return None


def _stable_zone_share(points: list[RobustnessPoint], best_metric: float | None) -> float:
    if best_metric is None or not np.isfinite(best_metric):
        return 0.0
    if best_metric <= 0:
        return sum(1 for point in points if (point.metric_value or float("-inf")) >= 0) / len(points)
    threshold = best_metric * 0.75
    return sum(
        1
        for point in points
        if point.metric_value is not None and np.isfinite(point.metric_value) and point.metric_value >= threshold
    ) / len(points)


def _overfit_warning(
    best_metric: float | None,
    stable_zone_share: float,
    positive_return_share: float,
) -> str | None:
    if best_metric is None or not np.isfinite(best_metric):
        return "The robustness scan did not find a finite best metric."
    if best_metric <= 0:
        return "The best tested parameter set did not produce a positive robustness metric."
    if stable_zone_share < 0.2:
        return "Only a narrow part of the parameter grid is close to the best result."
    if positive_return_share < 0.5:
        return "Fewer than half of tested parameter sets produced a positive total return."
    return None


def _with_current(values: list[float], current: float) -> list[float]:
    combined = values + [current]
    return sorted({float(value) for value in combined})


def _round_optional(value: float | None) -> float | None:
    if value is None or not np.isfinite(value):
        return None
    return round(float(value), 8)
