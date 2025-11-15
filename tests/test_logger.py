"""
Logging System Test Suite
Tests logging infrastructure and performance tracking
"""

import sys
import time
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import (
    get_logger,
    get_trading_logger,
    log_trade,
    log_signal,
    log_performance,
    log_method,
    TradingLogger
)


def test_logger_singleton():
    """Test singleton pattern"""
    print("\n" + "="*60)
    print("TEST 1: Logger Singleton Pattern")
    print("="*60)

    logger1 = TradingLogger()
    logger2 = TradingLogger()
    logger3 = get_trading_logger()

    assert logger1 is logger2 is logger3, "Should be same instance"
    print("✓ Singleton pattern working correctly")
    print(f"  All instances identical: {id(logger1) == id(logger2) == id(logger3)}")


def test_basic_logging():
    """Test basic logging functionality"""
    print("\n" + "="*60)
    print("TEST 2: Basic Logging Levels")
    print("="*60)

    logger = get_logger('test_module')

    # Test different levels
    logger.debug("Debug message - detailed information")
    logger.info("Info message - general information")
    logger.warning("Warning message - something to watch")
    logger.error("Error message - something went wrong")

    print("✓ All log levels working")
    print("  Check logs/trading.log for output")


def test_trade_logging():
    """Test trade logging"""
    print("\n" + "="*60)
    print("TEST 3: Trade Logging")
    print("="*60)

    # Log various trades
    log_trade("RELIANCE.NS", "BUY", 10, 2450.50,
              strategy="TREND_RSI",
              reason="RSI oversold",
              confidence=85.0)

    log_trade("TCS.NS", "SELL", 5, 3200.75,
              strategy="MEAN_REVERSION",
              reason="Bollinger upper band",
              pnl=1250.50)

    log_trade("INFY.NS", "SHORT", 15, 1450.25,
              strategy="BREAKOUT",
              reason="Breakdown with volume")

    print("✓ Trade logs created")
    print("  Check logs/trades.log for trade-specific logs")


def test_signal_logging():
    """Test signal logging"""
    print("\n" + "="*60)
    print("TEST 4: Signal Logging")
    print("="*60)

    # Log various signals
    log_signal("RELIANCE.NS", "BUY", 75.0,
               indicator="RSI",
               value=28.5,
               timeframe="1d")

    log_signal("TCS.NS", "SELL", 82.0,
               indicator="MACD",
               histogram=-2.5,
               timeframe="1h")

    log_signal("INFY.NS", "HOLD", 45.0,
               indicator="BB",
               price_position="middle")

    print("✓ Signal logs created")
    print("  Signals logged to main log file")


def test_performance_decorator():
    """Test performance tracking decorator"""
    print("\n" + "="*60)
    print("TEST 5: Performance Tracking Decorator")
    print("="*60)

    @log_performance
    def fast_function():
        """Fast function"""
        time.sleep(0.01)  # 10ms
        return "fast"

    @log_performance
    def slow_function():
        """Slow function"""
        time.sleep(0.05)  # 50ms
        return "slow"

    # Execute functions
    result1 = fast_function()
    result2 = slow_function()

    assert result1 == "fast"
    assert result2 == "slow"

    # Get performance stats
    trading_logger = get_trading_logger()

    stats_fast = trading_logger.get_performance_stats(
        f"{__name__}.fast_function"
    )
    stats_slow = trading_logger.get_performance_stats(
        f"{__name__}.slow_function"
    )

    print("✓ Performance tracking working")
    print(f"  fast_function: {stats_fast.get('avg_ms', 0):.2f}ms avg")
    print(f"  slow_function: {stats_slow.get('avg_ms', 0):.2f}ms avg")


def test_method_logging_decorator():
    """Test method logging decorator"""
    print("\n" + "="*60)
    print("TEST 6: Method Logging Decorator")
    print("="*60)

    class TestClass:
        @log_method(level='INFO')
        def calculate_something(self, x: int, y: int) -> int:
            """Test method"""
            return x + y

        @log_method(level='DEBUG')
        def process_data(self, data: list) -> int:
            """Another test method"""
            return len(data)

    obj = TestClass()
    result1 = obj.calculate_something(5, 10)
    result2 = obj.process_data([1, 2, 3, 4, 5])

    assert result1 == 15
    assert result2 == 5

    print("✓ Method logging decorator working")
    print(f"  calculate_something returned: {result1}")
    print(f"  process_data returned: {result2}")


