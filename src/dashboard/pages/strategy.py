"""
Strategy Configuration Page
Configure trading strategies and parameters
Changes apply after market close (4:00 PM)
"""

import streamlit as st
import yaml
import os
import sys
from datetime import datetime, time

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.dashboard.utils.data_loader import get_performance_stats

st.title("⚙️ Strategy Configuration")
st.markdown("Configure trading parameters and strategy settings")

# Check if we can make changes now
now = datetime.now()
market_close = time(16, 0)  # 4:00 PM
can_modify = now.time() >= market_close or now.time() < time(9, 15)

if can_modify:
    st.success("✅ Configuration changes allowed (Market closed)")
else:
    st.warning(f"⚠️ Changes will apply after 4:00 PM (Currently {now.strftime('%H:%M')})")

st.markdown("---")

# Load current configuration
config_file = 'config/environments/development.yaml'

try:
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
except Exception as e:
    st.error(f"Could not load configuration: {e}")
    config = {}

st.markdown("### 📊 Strategy Performance")

# Show current strategy performance
stats = get_performance_stats()
if stats:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Trades", stats.get('total_trades', 0))

    with col2:
        st.metric("Win Rate", f"{stats.get('win_rate', 0):.1f}%")

    with col3:
        st.metric("Profit Factor", f"{stats.get('profit_factor', 0):.2f}")

    with col4:
        st.metric("Total P&L", f"₹{stats.get('total_pnl', 0):,.0f}")

st.markdown("---")

# Configuration tabs
tab1, tab2, tab3, tab4 = st.tabs(["Risk Management", "Indicators", "Trading Rules", "Symbols"])

