from datetime import date, timedelta

import pandas as pd

from core.config import get_settings
from data.provider import MarketDataProvider, validate_price_data


class YahooFinanceProvider(MarketDataProvider):
    """Market data adapter around yfinance.

    Strategy and backtesting modules depend only on the normalized DataFrame
    contract, so this adapter can be replaced later without touching core logic.
    """

    def get_history(self, ticker: str, start_date: date, end_date: date) -> pd.DataFrame:
        try:
            import yfinance as yf
        except ImportError as exc:
            raise RuntimeError(
                "yfinance is not installed. Install backend requirements before fetching market data."
            ) from exc

        inclusive_end = end_date + timedelta(days=1)
        settings = get_settings()
        raw = yf.download(
            tickers=ticker,
            start=start_date.isoformat(),
            end=inclusive_end.isoformat(),
            auto_adjust=False,
            progress=False,
            group_by="column",
            threads=False,
            timeout=settings.yahoo_timeout_seconds,
        )
        if raw.empty:
            raise ValueError(f"No historical price data found for {ticker}.")

        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)

        normalized = raw.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Adj Close": "adjusted_close",
                "Volume": "volume",
            }
        )
        return validate_price_data(normalized, ticker)
