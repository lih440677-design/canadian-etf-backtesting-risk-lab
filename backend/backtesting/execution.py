from dataclasses import dataclass

from backtesting.transaction_costs import TransactionCostModel


@dataclass(frozen=True)
class ExecutionResult:
    shares_delta: float
    cash_delta: float
    transaction_cost: float
    executed_value: float


class LongOnlyExecutionModel:
    def __init__(self, cost_model: TransactionCostModel | None = None):
        self.cost_model = cost_model or TransactionCostModel()

    def buy_with_cash(self, available_cash: float, price: float) -> ExecutionResult:
        if available_cash <= 0 or price <= 0:
            return ExecutionResult(0.0, 0.0, 0.0, 0.0)

        if self.cost_model.fixed_fee >= available_cash:
            return ExecutionResult(0.0, 0.0, 0.0, 0.0)

        gross_value = (available_cash - self.cost_model.fixed_fee) / (
            1 + self.cost_model.variable_rate
        )
        if gross_value <= 0:
            return ExecutionResult(0.0, 0.0, 0.0, 0.0)
        transaction_cost = self.cost_model.calculate(gross_value)
        if gross_value + transaction_cost > available_cash + 1e-8:
            return ExecutionResult(0.0, 0.0, 0.0, 0.0)
        shares = gross_value / price
        return ExecutionResult(
            shares_delta=shares,
            cash_delta=-(gross_value + transaction_cost),
            transaction_cost=transaction_cost,
            executed_value=gross_value,
        )

    def sell_all(self, shares: float, price: float) -> ExecutionResult:
        if shares <= 0 or price <= 0:
            return ExecutionResult(0.0, 0.0, 0.0, 0.0)
        gross_value = shares * price
        transaction_cost = self.cost_model.calculate(gross_value)
        return ExecutionResult(
            shares_delta=-shares,
            cash_delta=gross_value - transaction_cost,
            transaction_cost=transaction_cost,
            executed_value=gross_value,
        )
