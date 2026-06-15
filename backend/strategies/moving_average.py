import pandas as pd

from strategies.base import Strategy


class MovingAverageCrossoverStrategy(Strategy):
    name = "moving_average_crossover"

    def __init__(self, short_window: int = 50, long_window: int = 200):
        if short_window < 1 or long_window < 2:
            raise ValueError("Moving average windows must be positive.")
        if short_window >= long_window:
            raise ValueError("Short window must be smaller than long window.")
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, price_data: pd.DataFrame) -> pd.Series:
        if len(price_data) < self.long_window:
            raise ValueError(
                f"Need at least {self.long_window} rows for this moving average strategy."
            )

        prices = price_data["adjusted_close"]
        short_ma = prices.rolling(window=self.short_window, min_periods=self.short_window).mean()
        long_ma = prices.rolling(window=self.long_window, min_periods=self.long_window).mean()
        signal = (short_ma > long_ma).astype(float)
        signal[long_ma.isna()] = 0.0
        return signal.rename("signal")

