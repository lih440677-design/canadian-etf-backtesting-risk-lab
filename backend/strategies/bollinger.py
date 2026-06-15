import pandas as pd

from strategies.base import Strategy


class BollingerBandStrategy(Strategy):
    name = "bollinger_bands"

    def __init__(
        self,
        window: int = 20,
        standard_deviation_multiplier: float = 2.0,
        mode: str = "mean_reversion",
    ):
        if window < 2:
            raise ValueError("Bollinger window must be at least 2.")
        if standard_deviation_multiplier <= 0:
            raise ValueError("Standard deviation multiplier must be positive.")
        if mode not in {"mean_reversion", "breakout"}:
            raise ValueError("Bollinger mode must be mean_reversion or breakout.")
        self.window = window
        self.standard_deviation_multiplier = standard_deviation_multiplier
        self.mode = mode

    def generate_signals(self, price_data: pd.DataFrame) -> pd.Series:
        if len(price_data) < self.window:
            raise ValueError(f"Need at least {self.window} rows for this Bollinger strategy.")

        prices = price_data["adjusted_close"]
        middle = prices.rolling(window=self.window, min_periods=self.window).mean()
        standard_deviation = prices.rolling(window=self.window, min_periods=self.window).std()
        upper = middle + self.standard_deviation_multiplier * standard_deviation
        lower = middle - self.standard_deviation_multiplier * standard_deviation

        signal_values: list[float] = []
        invested = False
        for price, mid, upper_band, lower_band in zip(prices, middle, upper, lower):
            if pd.isna(mid) or pd.isna(upper_band) or pd.isna(lower_band):
                signal_values.append(0.0)
                continue

            if self.mode == "mean_reversion":
                if price < lower_band:
                    invested = True
                elif price >= mid:
                    invested = False
            else:
                if price > upper_band:
                    invested = True
                elif price <= mid:
                    invested = False
            signal_values.append(1.0 if invested else 0.0)

        return pd.Series(signal_values, index=price_data.index, name="signal")