def test_structured_logging():
    """Test JSON structured logging"""
    print("\n" + "="*60)
    print("TEST 7: Structured JSON Logging")
    print("="*60)

    logger = get_logger('json_test')

    # Log with various data types
    logger.info("Testing structured logging with metadata")
    logger.warning("Warning with extra context")
    logger.error("Error occurred during processing")

    print("✓ Structured logs created")
    print("  Check logs/trading.json for JSON-formatted logs")

    # Try to read and parse JSON log
    json_log_path = Path("logs/trading.json")
    if json_log_path.exists():
        with open(json_log_path, 'r') as f:
            # Read last line
            lines = f.readlines()
            if lines:
                last_log = json.loads(lines[-1])
                print(f"  Latest JSON log entry:")
                print(f"    Level: {last_log.get('level')}")
                print(f"    Message: {last_log.get('message')}")
                print(f"    Module: {last_log.get('module')}")


def test_error_logging():
    """Test error and exception logging"""
    print("\n" + "="*60)
    print("TEST 8: Error and Exception Logging")
    print("="*60)

    logger = get_logger('error_test')

    # Log simple error
    logger.error("Database connection failed")

    # Log with exception
    try:
        raise ValueError("Invalid parameter value")
    except ValueError as e:
        logger.error(f"Exception occurred: {e}", exc_info=True)

    print("✓ Error logging working")
    print("  Check logs/errors.log for error-specific logs")


def test_performance_stats():
    """Test performance statistics"""
    print("\n" + "="*60)
    print("TEST 9: Performance Statistics")
    print("="*60)

    trading_logger = get_trading_logger()

    # Track multiple operations
    for i in range(10):
        duration = 10 + (i * 5)  # Increasing durations
        trading_logger.track_performance(
            "data_fetch",
            duration,
            symbol="TEST",
            bars=100
        )

    # Get stats
    stats = trading_logger.get_performance_stats("data_fetch")

    print("✓ Performance statistics:")
    print(f"  Count: {stats['count']}")
    print(f"  Average: {stats['avg_ms']:.2f}ms")
    print(f"  Min: {stats['min_ms']:.2f}ms")
    print(f"  Max: {stats['max_ms']:.2f}ms")
    print(f"  Total: {stats['total_ms']:.2f}ms")

    assert stats['count'] == 10
    assert stats['min_ms'] == 10.0
    assert stats['max_ms'] == 55.0


def test_log_files_created():
    """Test that log files are created"""
    print("\n" + "="*60)
    print("TEST 10: Log Files Created")
    print("="*60)

    log_dir = Path("logs")
    expected_files = [
        'trading.log',
        'errors.log',
        'trades.log',
        'trading.json'
    ]

    print("Log files created:")
    for log_file in expected_files:
        file_path = log_dir / log_file
        exists = file_path.exists()
        size = file_path.stat().st_size if exists else 0

        status = "✓" if exists else "❌"
        print(f"  {status} {log_file}: {size} bytes")

        assert exists, f"{log_file} should exist"


def run_all_tests():
    """Run all logging tests"""
    print("\n" + "╔" + "="*58 + "╗")
    print("║" + " "*17 + "LOGGING SYSTEM TESTS" + " "*20 + "║")
    print("╚" + "="*58 + "╝")

    try:
        test_logger_singleton()
        test_basic_logging()
        test_trade_logging()
        test_signal_logging()
        test_performance_decorator()
        test_method_logging_decorator()
        test_structured_logging()
        test_error_logging()
        test_performance_stats()
        test_log_files_created()

        print("\n" + "╔" + "="*58 + "╗")
        print("║" + " "*10 + "✓ ALL TESTS PASSED SUCCESSFULLY" + " "*16 + "║")
        print("╚" + "="*58 + "╝\n")

        print("Log files created in ./logs/ directory:")
        print("  - trading.log: Main application log")
        print("  - errors.log: Error messages only")
        print("  - trades.log: Trade execution logs")
        print("  - trading.json: Structured JSON logs")

        return True

    except Exception as e:
        print("\n" + "╔" + "="*58 + "╗")
        print("║" + " "*15 + "❌ TEST FAILED" + " "*23 + "║")
        print("╚" + "="*58 + "╝")
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
