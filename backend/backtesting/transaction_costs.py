from dataclasses import dataclass


@dataclass(frozen=True)
class TransactionCostModel:
    fixed_fee: float = 0.0
    percentage_fee: float = 0.0
    slippage_bps: float = 0.0
    bid_ask_spread_bps: float = 0.0

    @property
    def variable_rate(self) -> float:
        return self.percentage_fee + (self.slippage_bps / 10000) + (self.bid_ask_spread_bps / 10000)

    def calculate(self, trade_value: float) -> float:
        if trade_value < 0:
            raise ValueError("Trade value cannot be negative.")
        if trade_value == 0:
            return 0.0
        return self.fixed_fee + trade_value * self.variable_rate
