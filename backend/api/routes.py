from datetime import date

from fastapi import APIRouter, HTTPException

from analytics.metrics import calculate_metrics
from analytics.robustness import calculate_robustness
from analytics.rolling_metrics import calculate_rolling_metrics
from backtesting.execution import LongOnlyExecutionModel
from backtesting.engine import BacktestEngine, BacktestInputError
from backtesting.portfolio_engine import PortfolioRebalanceEngine
from backtesting.transaction_costs import TransactionCostModel
from data.yahoo_provider import YahooFinanceProvider
from models.schemas import (
    AssetPreset,
    BacktestRequest,
    BacktestResponse,
    HealthResponse,
    StrategyConfig,
)
from strategies.bollinger import BollingerBandStrategy
from strategies.buy_and_hold import BuyAndHoldStrategy
from strategies.momentum import MomentumStrategy
from strategies.moving_average import MovingAverageCrossoverStrategy
from strategies.rsi import RSIMeanReversionStrategy

router = APIRouter()


ASSET_PRESETS = [
    AssetPreset(ticker=ticker, name=name, category=category)
    for ticker, name, category in [
        ("XIU.TO", "iShares S&P/TSX 60 Index ETF", "Canada Equity"),
        ("XIC.TO", "iShares Core S&P/TSX Capped Composite ETF", "Canada Equity"),
        ("VCN.TO", "Vanguard FTSE Canada All Cap Index ETF", "Canada Equity"),
        ("ZCN.TO", "BMO S&P/TSX Capped Composite ETF", "Canada Equity"),
        ("VFV.TO", "Vanguard S&P 500 Index ETF", "US Equity"),
        ("ZSP.TO", "BMO S&P 500 Index ETF", "US Equity"),
        ("XUS.TO", "iShares Core S&P 500 Index ETF", "US Equity"),
        ("VUN.TO", "Vanguard US Total Market Index ETF", "US Equity"),
        ("XSP.TO", "iShares Core S&P 500 CAD-Hedged ETF", "US Equity"),
        ("QQC.TO", "Invesco NASDAQ 100 Index ETF", "Growth"),
        ("XQQ.TO", "iShares NASDAQ 100 CAD-Hedged ETF", "Growth"),
        ("HXQ.TO", "Global X NASDAQ 100 Index ETF", "Growth"),
        ("XEF.TO", "iShares Core MSCI EAFE IMI Index ETF", "International Equity"),
        ("VIU.TO", "Vanguard FTSE Developed All Cap ex North America ETF", "International Equity"),
        ("ZEA.TO", "BMO MSCI EAFE Index ETF", "International Equity"),
        ("VEE.TO", "Vanguard FTSE Emerging Markets All Cap Index ETF", "International Equity"),
        ("XEC.TO", "iShares Core MSCI Emerging Markets IMI Index ETF", "International Equity"),
        ("XBB.TO", "iShares Core Canadian Universe Bond Index ETF", "Fixed Income"),
        ("VAB.TO", "Vanguard Canadian Aggregate Bond Index ETF", "Fixed Income"),
        ("ZAG.TO", "BMO Aggregate Bond Index ETF", "Fixed Income"),
        ("XSB.TO", "iShares Core Canadian Short Term Bond Index ETF", "Fixed Income"),
        ("VDY.TO", "Vanguard FTSE Canadian High Dividend Yield Index ETF", "Dividend"),
        ("XEI.TO", "iShares S&P/TSX Composite High Dividend Index ETF", "Dividend"),
        ("ZDV.TO", "BMO Canadian Dividend ETF", "Dividend"),
        ("CDZ.TO", "iShares S&P/TSX Canadian Dividend Aristocrats Index ETF", "Dividend"),
        ("XRE.TO", "iShares S&P/TSX Capped REIT Index ETF", "Real Assets"),
        ("ZRE.TO", "BMO Equal Weight REITs Index ETF", "Real Assets"),
        ("XGD.TO", "iShares S&P/TSX Global Gold Index ETF", "Real Assets"),
        ("RY.TO", "Royal Bank of Canada", "Canadian Stocks"),
        ("TD.TO", "Toronto-Dominion Bank", "Canadian Stocks"),
        ("BNS.TO", "Bank of Nova Scotia", "Canadian Stocks"),
        ("ENB.TO", "Enbridge Inc.", "Canadian Stocks"),
        ("CNQ.TO", "Canadian Natural Resources", "Canadian Stocks"),
        ("SHOP.TO", "Shopify Inc.", "Canadian Stocks"),
    ]
]


