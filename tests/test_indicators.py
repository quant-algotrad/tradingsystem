"""
Technical Indicators Test Suite
Tests indicator calculations and signal generation
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.indicators import (
    SMA, EMA, RSI, MACD, BollingerBands, ATR,
    IndicatorFactory,
    calculate_indicator,
    calculate_indicators,
    MovingAverageParams,
    RSIParams,
    MACDParams
)


def create_sample_data(days: int = 100) -> pd.DataFrame:
    """Create sample OHLCV data for testing"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')

    # Generate synthetic price data
    base_price = 500
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.02, days)
    prices = base_price * np.exp(np.cumsum(returns))

    # Create OHLCV data
    data = pd.DataFrame({
        'open': prices * (1 + np.random.uniform(-0.01, 0.01, days)),
        'high': prices * (1 + np.random.uniform(0, 0.02, days)),
        'low': prices * (1 - np.random.uniform(0, 0.02, days)),
        'close': prices,
        'volume': np.random.randint(100000, 1000000, days)
    }, index=dates)

    # Ensure high/low are valid
    data['high'] = data[['open', 'high', 'close']].max(axis=1)
    data['low'] = data[['open', 'low', 'close']].min(axis=1)

    return data


def test_sma_calculation():
    """Test SMA indicator"""
    print("\n" + "="*60)
    print("TEST 1: SMA (Simple Moving Average)")
    print("="*60)

    data = create_sample_data(50)

    # Create SMA with 20-period
    sma = SMA(MovingAverageParams(period=20))

    print(f"✓ SMA created: {sma.get_name()}")
    print(f"  Category: {sma.get_category().value}")
    print(f"  Required periods: {sma.get_required_periods()}")

    # Calculate
    result = sma.calculate(data)

    print(f"✓ SMA calculated")
    print(f"  Values calculated: {len(result)}")
    print(f"  Latest SMA: {result.get_latest_value():.2f}")
    print(f"  Date range: {result.start_date.date()} to {result.end_date.date()}")

    # Convert to series
    series = result.to_series()
    print(f"✓ Converted to pandas Series: {len(series)} values")

    assert len(result) > 0, "Should have calculated values"
    assert result.get_latest_value() is not None, "Should have latest value"


def test_ema_calculation():
    """Test EMA indicator"""
    print("\n" + "="*60)
    print("TEST 2: EMA (Exponential Moving Average)")
    print("="*60)

    data = create_sample_data(50)

    ema = EMA(MovingAverageParams(period=20, ma_type="EMA"))
    result = ema.calculate(data)

    print(f"✓ EMA calculated: {ema.get_name()}")
    print(f"  Latest EMA: {result.get_latest_value():.2f}")
    print(f"  Values: {len(result)}")

    # EMA should be more responsive than SMA
    assert result.get_latest_value() > 0


def test_rsi_calculation():
    """Test RSI indicator"""
    print("\n" + "="*60)
    print("TEST 3: RSI (Relative Strength Index)")
    print("="*60)

    data = create_sample_data(50)

    rsi = RSI(RSIParams(period=14, overbought=70, oversold=30))
    result = rsi.calculate(data)

    print(f"✓ RSI calculated: {rsi.get_name()}")
    print(f"  Latest RSI: {result.get_latest_value():.2f}")
    print(f"  Values: {len(result)}")

    # Interpret signal
    signal = rsi.interpret_signal(result)
    print(f"✓ Signal interpretation:")
    print(f"  Signal: {signal.signal.value}")
    print(f"  Strength: {signal.strength:.1f}")
    print(f"  Reasoning: {signal.reasoning}")

    # RSI should be between 0-100
    assert 0 <= result.get_latest_value() <= 100, "RSI should be 0-100"


def test_macd_calculation():
    """Test MACD indicator"""
    print("\n" + "="*60)
    print("TEST 4: MACD (Moving Average Convergence Divergence)")
    print("="*60)

    data = create_sample_data(100)

    macd = MACD(MACDParams(fast_period=12, slow_period=26, signal_period=9))
    result = macd.calculate(data)

    print(f"✓ MACD calculated: {macd.get_name()}")
    print(f"  MACD Line: {result.get_latest_value():.2f}")

    # Check additional lines
    assert 'signal' in result.additional_lines, "Should have signal line"
    assert 'histogram' in result.additional_lines, "Should have histogram"

    signal_line = result.additional_lines['signal'][-1]
    histogram = result.additional_lines['histogram'][-1]

    print(f"  Signal Line: {signal_line:.2f}")
    print(f"  Histogram: {histogram:.2f}")

    # Interpret signal
    signal = macd.interpret_signal(result)
    print(f"✓ Signal: {signal.signal.value}, Strength: {signal.strength:.1f}")


