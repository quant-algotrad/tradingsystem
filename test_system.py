#!/usr/bin/env python3
"""
System Health Check Script
Run this to verify all components are working correctly
"""

import sys
sys.path.insert(0, '.')

def test_imports():
    """Test all core imports"""
    print("\n1️⃣  Testing Imports...")
    try:
        from src.strategy import StrategyFactory
        from src.risk import get_risk_manager
        from src.notifications import get_notification_manager
        from src.strategy.position_sizing import FixedRiskSizer
        print("   ✅ All imports successful")
        return True
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        return False

def test_strategies():
    """Test strategy system"""
    print("\n2️⃣  Testing Strategies...")
    try:
        from src.strategy import StrategyFactory

        strategies = StrategyFactory.get_available_strategies()
        print(f"   ✅ Found {len(strategies)} strategies:")
        for s in strategies:
            print(f"      • {s['name']}")

        # Test creation
        strategy = StrategyFactory.create('MULTI_INDICATOR')
        print(f"   ✅ Created: {strategy.get_name()}")
        return True
    except Exception as e:
        print(f"   ❌ Strategy error: {e}")
        return False

def test_position_sizing():
    """Test position sizing"""
    print("\n3️⃣  Testing Position Sizing...")
    try:
        from src.strategy.position_sizing import FixedRiskSizer

        sizer = FixedRiskSizer(risk_percent=1.0)
        result = sizer.calculate_position_size(
            capital=50000,
            entry_price=100.0,
            stop_loss=98.0
        )
        print(f"   ✅ Position sizing works")
        print(f"      Capital: ₹50,000 → {result.quantity} shares")
        return True
    except Exception as e:
        print(f"   ❌ Position sizing error: {e}")
        return False

def test_risk_management():
    """Test risk management"""
    print("\n4️⃣  Testing Risk Management...")
    try:
        from src.risk import RiskManager

        manager = RiskManager()

        trade_data = {
            'symbol': 'RELIANCE.NS',
            'quantity': 50,
            'entry_price': 2500,
            'stop_loss': 2450,
            'position_value': 125000,
            'risk_percent': 1.0,
            'risk_amount': 500,
            'capital': 50000,
            'current_positions': [],
            'current_position_count': 0,
            'existing_position_symbols': [],
            'position_type': 'SWING',
            'daily_pnl': 0,
            'sector': 'Energy'
        }

        passed, results = manager.validate_trade(trade_data, stop_on_first_failure=False)

        passed_count = sum(1 for r in results if r.passed)
        total_count = len(results)

        print(f"   ✅ Risk validators working: {passed_count}/{total_count} checks passed")
        return True
    except Exception as e:
        print(f"   ❌ Risk management error: {e}")
        return False

def test_notifications():
    """Test notification system"""
    print("\n5️⃣  Testing Notifications...")
    try:
        from src.notifications import get_notification_manager

        manager = get_notification_manager()
        status = manager.get_status()

        enabled = sum(1 for ch in status['channels'] if ch['enabled'])
        total = status['total_channels']

        print(f"   ✅ Notification system: {enabled}/{total} channels enabled")
        for ch in status['channels']:
            status_icon = '✅' if ch['enabled'] else '⚠️'
            print(f"      {status_icon} {ch['name']}")
        return True
    except Exception as e:
        print(f"   ❌ Notification error: {e}")
        return False

def test_config():
    """Test configuration files"""
    print("\n6️⃣  Testing Configuration...")
    try:
        import yaml

        with open('config/environments/development.yaml', 'r') as f:
            config = yaml.safe_load(f)

        symbols = config['trading']['watchlist_symbols']
        capital = config['trading']['position_limits']['initial_capital']
        risk = config['risk']['loss_limits']['risk_per_trade_percent']

        print(f"   ✅ Configuration valid")
        print(f"      • Watchlist: {len(symbols)} stocks")
        print(f"      • Capital: ₹{capital:,.0f}")
        print(f"      • Risk per trade: {risk}%")
        return True
    except Exception as e:
        print(f"   ❌ Config error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 70)
    print(" " * 20 + "TRADING SYSTEM HEALTH CHECK")
    print("=" * 70)

    tests = [
        test_imports,
        test_strategies,
        test_position_sizing,
        test_risk_management,
        test_notifications,
        test_config,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            results.append(False)

    print("\n" + "=" * 70)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("=" * 70)
        print("\n🚀 System is ready to use!")
        print("\n   Next steps:")
        print("   • Start system: docker-compose up -d")
        print("   • View dashboard: http://localhost:8050")
        print("   • Add stocks: config/environments/development.yaml")
        sys.exit(0)
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total} passed)")
        print("=" * 70)
        print("\n⚠️  Please check the errors above")
        sys.exit(1)

if __name__ == '__main__':
    main()
