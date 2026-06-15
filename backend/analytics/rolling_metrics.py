from math import sqrt

import pandas as pd

from analytics.metrics import TRADING_DAYS_PER_YEAR
from models.schemas import PortfolioPoint, RollingMetricPoint


def calculate_rolling_metrics(
    equity_curve: list[PortfolioPoint],
    window: int = 63,
) -> list[RollingMetricPoint]:
    if window < 2:
        raise ValueError("Rolling metric window must be at least 2.")
    if len(equity_curve) < window + 1:
        return []

    values = pd.Series(
        [point.value for point in equity_curve],
        index=pd.to_datetime([point.date for point in equity_curve]),
        dtype=float,
    )
    daily_returns = values.pct_change()
    rolling_return = values / values.shift(window) - 1
    rolling_volatility = daily_returns.rolling(window=window).std() * sqrt(TRADING_DAYS_PER_YEAR)
    rolling_sharpe = (
        daily_returns.rolling(window=window).mean()
        / daily_returns.rolling(window=window).std()
        * sqrt(TRADING_DAYS_PER_YEAR)
    )

    points: list[RollingMetricPoint] = []
    for timestamp in values.index:
        ret = rolling_return.loc[timestamp]
        vol = rolling_volatility.loc[timestamp]
        sharpe = rolling_sharpe.loc[timestamp]
        if pd.isna(ret) or pd.isna(vol) or pd.isna(sharpe):
            continue
        points.append(
            RollingMetricPoint(
                date=timestamp.date(),
                rolling_return=round(float(ret), 8),
                rolling_volatility=round(float(vol), 8),
                rolling_sharpe=round(float(sharpe), 8),
            )
        )
    return points

