export type StrategyName =
  | "buy_and_hold"
  | "moving_average_crossover"
  | "rsi_mean_reversion"
  | "momentum"
  | "bollinger_bands";

export interface AssetPreset {
  ticker: string;
  name: string;
  category: string;
}

export interface StrategyConfig {
  name: StrategyName;
  parameters: Record<string, number | string>;
}

export type RebalancingFrequency = "none" | "monthly" | "quarterly" | "annual";

export interface PortfolioAllocationConfig {
  ticker: string;
  weight: number;
}

export type RobustnessMetric = "sharpe_ratio" | "total_return";

export interface RobustnessConfig {
  enabled: boolean;
  metric: RobustnessMetric;
}

export interface BacktestRequest {
  ticker: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  position_size: number;
  strategy: StrategyConfig;
  benchmark_ticker?: string | null;
  transaction_costs: TransactionCostConfig;
  risk_controls: RiskControlConfig;
  rolling_window: number;
  portfolio_allocations?: PortfolioAllocationConfig[];
  rebalancing_frequency?: RebalancingFrequency;
  robustness?: RobustnessConfig;
}

export interface TransactionCostConfig {
  fixed_fee: number;
  percentage_fee: number;
  slippage_bps: number;
  bid_ask_spread_bps: number;
}

export interface RiskControlConfig {
  stop_loss_pct: number | null;
  take_profit_pct: number | null;
}

export interface PortfolioPoint {
  date: string;
  price: number;
  cash: number;
  shares: number;
  value: number;
}

export interface RollingMetricPoint {
  date: string;
  rolling_return: number;
  rolling_volatility: number;
  rolling_sharpe: number;
}

export interface TradeRecord {
  entry_date: string;
  entry_price: number;
  exit_date: string | null;
  exit_price: number | null;
  shares: number;
  gross_profit: number | null;
  transaction_cost: number;
  net_profit: number | null;
  holding_period: number | null;
  exit_reason: string | null;
}

export interface MetricSummary {
  total_return: number;
  annualized_return: number;
  annualized_volatility: number;
  sharpe_ratio: number | null;
  maximum_drawdown: number;
  number_of_trades: number;
  win_rate: number | null;
  average_trade_return: number | null;
  best_trade: number | null;
  worst_trade: number | null;
  total_transaction_costs: number;
  transaction_cost_pct_of_initial: number;
  return_drag_from_costs: number | null;
  benchmark_return: number | null;
  alpha_relative_to_benchmark: number | null;
  tooltip_explanations: Record<string, string>;
}

export interface AllocationResult {
  ticker: string;
  target_weight: number;
  ending_weight: number;
  contribution_to_return: number;
  annualized_volatility: number;
  risk_contribution: number;
}

export interface CorrelationCell {
  row_ticker: string;
  column_ticker: string;
  correlation: number;
}

export interface RebalanceRecord {
  date: string;
  ticker: string;
  action: "buy" | "sell";
  shares_delta: number;
  price: number;
  transaction_cost: number;
  target_value: number;
  actual_value: number;
}

export interface RobustnessPoint {
  x_value: number;
  y_value: number;
  parameters: Record<string, number | string>;
  metric_value: number | null;
  total_return: number;
  annualized_volatility: number;
  sharpe_ratio: number | null;
  maximum_drawdown: number;
  number_of_trades: number;
}

export interface RobustnessResult {
  strategy_name: string;
  metric: RobustnessMetric;
  x_axis_label: string;
  y_axis_label: string;
  best_x_value: number | null;
  best_y_value: number | null;
  best_metric_value: number | null;
  median_metric_value: number | null;
  positive_return_share: number;
  stable_zone_share: number;
  tested_combinations: number;
  overfit_warning: string | null;
  points: RobustnessPoint[];
}

export interface BacktestResponse {
  ticker: string;
  benchmark_ticker: string;
  strategy_name: string;
  metrics: MetricSummary;
  before_cost_metrics: MetricSummary;
  benchmark_metrics: MetricSummary;
  portfolio_curve: PortfolioPoint[];
  before_cost_curve: PortfolioPoint[];
  benchmark_curve: PortfolioPoint[];
  rolling_metrics: RollingMetricPoint[];
  trades: TradeRecord[];
  warnings: string[];
  portfolio_allocations: AllocationResult[];
  correlation_matrix: CorrelationCell[];
  rebalance_events: RebalanceRecord[];
  rebalancing_frequency: RebalancingFrequency | null;
  robustness: RobustnessResult | null;
}

export interface ApiError {
  detail: string;
}