def test_bollinger_bands():
    """Test Bollinger Bands indicator"""
    print("\n" + "="*60)
    print("TEST 5: Bollinger Bands")
    print("="*60)

    data = create_sample_data(50)

    from src.indicators import BollingerBandsParams
    bb = BollingerBands(BollingerBandsParams(period=20, std_dev=2.0))
    result = bb.calculate(data)

    print(f"✓ Bollinger Bands calculated")
    print(f"  Middle Band: {result.get_latest_value():.2f}")

    # Check bands
    assert 'upper' in result.additional_lines
    assert 'lower' in result.additional_lines

    upper = result.additional_lines['upper'][-1]
    lower = result.additional_lines['lower'][-1]
    middle = result.get_latest_value()

    print(f"  Upper Band: {upper:.2f}")
    print(f"  Lower Band: {lower:.2f}")
    print(f"  Band Width: {(upper - lower):.2f}")

    # Verify bands are in correct order
    assert lower < middle < upper, "Bands should be ordered: lower < middle < upper"


def test_atr_calculation():
    """Test ATR indicator"""
    print("\n" + "="*60)
    print("TEST 6: ATR (Average True Range)")
    print("="*60)

    data = create_sample_data(50)

    from src.indicators import ATRParams
    atr = ATR(ATRParams(period=14))
    result = atr.calculate(data)

    print(f"✓ ATR calculated: {atr.get_name()}")
    print(f"  Latest ATR: {result.get_latest_value():.2f}")

    # ATR should be positive
    assert result.get_latest_value() > 0, "ATR should be positive"


def test_indicator_factory():
    """Test indicator factory"""
    print("\n" + "="*60)
    print("TEST 7: Indicator Factory")
    print("="*60)

    # Get available indicators
    available = IndicatorFactory.get_available_indicators()
    print(f"Available indicators: {available}")

    # Create indicators using factory
    indicators_to_test = ['sma', 'ema', 'rsi', 'macd', 'bb', 'atr']

    for ind_name in indicators_to_test:
        indicator = IndicatorFactory.create(ind_name)
        assert indicator is not None, f"Should create {ind_name}"
        print(f"✓ Created: {indicator.get_name()}")


def test_convenience_functions():
    """Test convenience functions"""
    print("\n" + "="*60)
    print("TEST 8: Convenience Functions")
    print("="*60)

    data = create_sample_data(50)

    # Single indicator
    result = calculate_indicator('rsi', data)
    print(f"✓ calculate_indicator('rsi') -> RSI: {result.get_latest_value():.2f}")

    # Multiple indicators
    multi_result = calculate_indicators(['rsi', 'macd', 'bb'], data, symbol="TEST")
    print(f"✓ calculate_indicators() -> {len(multi_result.indicators)} indicators")

    # Get latest values
    latest = multi_result.get_latest_values()
    print(f"  Latest values: {list(latest.keys())}")

    # Convert to DataFrame
    df = multi_result.to_dataframe()
    print(f"✓ Converted to DataFrame: {df.shape}")
    print(f"  Columns: {list(df.columns)}")


def test_multi_indicator_calculation():
    """Test batch calculation of multiple indicators"""
    print("\n" + "="*60)
    print("TEST 9: Multi-Indicator Batch Calculation")
    print("="*60)

    data = create_sample_data(100)

    # Calculate all common indicators at once
    indicators = ['sma', 'ema', 'rsi', 'macd', 'bb', 'atr']
    result = calculate_indicators(indicators, data, symbol="RELIANCE.NS")

    print(f"✓ Calculated {len(result.indicators)} indicators")
    print(f"  Symbol: {result.symbol}")
    print(f"  Calculation time: {result.calculation_time_ms:.2f}ms")

    # Check each indicator
    for ind_name, ind_result in result.indicators.items():
        latest = ind_result.get_latest_value()
        print(f"  {ind_name}: {latest:.2f}" if latest else f"  {ind_name}: N/A")

    # Create combined DataFrame
    df = result.to_dataframe()
    print(f"✓ Combined DataFrame: {df.shape}")


def run_all_tests():
    """Run all indicator tests"""
    print("\n" + "╔" + "="*58 + "╗")
    print("║" + " "*12 + "TECHNICAL INDICATORS TESTS" + " "*19 + "║")
    print("╚" + "="*58 + "╝")

    try:
        test_sma_calculation()
        test_ema_calculation()
        test_rsi_calculation()
        test_macd_calculation()
        test_bollinger_bands()
        test_atr_calculation()
        test_indicator_factory()
        test_convenience_functions()
        test_multi_indicator_calculation()

        print("\n" + "╔" + "="*58 + "╗")
        print("║" + " "*10 + "✓ ALL TESTS PASSED SUCCESSFULLY" + " "*16 + "║")
        print("╚" + "="*58 + "╝\n")

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
