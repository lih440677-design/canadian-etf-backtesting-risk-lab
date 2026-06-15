from abc import ABC, abstractmethod

import pandas as pd


class Strategy(ABC):
    name: str
    execute_on_first_bar: bool = False

    @abstractmethod
    def generate_signals(self, price_data: pd.DataFrame) -> pd.Series:
        """Return target exposure signals: 1.0 invested, 0.0 cash.

        Signals are based on information available at the close of each row.
        The backtesting engine executes signal changes on the next trading day
        to avoid look-ahead bias.
        """
