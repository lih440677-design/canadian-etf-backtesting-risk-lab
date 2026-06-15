from dataclasses import dataclass
from datetime import date

from models.schemas import PortfolioPoint


@dataclass
class PortfolioState:
    cash: float
    shares: float = 0.0

    def value(self, price: float) -> float:
        return self.cash + self.shares * price

    def snapshot(self, current_date: date, price: float) -> PortfolioPoint:
        return PortfolioPoint(
            date=current_date,
            price=round(price, 6),
            cash=round(self.cash, 6),
            shares=round(self.shares, 8),
            value=round(self.value(price), 6),
        )

