import unittest

import pandas as pd

from strategies.bollinger import BollingerBandStrategy
from strategies.buy_and_hold import BuyAndHoldStrategy
from strategies.momentum import MomentumStrategy
from strategies.moving_average import MovingAverageCrossoverStrategy
from strategies.rsi import RSIMeanReversionStrategy


def sample_prices(values):
    index = pd.date_range("2024-01-01", periods=len(values), freq="B")
    return pd.DataFrame(
        {
            "open": values,
            "high": values,
            "low": values,
            "close": values,
            "adjusted_close": values,
            "volume": [1000] * len(values),
        },
        index=index,
    )


class StrategyTests(unittest.TestCase):
    def test_buy_and_hold_signal_is_always_invested(self):
        signals = BuyAndHoldStrategy().generate_signals(sample_prices([10, 11, 12]))
        self.assertEqual(signals.tolist(), [1.0, 1.0, 1.0])

    def test_moving_average_signal_turns_on_after_cross(self):
        data = sample_prices([1, 2, 3, 4, 5])
        signals = MovingAverageCrossoverStrategy(short_window=2, long_window=3).generate_signals(data)
        self.assertEqual(signals.tolist(), [0.0, 0.0, 1.0, 1.0, 1.0])

    def test_moving_average_rejects_invalid_windows(self):
        with self.assertRaises(ValueError):
            MovingAverageCrossoverStrategy(short_window=20, long_window=10)

    def test_momentum_holds_after_positive_signal(self):
        data = sample_prices([1.0, 1.0, 1.0, 1.1, 1.2, 1.3])
        signals = MomentumStrategy(
            lookback_period=2,
            momentum_threshold=0.05,
            holding_period=2,
        ).generate_signals(data)
        self.assertEqual(signals.tolist(), [0.0, 0.0, 0.0, 1.0, 1.0, 1.0])

    def test_rsi_mean_reversion_can_enter_after_oversold_reading(self):
        data = sample_prices([10.0, 9.0, 8.0, 7.0, 8.0, 9.0, 10.0, 11.0])
        signals = RSIMeanReversionStrategy(
            rsi_period=3,
            oversold_threshold=40,
            overbought_threshold=60,
        ).generate_signals(data)
        self.assertEqual(signals.iloc[0], 0.0)
        self.assertIn(1.0, signals.tolist())

    def test_bollinger_mean_reversion_enters_below_lower_band(self):
        data = sample_prices([10.0, 10.0, 10.0, 8.0, 9.0, 10.0])
        signals = BollingerBandStrategy(
            window=3,
            standard_deviation_multiplier=1.0,
            mode="mean_reversion",
        ).generate_signals(data)
        self.assertEqual(signals.tolist(), [0.0, 0.0, 0.0, 1.0, 0.0, 0.0])

    def test_bollinger_breakout_enters_above_upper_band(self):
        data = sample_prices([10.0, 10.0, 10.0, 12.0, 11.0, 10.0])
        signals = BollingerBandStrategy(
            window=3,
            standard_deviation_multiplier=1.0,
            mode="breakout",
        ).generate_signals(data)
        self.assertEqual(signals.tolist(), [0.0, 0.0, 0.0, 1.0, 0.0, 0.0])


if __name__ == "__main__":
    unittest.main()
