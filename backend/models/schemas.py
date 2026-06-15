from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class HealthResponse(BaseModel):
    status: str
    as_of: date


class AssetPreset(BaseModel):
    ticker: str
    name: str
    category: str


class StrategyConfig(BaseModel):
    name: Literal[
        "buy_and_hold",
        "moving_average_crossover",
        "rsi_mean_reversion",
        "momentum",
        "bollinger_bands",
    ]
    parameters: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_strategy_parameters(self) -> "StrategyConfig":
        if self.name == "moving_average_crossover":
            short_window = int(self.parameters.get("short_window", 50))
            long_window = int(self.parameters.get("long_window", 200))
            if short_window < 1 or long_window < 2:
                raise ValueError("Moving average windows must be positive.")
            if short_window >= long_window:
                raise ValueError("Short window must be smaller than long window.")
        if self.name == "rsi_mean_reversion":
            rsi_period = int(self.parameters.get("rsi_period", 14))
            oversold = float(self.parameters.get("oversold_threshold", 30))
            overbought = float(self.parameters.get("overbought_threshold", 70))
            if rsi_period < 2:
                raise ValueError("RSI period must be at least 2.")
            if not 0 < oversold < overbought < 100:
                raise ValueError("RSI thresholds must satisfy 0 < oversold < overbought < 100.")
        if self.name == "momentum":
            lookback_period = int(self.parameters.get("lookback_period", 63))
            momentum_threshold = float(self.parameters.get("momentum_threshold", 0.02))
            holding_period = int(self.parameters.get("holding_period", 20))
            if lookback_period < 1 or holding_period < 1:
                raise ValueError("Momentum lookback and holding period must be positive.")
            if momentum_threshold < 0:
                raise ValueError("Momentum threshold cannot be negative.")
        if self.name == "bollinger_bands":
            window = int(self.parameters.get("window", 20))
            multiplier = float(self.parameters.get("standard_deviation_multiplier", 2.0))
            mode = str(self.parameters.get("mode", "mean_reversion"))
            if window < 2:
                raise ValueError("Bollinger window must be at least 2.")
            if multiplier <= 0:
                raise ValueError("Standard deviation multiplier must be positive.")
            if mode not in {"mean_reversion", "breakout"}:
                raise ValueError("Bollinger mode must be mean_reversion or breakout.")
        return self


class TransactionCostConfig(BaseModel):
    fixed_fee: float = Field(ge=0, default=0.0)
    percentage_fee: float = Field(ge=0, default=0.0)
    slippage_bps: float = Field(ge=0, default=0.0)
    bid_ask_spread_bps: float = Field(ge=0, default=0.0)


class RiskControlConfig(BaseModel):
    stop_loss_pct: float | None = Field(default=None, ge=0, lt=1)
    take_profit_pct: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def normalize_disabled_controls(self) -> "RiskControlConfig":
        if self.stop_loss_pct == 0:
            self.stop_loss_pct = None
        if self.take_profit_pct == 0:
            self.take_profit_pct = None
        return self


class PortfolioAllocation(BaseModel):
    ticker: str = Field(min_length=1, max_length=24)
    weight: float = Field(gt=0, le=1)

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        ticker = value.strip().upper()
        if not ticker:
            raise ValueError("Ticker cannot be empty.")
        return ticker


class RobustnessConfig(BaseModel):
    enabled: bool = False
    metric: Literal["sharpe_ratio", "total_return"] = "sharpe_ratio"


class BacktestRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=24)
    start_date: date
    end_date: date
    initial_capital: float = Field(gt=0, default=10000)
    position_size: float = Field(gt=0, le=1, default=1.0)
    strategy: StrategyConfig
    benchmark_ticker: str | None = Field(default=None, max_length=24)
    transaction_costs: TransactionCostConfig = Field(default_factory=TransactionCostConfig)
    risk_controls: RiskControlConfig = Field(default_factory=RiskControlConfig)
    rolling_window: int = Field(default=63, ge=2, le=252)
    portfolio_allocations: list[PortfolioAllocation] = Field(default_factory=list)
    rebalancing_frequency: Literal["none", "monthly", "quarterly", "annual"] = "quarterly"
    robustness: RobustnessConfig = Field(default_factory=RobustnessConfig)

    @field_validator("ticker", "benchmark_ticker")
    @classmethod
    def normalize_ticker(cls, value: str | None) -> str | None:
        if value is None:
            return None
        ticker = value.strip().upper()
        if not ticker:
            raise ValueError("Ticker cannot be empty.")
        return ticker

    @model_validator(mode="after")
    def validate_dates(self) -> "BacktestRequest":
        if self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date.")
        if self.portfolio_allocations:
            tickers = [allocation.ticker for allocation in self.portfolio_allocations]
            if len(set(tickers)) != len(tickers):
                raise ValueError("Portfolio tickers must be unique.")
            if len(self.portfolio_allocations) < 2:
                raise ValueError("Portfolio mode requires at least two tickers.")
            total_weight = sum(allocation.weight for allocation in self.portfolio_allocations)
            if abs(total_weight - 1.0) > 0.0001:
                raise ValueError("Portfolio weights must sum to 100%.")
        return self


class PortfolioPoint(BaseModel):
    date: date
    price: float
    cash: float
    shares: float
    value: float


class RollingMetricPoint(BaseModel):
    date: date
    rolling_return: float
    rolling_volatility: float
    rolling_sharpe: float


class TradeRecord(BaseModel):
    entry_date: date
    entry_price: float
    exit_date: date | None = None
    exit_price: float | None = None
    shares: float
    gross_profit: float | None = None
    transaction_cost: float = 0.0
    net_profit: float | None = None
    holding_period: int | None = None
    exit_reason: str | None = None


class MetricSummary(BaseModel):
    total_return: float
    annualized_return: float
    annualized_volatility: float
    sharpe_ratio: float | None
    maximum_drawdown: float
    number_of_trades: int
    win_rate: float | None
    average_trade_return: float | None
    best_trade: float | None
    worst_trade: float | None
    total_transaction_costs: float = 0.0
    transaction_cost_pct_of_initial: float = 0.0
    return_drag_from_costs: float | None = None
    benchmark_return: float | None = None
    alpha_relative_to_benchmark: float | None = None
    tooltip_explanations: dict[str, str]


class AllocationResult(BaseModel):
    ticker: str
    target_weight: float
    ending_weight: float
    contribution_to_return: float
    annualized_volatility: float
    risk_contribution: float


class CorrelationCell(BaseModel):
    row_ticker: str
    column_ticker: str
    correlation: float


class RebalanceRecord(BaseModel):
    date: date
    ticker: str
    action: Literal["buy", "sell"]
    shares_delta: float
    price: float
    transaction_cost: float
    target_value: float
    actual_value: float


class RobustnessPoint(BaseModel):
    x_value: float
    y_value: float
    parameters: dict[str, Any]
    metric_value: float | None
    total_return: float
    annualized_volatility: float
    sharpe_ratio: float | None
    maximum_drawdown: float
    number_of_trades: int


class RobustnessResult(BaseModel):
    strategy_name: str
    metric: str
    x_axis_label: str
    y_axis_label: str
    best_x_value: float | None
    best_y_value: float | None
    best_metric_value: float | None
    median_metric_value: float | None
    positive_return_share: float
    stable_zone_share: float
    tested_combinations: int
    overfit_warning: str | None = None
    points: list[RobustnessPoint]


class BacktestResponse(BaseModel):
    ticker: str
    benchmark_ticker: str
    strategy_name: str
    metrics: MetricSummary
    before_cost_metrics: MetricSummary
    benchmark_metrics: MetricSummary
    portfolio_curve: list[PortfolioPoint]
    before_cost_curve: list[PortfolioPoint]
    benchmark_curve: list[PortfolioPoint]
    rolling_metrics: list[RollingMetricPoint]
    trades: list[TradeRecord]
    warnings: list[str] = Field(default_factory=list)
    portfolio_allocations: list[AllocationResult] = Field(default_factory=list)
    correlation_matrix: list[CorrelationCell] = Field(default_factory=list)
    rebalance_events: list[RebalanceRecord] = Field(default_factory=list)
    rebalancing_frequency: str | None = None
    robustness: RobustnessResult | None = None