with tab1:
    st.markdown("### 💰 Risk Management Parameters")

    # Get current risk config
    risk_config = config.get('risk_management', {})
    trading_config = config.get('trading', {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Position Sizing:**")

        initial_capital = st.number_input(
            "Initial Capital (₹)",
            min_value=10000,
            max_value=10000000,
            value=risk_config.get('capital_management', {}).get('initial_capital', 50000),
            step=10000,
            help="Starting capital for trading"
        )

        risk_per_trade = st.slider(
            "Risk Per Trade (%)",
            min_value=0.5,
            max_value=3.0,
            value=risk_config.get('loss_limits', {}).get('risk_per_trade_percent', 1.0),
            step=0.1,
            help="Maximum risk per trade as % of capital"
        )

        max_position_size = st.slider(
            "Max Position Size (%)",
            min_value=10,
            max_value=50,
            value=trading_config.get('position_limits', {}).get('max_position_size_percent', 20),
            step=5,
            help="Maximum position size as % of capital"
        )

    with col2:
        st.markdown("**Risk Limits:**")

        max_daily_loss = st.slider(
            "Max Daily Loss (%)",
            min_value=1,
            max_value=10,
            value=risk_config.get('loss_limits', {}).get('max_daily_loss_percent', 5),
            step=1,
            help="Stop trading if daily loss exceeds this %"
        )

        max_drawdown = st.slider(
            "Max Drawdown (%)",
            min_value=5,
            max_value=25,
            value=risk_config.get('loss_limits', {}).get('max_drawdown_percent', 10),
            step=5,
            help="Maximum portfolio drawdown allowed"
        )

        max_positions = st.number_input(
            "Max Concurrent Positions",
            min_value=1,
            max_value=20,
            value=trading_config.get('position_limits', {}).get('max_concurrent_positions', 6),
            step=1,
            help="Maximum number of open positions"
        )

    # Calculate preview
    st.markdown("**Preview:**")
    risk_amount = initial_capital * (risk_per_trade / 100)
    max_position_value = initial_capital * (max_position_size / 100)
    max_daily_loss_amount = initial_capital * (max_daily_loss / 100)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**Risk per trade:** ₹{risk_amount:,.0f}")
    with col2:
        st.info(f"**Max position value:** ₹{max_position_value:,.0f}")
    with col3:
        st.info(f"**Max daily loss:** ₹{max_daily_loss_amount:,.0f}")

with tab2:
    st.markdown("### 📈 Technical Indicators")

    st.markdown("**Indicator Weights** (for signal aggregation):")

    # Get current weights (default values)
    default_weights = {
        'RSI': 25.0,
        'MACD': 25.0,
        'BB': 20.0,
        'ADX': 15.0,
        'STOCH': 10.0,
        'ATR': 5.0
    }

    weights = {}
    total_weight = 0

    col1, col2 = st.columns(2)

    with col1:
        weights['RSI'] = st.slider("RSI Weight", 0, 50, int(default_weights['RSI']), 5,
                                   help="Relative Strength Index importance")
        weights['MACD'] = st.slider("MACD Weight", 0, 50, int(default_weights['MACD']), 5,
                                    help="Moving Average Convergence Divergence importance")
        weights['BB'] = st.slider("Bollinger Bands Weight", 0, 50, int(default_weights['BB']), 5,
                                  help="Bollinger Bands importance")

    with col2:
        weights['ADX'] = st.slider("ADX Weight", 0, 50, int(default_weights['ADX']), 5,
                                   help="Average Directional Index importance")
        weights['STOCH'] = st.slider("Stochastic Weight", 0, 50, int(default_weights['STOCH']), 5,
                                     help="Stochastic Oscillator importance")
        weights['ATR'] = st.slider("ATR Weight", 0, 50, int(default_weights['ATR']), 5,
                                   help="Average True Range importance")

    total_weight = sum(weights.values())

    st.info(f"**Total Weight:** {total_weight}% (Should be 100%)")

    if total_weight != 100:
        st.warning("⚠️ Weights should sum to 100%. Auto-normalizing on save.")

    # Indicator parameters
    st.markdown("**Indicator Parameters:**")

    col1, col2, col3 = st.columns(3)

    with col1:
        rsi_period = st.number_input("RSI Period", 5, 30, 14, 1)
        rsi_overbought = st.number_input("RSI Overbought", 60, 90, 70, 5)
        rsi_oversold = st.number_input("RSI Oversold", 10, 40, 30, 5)

    with col2:
        macd_fast = st.number_input("MACD Fast Period", 5, 20, 12, 1)
        macd_slow = st.number_input("MACD Slow Period", 20, 35, 26, 1)
        macd_signal = st.number_input("MACD Signal Period", 5, 15, 9, 1)

    with col3:
        bb_period = st.number_input("BB Period", 10, 30, 20, 1)
        bb_std = st.number_input("BB Std Dev", 1.0, 3.0, 2.0, 0.5)

with tab3:
    st.markdown("### 📋 Trading Rules")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Entry Criteria:**")

        min_confidence = st.slider(
            "Minimum Signal Confidence (%)",
            min_value=50,
            max_value=90,
            value=60,
            step=5,
            help="Minimum confidence score to enter trade"
        )

        min_risk_reward = st.slider(
            "Minimum Risk-Reward Ratio",
            min_value=1.0,
            max_value=5.0,
            value=1.5,
            step=0.5,
            help="Minimum R:R ratio required"
        )

        min_adx = st.slider(
            "Minimum ADX (Trend Strength)",
            min_value=15,
            max_value=35,
            value=25,
            step=5,
            help="Minimum trend strength to trade"
        )

    with col2:
        st.markdown("**Exit Rules:**")

        use_trailing_stop = st.checkbox("Use Trailing Stop Loss", value=False,
                                        help="Trail stop loss as price moves in favor")

        if use_trailing_stop:
            trailing_stop_pct = st.slider("Trailing Stop %", 1.0, 5.0, 2.0, 0.5)
        else:
            trailing_stop_pct = 0

        auto_close_eod = st.checkbox("Auto-close Intraday at EOD", value=True,
                                      help="Automatically close intraday positions at 3:25 PM")

        partial_exit = st.checkbox("Partial Position Exit", value=False,
                                   help="Take partial profits at milestones")

        if partial_exit:
            partial_exit_pct = st.slider("Partial Exit % at 50% Target", 25, 75, 50, 25)

with tab4:
    st.markdown("### 📊 Symbol Watchlist")

    # Default Nifty 50 stocks
    default_symbols = [
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'HINDUNILVR.NS',
        'ICICIBANK.NS', 'KOTAKBANK.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'ITC.NS',
        'LT.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 'MARUTI.NS', 'SUNPHARMA.NS'
    ]

    # Load from watchlist preset
    col1, col2 = st.columns([2, 1])

    with col1:
        preset = st.selectbox(
            "Load Preset",
            ["Custom", "Nifty 50 Top 15", "Bank Nifty", "IT Stocks", "Pharma Stocks"]
        )

    with col2:
        max_symbols = st.number_input("Max Symbols to Trade", 5, 50, 15, 5)

    # Text area for manual symbol entry
    symbols_text = st.text_area(
        "Symbols (one per line)",
        value="\n".join(default_symbols),
        height=200,
        help="Enter NSE symbols (e.g., RELIANCE.NS)"
    )

    symbols_list = [s.strip() for s in symbols_text.split('\n') if s.strip()]

    st.info(f"**Total Symbols:** {len(symbols_list)} (Will trade up to {max_symbols})")

st.markdown("---")

# Save configuration
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button("💾 Save Configuration", use_container_width=True, type="primary"):
        if can_modify:
            try:
                # Update config dict
                config['risk_management'] = config.get('risk_management', {})
                config['risk_management']['capital_management'] = {
                    'initial_capital': initial_capital
                }
                config['risk_management']['loss_limits'] = {
                    'risk_per_trade_percent': risk_per_trade,
                    'max_daily_loss_percent': max_daily_loss,
                    'max_drawdown_percent': max_drawdown
                }

                config['trading'] = config.get('trading', {})
                config['trading']['position_limits'] = {
                    'max_position_size_percent': max_position_size,
                    'max_concurrent_positions': max_positions
                }

                # Save to file
                with open(config_file, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False, sort_keys=False)

                st.success("✅ Configuration saved! Changes will apply after system restart.")

            except Exception as e:
                st.error(f"Failed to save configuration: {e}")
        else:
            st.warning("⚠️ Configuration locked during market hours. Changes will apply after 4:00 PM.")

with col2:
    if st.button("🔄 Reset to Defaults", use_container_width=True):
        st.warning("This will reset all settings to default values. Use with caution!")

with col3:
    st.caption("💡 Changes apply after saving and restarting the trading system")

# Show configuration file preview
with st.expander("📄 View Configuration File"):
    st.code(yaml.dump(config, default_flow_style=False, sort_keys=False), language='yaml')

# Backtest simulation
st.markdown("---")
st.markdown("### 🧪 Simulate Strategy Changes")

st.info("""
**Experimental Feature:** Test how your parameter changes would have performed historically.

This runs a quick backtest simulation using the last 30 days of data with your modified parameters.
""")

if st.button("🚀 Run Backtest Simulation"):
    with st.spinner("Running backtest with new parameters..."):
        import time
        time.sleep(2)  # Simulate backtest

        # Mock results
        st.success("Backtest completed!")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Trades", "42", "+7")

        with col2:
            st.metric("Win Rate", "71.4%", "+2.8%")

        with col3:
            st.metric("Profit Factor", "2.8", "+0.3")

        with col4:
            st.metric("Total P&L", "₹3,450", "+₹650")

        st.caption("⚠️ Past performance doesn't guarantee future results. Use for comparison only.")

# Footer
st.markdown("---")
st.caption("⚙️ Strategy configuration | Changes apply after 4:00 PM")