def _build_strategy(request: BacktestRequest):
    params = request.strategy.parameters
    if request.strategy.name == "buy_and_hold":
        return BuyAndHoldStrategy()
    if request.strategy.name == "moving_average_crossover":
        short_window = int(params.get("short_window", 50))
        long_window = int(params.get("long_window", 200))
        return MovingAverageCrossoverStrategy(
            short_window=short_window,
            long_window=long_window,
        )
    if request.strategy.name == "rsi_mean_reversion":
        return RSIMeanReversionStrategy(
            rsi_period=int(params.get("rsi_period", 14)),
            oversold_threshold=float(params.get("oversold_threshold", 30)),
            overbought_threshold=float(params.get("overbought_threshold", 70)),
        )
    if request.strategy.name == "momentum":
        return MomentumStrategy(
            lookback_period=int(params.get("lookback_period", 63)),
            momentum_threshold=float(params.get("momentum_threshold", 0.02)),
            holding_period=int(params.get("holding_period", 20)),
        )
    if request.strategy.name == "bollinger_bands":
        return BollingerBandStrategy(
            window=int(params.get("window", 20)),
            standard_deviation_multiplier=float(
                params.get("standard_deviation_multiplier", 2.0)
            ),
            mode=str(params.get("mode", "mean_reversion")),
        )
    raise HTTPException(status_code=400, detail=f"Unsupported strategy: {request.strategy.name}")


def _build_cost_model(request: BacktestRequest) -> TransactionCostModel:
    return TransactionCostModel(
        fixed_fee=request.transaction_costs.fixed_fee,
        percentage_fee=request.transaction_costs.percentage_fee,
        slippage_bps=request.transaction_costs.slippage_bps,
        bid_ask_spread_bps=request.transaction_costs.bid_ask_spread_bps,
    )


def _build_engine(
    request: BacktestRequest,
    cost_model: TransactionCostModel | None = None,
    include_risk_controls: bool = True,
    position_size: float | None = None,
) -> BacktestEngine:
    return BacktestEngine(
        initial_capital=request.initial_capital,
        position_size=request.position_size if position_size is None else position_size,
        stop_loss_pct=request.risk_controls.stop_loss_pct if include_risk_controls else None,
        take_profit_pct=request.risk_controls.take_profit_pct if include_risk_controls else None,
        execution_model=LongOnlyExecutionModel(cost_model=cost_model),
    )


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", as_of=date.today())


@router.get("/assets/presets", response_model=list[AssetPreset])
def asset_presets() -> list[AssetPreset]:
    return ASSET_PRESETS


@router.post("/backtests/run", response_model=BacktestResponse)
def run_backtest(request: BacktestRequest) -> BacktestResponse:
    provider = YahooFinanceProvider()
    try:
        if request.portfolio_allocations:
            return _run_portfolio_backtest(request=request, provider=provider)

        price_data = provider.get_history(
            ticker=request.ticker,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        strategy = _build_strategy(request)
        engine = _build_engine(request=request, cost_model=_build_cost_model(request))
        before_cost_engine = _build_engine(
            request=request,
            cost_model=TransactionCostModel(),
        )
        result = engine.run(price_data=price_data, strategy=strategy)
        before_cost_result = before_cost_engine.run(price_data=price_data, strategy=strategy)

        benchmark_ticker = request.benchmark_ticker or request.ticker
        if benchmark_ticker == request.ticker:
            benchmark_prices = price_data
        else:
            benchmark_prices = provider.get_history(
                ticker=benchmark_ticker,
                start_date=request.start_date,
                end_date=request.end_date,
            )
        benchmark_engine = _build_engine(
            request=request,
            cost_model=TransactionCostModel(),
            include_risk_controls=False,
            position_size=1.0,
        )
        benchmark_result = benchmark_engine.run(
            price_data=benchmark_prices,
            strategy=BuyAndHoldStrategy(),
        )

        before_cost_metrics = calculate_metrics(
            equity_curve=before_cost_result.portfolio_curve,
            trades=before_cost_result.trades,
            initial_capital=request.initial_capital,
        )
        strategy_metrics = calculate_metrics(
            equity_curve=result.portfolio_curve,
            trades=result.trades,
            initial_capital=request.initial_capital,
            before_cost_total_return=before_cost_metrics.total_return,
        )
        benchmark_metrics = calculate_metrics(
            equity_curve=benchmark_result.portfolio_curve,
            trades=benchmark_result.trades,
            initial_capital=request.initial_capital,
        )
        strategy_metrics.benchmark_return = round(benchmark_metrics.total_return, 8)
        strategy_metrics.alpha_relative_to_benchmark = round(
            strategy_metrics.total_return - benchmark_metrics.total_return,
            8,
        )
        before_cost_metrics.benchmark_return = round(benchmark_metrics.total_return, 8)
        before_cost_metrics.alpha_relative_to_benchmark = round(
            before_cost_metrics.total_return - benchmark_metrics.total_return,
            8,
        )

        warnings = list(
            dict.fromkeys(result.warnings + before_cost_result.warnings + benchmark_result.warnings)
        )
        rolling_metrics = calculate_rolling_metrics(
            equity_curve=result.portfolio_curve,
            window=request.rolling_window,
        )
        robustness = calculate_robustness(
            request=request,
            metric_runner=lambda parameters: _calculate_strategy_metrics_for_parameters(
                request=request,
                price_data=price_data,
                parameters=parameters,
            ),
        )

        return BacktestResponse(
            ticker=request.ticker,
            benchmark_ticker=benchmark_ticker,
            strategy_name=strategy.name,
            metrics=strategy_metrics,
            before_cost_metrics=before_cost_metrics,
            benchmark_metrics=benchmark_metrics,
            portfolio_curve=result.portfolio_curve,
            before_cost_curve=before_cost_result.portfolio_curve,
            benchmark_curve=benchmark_result.portfolio_curve,
            rolling_metrics=rolling_metrics,
            trades=result.trades,
            warnings=warnings,
            robustness=robustness,
        )
    except BacktestInputError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Unable to complete the backtest. Check the ticker, date range, "
                "and data availability."
            ),
        ) from exc


