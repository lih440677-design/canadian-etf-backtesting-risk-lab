import pandas as pd

from strategies.base import Strategy


class MomentumStrategy(Strategy):
    name = "momentum"

    def __init__(
        self,
        lookback_period: int = 63,
        momentum_threshold: float = 0.02,
        holding_period: int = 20,
    ):
        if lookback_period < 1:
            raise ValueError("Lookback period must be positive.")
        if holding_period < 1:
            raise ValueError("Holding period must be positive.")
        if momentum_threshold < 0:
            raise ValueError("Momentum threshold cannot be negative.")
        self.lookback_period = lookback_period
        self.momentum_threshold = momentum_threshold
        self.holding_period = holding_period

    def generate_signals(self, price_data: pd.DataFrame) -> pd.Series:
        if len(price_data) <= self.lookback_period:
            raise ValueError(f"Need more than {self.lookback_period} rows for this momentum strategy.")

        momentum = price_data["adjusted_close"].pct_change(periods=self.lookback_period)
        signal_values: list[float] = []
        hold_counter = 0

        for value in momentum:
            if not pd.isna(value) and value >= self.momentum_threshold:
                hold_counter = self.holding_period
            signal_values.append(1.0 if hold_counter > 0 else 0.0)
            if hold_counter > 0:
                hold_counter -= 1

        return pd.Series(signal_values, index=price_data.index, name="signal")

