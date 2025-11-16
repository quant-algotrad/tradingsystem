"""
Trading Pipeline Integration
Complete end-to-end trading flow with caching

Pattern: Facade Pattern + Pipeline Pattern
- Orchestrates entire trading workflow
- Integrates all components seamlessly
- Provides caching at each layer

Flow:
1. Fetch Market Data (with cache)
2. Calculate Indicators (with cache)
3. Aggregate Signals
4. Make Trade Decision
5. Log Results
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import pandas as pd

from src.data import DataFetcher, get_data_fetcher
from src.indicators import calculate_indicators, MultiIndicatorResult
from src.strategy import (
    get_aggregated_signal,
    evaluate_trade_opportunity,
    TradeDecision,
    AggregatedSignal
)
from src.cache import get_cache
from src.utils import get_logger, log_performance

logger = get_logger(__name__)


class TradingPipeline:
    """
    Complete trading pipeline with caching

    Pattern: Facade Pattern
    - Simplifies complex multi-step workflow
    - Handles caching transparently
    - Provides clean API for trading logic

    Usage:
        pipeline = TradingPipeline()
        decision = pipeline.evaluate_symbol("RELIANCE.NS")
    """

    def __init__(self, enable_cache: bool = True):
        """
        Initialize trading pipeline

        Args:
            enable_cache: Enable Redis caching
        """
        self.data_fetcher = get_data_fetcher()
        self.cache = get_cache() if enable_cache else None
        self.enable_cache = enable_cache and (self.cache.is_enabled() if self.cache else False)

        logger.info(f"Trading Pipeline initialized (cache: {self.enable_cache})")

    @log_performance
    def fetch_market_data(
        self,
        symbol: str,
        timeframe: str = "1d",
        days_back: int = 100
    ) -> Optional[pd.DataFrame]:
        """
        Fetch market data with caching

        Args:
            symbol: Stock symbol
            timeframe: Timeframe (1d, 1h, 15m, etc.)
            days_back: Number of days of historical data

        Returns:
            OHLCV DataFrame or None
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Try cache first
        if self.enable_cache:
            cached_data = self.cache.get_ohlcv(symbol, timeframe, start_date, end_date)
            if cached_data is not None:
                logger.debug(f"Cache hit for {symbol} {timeframe}")
                return cached_data

        # Fetch from source
        logger.debug(f"Fetching {symbol} {timeframe} from source")
        response = self.data_fetcher.fetch_historical(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date
        )

        if not response.is_success():
            logger.error(f"Failed to fetch data for {symbol}: {response.error_message}")
            return None

        data = response.get_dataframe()

        # Cache the result
        if self.enable_cache and data is not None:
            self.cache.set_ohlcv(symbol, timeframe, start_date, end_date, data)

        return data

    @log_performance
    def calculate_indicators_cached(
        self,
        symbol: str,
        data: pd.DataFrame,
        indicators: List[str] = None
    ) -> Optional[MultiIndicatorResult]:
        """
        Calculate indicators with caching

        Args:
            symbol: Stock symbol
            data: OHLCV DataFrame
            indicators: List of indicators to calculate

        Returns:
            MultiIndicatorResult or None
        """
        if indicators is None:
            indicators = ['sma', 'ema', 'rsi', 'macd', 'bb', 'adx', 'atr']

        # Calculate all indicators
        result = calculate_indicators(indicators, data, symbol)

        return result

    @log_performance
    def get_aggregated_signal_for_symbol(
        self,
        symbol: str,
        data: pd.DataFrame,
        indicators: List[str] = None
    ) -> Optional[AggregatedSignal]:
        """
        Get aggregated signal from multiple indicators

        Args:
            symbol: Stock symbol
            data: OHLCV DataFrame
            indicators: Indicators to use

        Returns:
            AggregatedSignal or None
        """
        if indicators is None:
            indicators = ['rsi', 'macd', 'bb', 'adx', 'stochastic']

        try:
            signal = get_aggregated_signal(symbol, data, indicators)
            return signal
        except Exception as e:
            logger.error(f"Failed to aggregate signals for {symbol}: {e}")
            return None

    @log_performance
    def evaluate_symbol(
        self,
        symbol: str,
        timeframe: str = "1d",
        days_back: int = 100,
        position_type: str = "SWING"
    ) -> Optional[TradeDecision]:
        """
        Complete evaluation of trading opportunity for a symbol

        This is the main pipeline method that:
        1. Fetches market data (cached)
        2. Calculates indicators (cached)
        3. Aggregates signals
        4. Makes trade decision

        Args:
            symbol: Stock symbol
            timeframe: Timeframe
            days_back: Historical data period
            position_type: SWING or INTRADAY

        Returns:
            TradeDecision or None
        """
        logger.info(f"Evaluating {symbol} ({timeframe}, {position_type})")

        # Step 1: Fetch market data
        data = self.fetch_market_data(symbol, timeframe, days_back)
        if data is None or len(data) < 50:
            logger.error(f"Insufficient data for {symbol}")
            return None

        # Get current price
        current_price = data['close'].iloc[-1]

        # Step 2: Calculate indicators
        indicator_results = self.calculate_indicators_cached(symbol, data)
        if indicator_results is None:
            logger.error(f"Failed to calculate indicators for {symbol}")
            return None

        # Step 3: Aggregate signals
        aggregated_signal = self.get_aggregated_signal_for_symbol(symbol, data)
        if aggregated_signal is None:
            logger.error(f"Failed to aggregate signals for {symbol}")
            return None

        logger.info(
            f"{symbol} Signal: {aggregated_signal.signal.value} "
            f"(Confidence: {aggregated_signal.confidence:.0f}%, "
            f"Bullish: {aggregated_signal.bullish_signals}, "
            f"Bearish: {aggregated_signal.bearish_signals})"
        )

        # Step 4: Make trade decision
        decision = evaluate_trade_opportunity(
            symbol=symbol,
            aggregated_signal=aggregated_signal,
            current_price=current_price,
            timeframe=timeframe,
            position_type=position_type
        )

        # Log decision
        if decision.should_trade and decision.recommendation:
            logger.info(f"✓ TRADE OPPORTUNITY: {decision.recommendation.get_summary()}")
        else:
            reason = decision.rejection_reason.value if decision.rejection_reason else "Unknown"
            logger.info(f"✗ NO TRADE: {reason}")

        return decision

    @log_performance
    def evaluate_multiple_symbols(
        self,
        symbols: List[str],
        timeframe: str = "1d",
        position_type: str = "SWING"
    ) -> Dict[str, TradeDecision]:
        """
        Evaluate multiple symbols and return trade decisions

        Args:
            symbols: List of stock symbols
            timeframe: Timeframe
            position_type: SWING or INTRADAY

        Returns:
            Dictionary mapping symbol to TradeDecision
        """
        results = {}

        for symbol in symbols:
            try:
                decision = self.evaluate_symbol(
                    symbol=symbol,
                    timeframe=timeframe,
                    position_type=position_type
                )
                if decision:
                    results[symbol] = decision
            except Exception as e:
                logger.error(f"Error evaluating {symbol}: {e}")
                continue

        return results

    def get_top_opportunities(
        self,
        symbols: List[str],
        timeframe: str = "1d",
        position_type: str = "SWING",
        min_score: float = 60.0,
        limit: int = 5
    ) -> List[TradeDecision]:
        """
        Get top trading opportunities from symbol list

        Args:
            symbols: List of symbols to scan
            timeframe: Timeframe
            position_type: SWING or INTRADAY
            min_score: Minimum opportunity score
            limit: Maximum number of opportunities to return

        Returns:
            List of TradeDecisions sorted by score
        """
        # Evaluate all symbols
        decisions = self.evaluate_multiple_symbols(symbols, timeframe, position_type)

        # Filter actionable trades with minimum score
        opportunities = [
            decision for decision in decisions.values()
            if decision.should_trade and
            decision.recommendation and
            decision.recommendation.score >= min_score
        ]

        # Sort by score (descending)
        opportunities.sort(
            key=lambda d: d.recommendation.score,
            reverse=True
        )

        return opportunities[:limit]

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if self.cache and self.enable_cache:
            return self.cache.get_stats()
        return {'enabled': False}