def _run_portfolio_backtest(
    request: BacktestRequest,
    provider: YahooFinanceProvider,
) -> BacktestResponse:
    tickers = [allocation.ticker for allocation in request.portfolio_allocations]
    price_data_by_ticker = {
        ticker: provider.get_history(
            ticker=ticker,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        for ticker in tickers
    }
    portfolio_engine = PortfolioRebalanceEngine(
        initial_capital=request.initial_capital,
        allocations=request.portfolio_allocations,
        rebalancing_frequency=request.rebalancing_frequency,
        cost_model=_build_cost_model(request),
    )
    before_cost_engine = PortfolioRebalanceEngine(
        initial_capital=request.initial_capital,
        allocations=request.portfolio_allocations,
        rebalancing_frequency=request.rebalancing_frequency,
        cost_model=TransactionCostModel(),
    )
    result = portfolio_engine.run(price_data_by_ticker=price_data_by_ticker)
    before_cost_result = before_cost_engine.run(price_data_by_ticker=price_data_by_ticker)

    benchmark_ticker = request.benchmark_ticker or "XIU.TO"
    benchmark_prices = provider.get_history(
        ticker=benchmark_ticker,
        start_date=request.start_date,
        end_date=request.end_date,
    )
    benchmark_engine = _build_engine(
        request=request,
        cost_model=TransactionCostModel(),
        include_risk_controls=False,
        position_size=1.0,
    )
    benchmark_result = benchmark_engine.run(
        price_data=benchmark_prices,
        strategy=BuyAndHoldStrategy(),
    )

    before_cost_metrics = calculate_metrics(
        equity_curve=before_cost_result.portfolio_curve,
        trades=before_cost_result.trades,
        initial_capital=request.initial_capital,
    )
    strategy_metrics = calculate_metrics(
        equity_curve=result.portfolio_curve,
        trades=result.trades,
        initial_capital=request.initial_capital,
        before_cost_total_return=before_cost_metrics.total_return,
    )
    benchmark_metrics = calculate_metrics(
        equity_curve=benchmark_result.portfolio_curve,
        trades=benchmark_result.trades,
        initial_capital=request.initial_capital,
    )
    strategy_metrics.benchmark_return = round(benchmark_metrics.total_return, 8)
    strategy_metrics.alpha_relative_to_benchmark = round(
        strategy_metrics.total_return - benchmark_metrics.total_return,
        8,
    )
    before_cost_metrics.benchmark_return = round(benchmark_metrics.total_return, 8)
    before_cost_metrics.alpha_relative_to_benchmark = round(
        before_cost_metrics.total_return - benchmark_metrics.total_return,
        8,
    )

    warnings = list(dict.fromkeys(result.warnings + before_cost_result.warnings))
    if request.risk_controls.stop_loss_pct is not None or request.risk_controls.take_profit_pct is not None:
        warnings.append("Stop-loss and take-profit controls are disabled in portfolio mode.")

    return BacktestResponse(
        ticker="Portfolio",
        benchmark_ticker=benchmark_ticker,
        strategy_name="portfolio_rebalance",
        metrics=strategy_metrics,
        before_cost_metrics=before_cost_metrics,
        benchmark_metrics=benchmark_metrics,
        portfolio_curve=result.portfolio_curve,
        before_cost_curve=before_cost_result.portfolio_curve,
        benchmark_curve=benchmark_result.portfolio_curve,
        rolling_metrics=calculate_rolling_metrics(
            equity_curve=result.portfolio_curve,
            window=request.rolling_window,
        ),
        trades=result.trades,
        warnings=warnings,
        portfolio_allocations=result.allocation_results,
        correlation_matrix=result.correlation_matrix,
        rebalance_events=result.rebalance_events,
        rebalancing_frequency=request.rebalancing_frequency,
    )


def _calculate_strategy_metrics_for_parameters(
    request: BacktestRequest,
    price_data,
    parameters: dict,
):
    scan_request = request.model_copy(
        update={
            "strategy": StrategyConfig(
                name=request.strategy.name,
                parameters=parameters,
            )
        },
        deep=True,
    )
    strategy = _build_strategy(scan_request)
    engine = _build_engine(request=scan_request, cost_model=_build_cost_model(scan_request))
    result = engine.run(price_data=price_data, strategy=strategy)
    return calculate_metrics(
        equity_curve=result.portfolio_curve,
        trades=result.trades,
        initial_capital=scan_request.initial_capital,
    )
