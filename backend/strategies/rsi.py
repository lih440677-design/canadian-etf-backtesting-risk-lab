import pandas as pd

from strategies.base import Strategy


class RSIMeanReversionStrategy(Strategy):
    name = "rsi_mean_reversion"

    def __init__(
        self,
        rsi_period: int = 14,
        oversold_threshold: float = 30,
        overbought_threshold: float = 70,
    ):
        if rsi_period < 2:
            raise ValueError("RSI period must be at least 2.")
        if not 0 < oversold_threshold < overbought_threshold < 100:
            raise ValueError("RSI thresholds must satisfy 0 < oversold < overbought < 100.")
        self.rsi_period = rsi_period
        self.oversold_threshold = oversold_threshold
        self.overbought_threshold = overbought_threshold

    def generate_signals(self, price_data: pd.DataFrame) -> pd.Series:
        if len(price_data) <= self.rsi_period:
            raise ValueError(f"Need more than {self.rsi_period} rows for this RSI strategy.")

        rsi = self._calculate_rsi(price_data["adjusted_close"])
        signal_values: list[float] = []
        invested = False

        for value in rsi:
            if pd.isna(value):
                signal_values.append(0.0)
                continue
            if value <= self.oversold_threshold:
                invested = True
            elif value >= self.overbought_threshold:
                invested = False
            signal_values.append(1.0 if invested else 0.0)

        return pd.Series(signal_values, index=price_data.index, name="signal")

    def _calculate_rsi(self, prices: pd.Series) -> pd.Series:
        delta = prices.diff()
        gains = delta.clip(lower=0)
        losses = -delta.clip(upper=0)
        average_gain = gains.rolling(window=self.rsi_period, min_periods=self.rsi_period).mean()
        average_loss = losses.rolling(window=self.rsi_period, min_periods=self.rsi_period).mean()
        rs = average_gain / average_loss
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.mask(average_loss == 0, 100)
        return rsi.fillna(50)
