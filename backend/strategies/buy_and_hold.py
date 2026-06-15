import pandas as pd

from strategies.base import Strategy


class BuyAndHoldStrategy(Strategy):
    name = "buy_and_hold"
    execute_on_first_bar = True

    def generate_signals(self, price_data: pd.DataFrame) -> pd.Series:
        if price_data.empty:
            raise ValueError("Buy and Hold requires non-empty price data.")
        return pd.Series(1.0, index=price_data.index, name="signal")
