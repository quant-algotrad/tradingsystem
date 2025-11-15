"""
Market Data Ingestion Worker
Fetches market data and publishes to Kafka

Runs as background service:
- Fetches OHLCV data from APIs
- Caches in Redis
- Publishes to Kafka (trading.market_data topic)
- Stores in TimescaleDB for historical analysis
"""

import time
import schedule
from datetime import datetime, timedelta
from typing import List

from src.data import get_data_fetcher
from src.events import get_event_producer, create_market_data_event
from src.cache import get_cache
from src.utils import get_logger

logger = get_logger(__name__)


class MarketDataWorker:
    """
    Background worker for market data ingestion

    Pattern: Worker Pattern
    - Runs continuously in background
    - Scheduled tasks for different timeframes
    - Event-driven architecture
    """

    def __init__(self, symbols: List[str]):
        """
        Initialize market data worker

        Args:
            symbols: List of symbols to track
        """
        self.symbols = symbols
        self.data_fetcher = get_data_fetcher()
        self.event_producer = get_event_producer()
        self.cache = get_cache()

        logger.info(f"Market Data Worker initialized for {len(symbols)} symbols")

    def fetch_and_publish_quote(self, symbol: str):
        """Fetch real-time quote and publish"""
        try:
            # Fetch quote
            quote = self.data_fetcher.fetch_quote(symbol)

            if not quote:
                logger.warning(f"No quote data for {symbol}")
                return

            # Create event
            event = create_market_data_event(
                symbol=symbol,
                data_type='quote',
                source_service='market_data_worker',
                bid=quote.bid,
                ask=quote.ask,
                last_price=quote.last_price,
                bid_size=quote.bid_size,
                ask_size=quote.ask_size
            )

            # Publish to Kafka
            self.event_producer.send_market_data_event(
                event.to_dict(),
                symbol=symbol
            )

            # Cache quote
            if self.cache.is_enabled():
                self.cache.set_quote(symbol, event.to_dict())

            logger.debug(f"Quote published for {symbol}: ₹{quote.last_price:.2f}")

        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")

    def fetch_and_publish_bar(self, symbol: str, timeframe: str):
        """Fetch OHLCV bar and publish"""
        try:
            # Fetch historical data (last bar)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=2)  # Get latest bar

            response = self.data_fetcher.fetch_historical(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )

            if not response.is_success():
                logger.warning(f"Failed to fetch {timeframe} bar for {symbol}")
                return

            df = response.get_dataframe()
            if df is None or len(df) == 0:
                return

            # Get latest bar
            latest_bar = df.iloc[-1]

            # Create event
            event = create_market_data_event(
                symbol=symbol,
                data_type='bar',
                source_service='market_data_worker',
                timeframe=timeframe,
                open=float(latest_bar['open']),
                high=float(latest_bar['high']),
                low=float(latest_bar['low']),
                close=float(latest_bar['close']),
                volume=int(latest_bar['volume'])
            )

            # Publish to Kafka
            self.event_producer.send_market_data_event(
                event.to_dict(),
                symbol=symbol
            )

            logger.debug(
                f"{timeframe} bar published for {symbol}: "
                f"O={latest_bar['open']:.2f} H={latest_bar['high']:.2f} "
                f"L={latest_bar['low']:.2f} C={latest_bar['close']:.2f}"
            )

        except Exception as e:
            logger.error(f"Error fetching {timeframe} bar for {symbol}: {e}")

    def run_quote_collection(self):
        """Collect real-time quotes for all symbols"""
        logger.info(f"Collecting quotes for {len(self.symbols)} symbols...")

        for symbol in self.symbols:
            self.fetch_and_publish_quote(symbol)
            time.sleep(0.1)  # Rate limiting

    def run_bar_collection(self, timeframe: str):
        """Collect OHLCV bars for all symbols"""
        logger.info(f"Collecting {timeframe} bars for {len(self.symbols)} symbols...")

        for symbol in self.symbols:
            self.fetch_and_publish_bar(symbol, timeframe)
            time.sleep(0.2)  # Rate limiting

    def schedule_tasks(self):
        """Schedule periodic tasks"""
        # Real-time quotes (every 30 seconds during market hours)
        schedule.every(30).seconds.do(self.run_quote_collection)

        # 1-minute bars
        schedule.every(1).minutes.do(lambda: self.run_bar_collection('1m'))

        # 5-minute bars
        schedule.every(5).minutes.do(lambda: self.run_bar_collection('5m'))

        # 15-minute bars
        schedule.every(15).minutes.do(lambda: self.run_bar_collection('15m'))

        # 1-hour bars
        schedule.every(1).hours.do(lambda: self.run_bar_collection('1h'))

        # Daily bars (run at market close - 3:30 PM IST)
        schedule.every().day.at("15:30").do(lambda: self.run_bar_collection('1d'))

        logger.info("Market data collection scheduled")

    def run(self):
        """Run worker continuously"""
        logger.info("Starting Market Data Worker...")

        # Initial data collection
        self.run_bar_collection('1d')

        # Schedule tasks
        self.schedule_tasks()

        # Run scheduler
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Market Data Worker stopped by user")
                break
            except Exception as e:
                logger.error(f"Worker error: {e}", exc_info=True)
                time.sleep(5)  # Wait before retry


# ========================================
# Main Entry Point
# ========================================

if __name__ == '__main__':
    # Example symbols (Nifty 50 stocks)
    NIFTY_50_SYMBOLS = [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "HINDUNILVR.NS",
        "ICICIBANK.NS", "KOTAKBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS",
        # Add more symbols as needed
    ]

    # Create and run worker
    worker = MarketDataWorker(NIFTY_50_SYMBOLS)
    worker.run()
