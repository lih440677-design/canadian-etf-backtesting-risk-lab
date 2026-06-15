from abc import ABC, abstractmethod
from datetime import date

import pandas as pd


REQUIRED_COLUMNS = ["open", "high", "low", "close", "adjusted_close", "volume"]


class MarketDataProvider(ABC):
    @abstractmethod
    def get_history(self, ticker: str, start_date: date, end_date: date) -> pd.DataFrame:
        """Return historical OHLCV data indexed by date."""


def validate_price_data(data: pd.DataFrame, ticker: str) -> pd.DataFrame:
    if data.empty:
        raise ValueError(f"No historical price data found for {ticker}.")

    missing = [column for column in REQUIRED_COLUMNS if column not in data.columns]
    if missing:
        raise ValueError(f"Price data for {ticker} is missing columns: {', '.join(missing)}.")

    clean = data.copy()
    clean.index = pd.to_datetime(clean.index)
    clean = clean.sort_index()
    clean = clean.dropna(subset=["adjusted_close", "close"])
    clean = clean[clean["adjusted_close"] > 0]

    if len(clean) < 2:
        raise ValueError(f"Not enough valid price observations for {ticker}.")

    return clean

