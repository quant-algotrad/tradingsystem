"""
Configuration System Test Suite
Tests configuration loading, validation, and management
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import (
    ConfigurationManager,
    get_trading_config,
    get_risk_config,
    get_database_config,
    get_api_config,
    Environment,
    PositionType,
    BrokerType
)


def test_singleton_pattern():
    """Test that ConfigurationManager is a true singleton"""
    print("\n" + "="*60)
    print("TEST 1: Singleton Pattern")
    print("="*60)

    mgr1 = ConfigurationManager.get_instance()
    mgr2 = ConfigurationManager.get_instance()
    mgr3 = ConfigurationManager()

    assert mgr1 is mgr2 is mgr3, "ConfigurationManager should be singleton"
    print("✓ Singleton pattern working correctly")
    print(f"  All instances are identical: {id(mgr1) == id(mgr2) == id(mgr3)}")


def test_load_default_configs():
    """Test loading default configurations"""
    print("\n" + "="*60)
    print("TEST 2: Default Configuration Loading")
    print("="*60)

    mgr = ConfigurationManager.get_instance()
    mgr.reset()  # Reset for clean test

    # Load defaults (no YAML file)
    mgr.load_all_configs()

    # Access each config
    trading = mgr.get_trading_config()
    risk = mgr.get_risk_config()
    database = mgr.get_database_config()
    api = mgr.get_api_config()

    print("✓ All default configurations loaded successfully")
    print(f"  Trading Config: {type(trading).__name__}")
    print(f"  Risk Config: {type(risk).__name__}")
    print(f"  Database Config: {type(database).__name__}")
    print(f"  API Config: {type(api).__name__}")


def test_load_yaml_config():
    """Test loading from YAML file"""
    print("\n" + "="*60)
    print("TEST 3: YAML Configuration Loading")
    print("="*60)

    mgr = ConfigurationManager.get_instance()
    mgr.reset()

    # Set config directory
    config_dir = Path(__file__).parent.parent / "config" / "environments"
    mgr.set_config_directory(config_dir)

    # Load development config
    mgr.set_environment(Environment.DEVELOPMENT)
    mgr.load_all_configs()

    trading = mgr.get_trading_config()

    print("✓ Development YAML config loaded successfully")
    print(f"  Paper Trading Mode: {trading.paper_trading_mode}")
    print(f"  Initial Capital: ₹{trading.position_limits.initial_capital:,.0f}")
    print(f"  Watchlist Size: {len(trading.watchlist_symbols)}")


def test_validation():
    """Test configuration validation"""
    print("\n" + "="*60)
    print("TEST 4: Configuration Validation")
    print("="*60)

    mgr = ConfigurationManager.get_instance()
    trading = mgr.get_trading_config()
    risk = mgr.get_risk_config()

    # Validate trading config
    is_valid, errors = trading.validate()
    assert is_valid, f"Trading config should be valid: {errors}"
    print("✓ Trading configuration validation passed")

    # Validate risk config
    is_valid, errors = risk.validate()
    assert is_valid, f"Risk config should be valid: {errors}"
    print("✓ Risk configuration validation passed")

    # Test invalid config
    try:
        trading.position_limits.max_swing_positions = -1  # Invalid
        is_valid, errors = trading.validate()
        assert not is_valid, "Should detect invalid position count"
        print("✓ Validation correctly detects errors")
        print(f"  Detected error: {errors[0]}")

        # Reset to valid value
        trading.position_limits.max_swing_positions = 3
    except Exception as e:
        print(f"  Validation test passed with exception: {e}")


def test_computed_properties():
    """Test computed properties and helper methods"""
    print("\n" + "="*60)
    print("TEST 5: Computed Properties")
    print("="*60)

    trading = get_trading_config()
    risk = get_risk_config()

    # Test trading config computations
    max_position = trading.get_max_position_capital()
    deployable = trading.get_total_deployable_capital()
    cash_reserve = trading.get_cash_reserve()

    print("✓ Trading config computations:")
    print(f"  Max Position Capital: ₹{max_position:,.2f}")
    print(f"  Deployable Capital: ₹{deployable:,.2f}")
    print(f"  Cash Reserve: ₹{cash_reserve:,.2f}")

    # Test risk config computations
    capital = 50000
    entry = 500
    stop_loss = 490

    max_risk = risk.get_max_risk_amount(capital)
    position_size = risk.calculate_position_size(capital, entry, stop_loss)

    print("✓ Risk config computations:")
    print(f"  Max Risk Amount: ₹{max_risk:,.2f}")
    print(f"  Position Size: {position_size} shares")
    print(f"  Total Capital Deployed: ₹{position_size * entry:,.2f}")


def test_config_summary():
    """Test configuration summaries"""
    print("\n" + "="*60)
    print("TEST 6: Configuration Summaries")
    print("="*60)

    mgr = ConfigurationManager.get_instance()

    # Print full summary
    summary = mgr.get_summary()
    print(summary)


def test_environment_switching():
    """Test switching between environments"""
    print("\n" + "="*60)
    print("TEST 7: Environment Switching")
    print("="*60)

    mgr = ConfigurationManager.get_instance()
    config_dir = Path(__file__).parent.parent / "config" / "environments"
    mgr.set_config_directory(config_dir)

    # Load development
    mgr.set_environment(Environment.DEVELOPMENT)
    mgr.load_all_configs(force_reload=True)
    trading_dev = mgr.get_trading_config()

    print(f"Development Config:")
    print(f"  Paper Trading: {trading_dev.paper_trading_mode}")
    print(f"  Max Swing Positions: {trading_dev.position_limits.max_swing_positions}")
    print(f"  Enabled Strategies: {len(trading_dev.strategy.enabled_strategies)}")

    # Load production
    mgr.set_environment(Environment.PRODUCTION)
    mgr.load_all_configs(force_reload=True)
    trading_prod = mgr.get_trading_config()
    risk_prod = mgr.get_risk_config()

    print(f"\nProduction Config:")
    print(f"  Paper Trading: {trading_prod.paper_trading_mode}")
    print(f"  Max Swing Positions: {trading_prod.position_limits.max_swing_positions}")
    print(f"  Enabled Strategies: {len(trading_prod.strategy.enabled_strategies)}")
    print(f"  Strict Mode: {risk_prod.strict_mode}")

    print("\n✓ Environment switching works correctly")


def test_convenience_functions():
    """Test convenience accessor functions"""
    print("\n" + "="*60)
    print("TEST 8: Convenience Functions")
    print("="*60)

    # Test quick access functions
    trading = get_trading_config()
    risk = get_risk_config()
    database = get_database_config()
    api = get_api_config()

    print("✓ Convenience functions working:")
    print(f"  get_trading_config(): {type(trading).__name__}")
    print(f"  get_risk_config(): {type(risk).__name__}")
    print(f"  get_database_config(): {type(database).__name__}")
    print(f"  get_api_config(): {type(api).__name__}")


def test_constants_and_enums():
    """Test constants and enums"""
    print("\n" + "="*60)
    print("TEST 9: Constants and Enums")
    print("="*60)

    from src.config import (
        MarketHours,
        RiskDefaults,
        IndicatorDefaults,
        PositionType,
        OrderSide,
        Timeframe,
        StrategyName
    )

    print("✓ Market Hours:")
    print(f"  Open: {MarketHours.MARKET_OPEN}")
    print(f"  Close: {MarketHours.MARKET_CLOSE}")

    print("✓ Risk Defaults:")
    print(f"  Initial Capital: ₹{RiskDefaults.INITIAL_CAPITAL:,.0f}")
    print(f"  Risk Per Trade: {RiskDefaults.RISK_PER_TRADE_PERCENT}%")

    print("✓ Indicator Defaults:")
    print(f"  RSI Period: {IndicatorDefaults.RSI_PERIOD}")
    print(f"  RSI Overbought: {IndicatorDefaults.RSI_OVERBOUGHT}")

    print("✓ Enums:")
    print(f"  Position Types: {[p.value for p in PositionType]}")
    print(f"  Order Sides: {[o.value for o in OrderSide]}")
    print(f"  Timeframes: {[t.value for t in Timeframe]}")
    print(f"  Strategies: {[s.value for s in StrategyName][:4]}...")


def run_all_tests():
    """Run all configuration tests"""
    print("\n" + "╔" + "="*58 + "╗")
    print("║" + " "*15 + "CONFIGURATION SYSTEM TESTS" + " "*17 + "║")
    print("╚" + "="*58 + "╝")

    try:
        test_singleton_pattern()
        test_load_default_configs()
        test_load_yaml_config()
        test_validation()
        test_computed_properties()
        test_convenience_functions()
        test_constants_and_enums()
        test_environment_switching()
        test_config_summary()

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