# ========================================
# Convenience Functions
# ========================================

_global_pipeline: Optional[TradingPipeline] = None


def get_trading_pipeline() -> TradingPipeline:
    """Get global trading pipeline instance"""
    global _global_pipeline

    if _global_pipeline is None:
        _global_pipeline = TradingPipeline()

    return _global_pipeline


def evaluate_symbol_quick(
    symbol: str,
    timeframe: str = "1d",
    position_type: str = "SWING"
) -> Optional[TradeDecision]:
    """
    Quick evaluation of a symbol

    Args:
        symbol: Stock symbol
        timeframe: Timeframe
        position_type: SWING or INTRADAY

    Returns:
        TradeDecision or None
    """
    pipeline = get_trading_pipeline()
    return pipeline.evaluate_symbol(symbol, timeframe, position_type=position_type)


def scan_for_opportunities(
    symbols: List[str],
    timeframe: str = "1d",
    min_score: float = 60.0,
    limit: int = 5
) -> List[TradeDecision]:
    """
    Scan multiple symbols for trading opportunities

    Args:
        symbols: List of symbols to scan
        timeframe: Timeframe
        min_score: Minimum opportunity score
        limit: Maximum opportunities to return

    Returns:
        List of top TradeDecisions
    """
    pipeline = get_trading_pipeline()
    return pipeline.get_top_opportunities(
        symbols=symbols,
        timeframe=timeframe,
        min_score=min_score,
        limit=limit
    )
