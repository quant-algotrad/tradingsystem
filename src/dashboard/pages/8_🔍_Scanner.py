"""
Market Scanner Page
Real-time scanning for trading opportunities across all symbols
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.dashboard.utils.data_loader import get_available_symbols, get_live_price, get_indicator_values
from streamlit_autorefresh import st_autorefresh

# Auto-refresh every 30 seconds
st_autorefresh(interval=30000, key="scanner_refresh")

st.title("🔍 Market Scanner")
st.markdown("Find trading opportunities across all symbols in real-time")

# Scanner settings
st.sidebar.markdown("### 🎯 Scanner Settings")

scan_mode = st.sidebar.selectbox(
    "Scan Mode",
    ["All Signals", "Buy Only", "Sell Only", "High Confidence Only"]
)

min_confidence = st.sidebar.slider("Minimum Confidence", 50, 90, 65, 5)
min_indicators = st.sidebar.slider("Min Bullish Indicators", 3, 6, 4, 1)

symbols = get_available_symbols()
max_symbols = st.sidebar.number_input("Max Symbols to Scan", 5, 50, 15, 5)

st.markdown("---")

# Scan button
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    scan_button = st.button("🔍 Scan Now", use_container_width=True, type="primary")

with col2:
    auto_scan = st.checkbox("Auto-scan (30s)", value=True)

with col3:
    st.caption(f"Last scan: {datetime.now().strftime('%H:%M:%S')}")

st.markdown("---")

# Generate scan results (mock data for now)
def generate_scan_results():
    """Generate mock scan results"""
    np.random.seed(int(datetime.now().timestamp()))

    results = []

    for symbol in symbols[:max_symbols]:
        # Generate random signal
        signal_type = np.random.choice(['BUY', 'SELL', 'HOLD'], p=[0.3, 0.2, 0.5])
        confidence = np.random.uniform(50, 95)
        bullish_count = np.random.randint(0, 7)
        bearish_count = 6 - bullish_count
        price = np.random.uniform(500, 3000)

        # Generate random indicator reasons
        possible_reasons = [
            "RSI oversold", "MACD bullish crossover", "Price at lower Bollinger Band",
            "Strong uptrend (ADX > 25)", "Stochastic oversold", "Low volatility (ATR)",
            "RSI overbought", "MACD bearish crossover", "Price at upper Bollinger Band"
        ]

        reasons = np.random.choice(possible_reasons, size=2, replace=False)
        reason_str = ", ".join(reasons)

        # Calculate potential R:R
        if signal_type == 'BUY':
            entry = price
            stop_loss = price * 0.98  # 2% below
            target = price * 1.04  # 4% above
        else:
            entry = price
            stop_loss = price * 1.02
            target = price * 0.96

        risk = abs(entry - stop_loss)
        reward = abs(target - entry)
        rr_ratio = reward / risk if risk > 0 else 0

        results.append({
            'symbol': symbol,
            'price': price,
            'signal': signal_type,
            'confidence': confidence,
            'bullish': bullish_count,
            'bearish': bearish_count,
            'rr_ratio': rr_ratio,
            'reason': reason_str,
            'entry': entry,
            'sl': stop_loss,
            'target': target
        })

    return pd.DataFrame(results)

# Run scan
if scan_button or auto_scan:
    with st.spinner("Scanning market..."):
        scan_df = generate_scan_results()

        # Filter based on settings
        if scan_mode == "Buy Only":
            scan_df = scan_df[scan_df['signal'] == 'BUY']
        elif scan_mode == "Sell Only":
            scan_df = scan_df[scan_df['signal'] == 'SELL']
        elif scan_mode == "High Confidence Only":
            scan_df = scan_df[scan_df['confidence'] >= 75]

        scan_df = scan_df[scan_df['confidence'] >= min_confidence]
        scan_df = scan_df[scan_df['bullish'] >= min_indicators]

        # Sort by confidence
        scan_df = scan_df.sort_values('confidence', ascending=False)

        # Display summary
        st.markdown("### 📊 Scan Results")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            buy_signals = len(scan_df[scan_df['signal'] == 'BUY'])
            st.metric("Buy Signals", buy_signals)

        with col2:
            sell_signals = len(scan_df[scan_df['signal'] == 'SELL'])
            st.metric("Sell Signals", sell_signals)

        with col3:
            high_conf = len(scan_df[scan_df['confidence'] >= 75])
            st.metric("High Confidence", high_conf)

        with col4:
            avg_conf = scan_df['confidence'].mean() if len(scan_df) > 0 else 0
            st.metric("Avg Confidence", f"{avg_conf:.1f}%")

        st.markdown("---")

        if len(scan_df) > 0:
            # Opportunities section
            st.markdown("### 🎯 Top Opportunities")

            # Display top 5 opportunities
            top_opportunities = scan_df.head(5)

            for idx, row in top_opportunities.iterrows():
                signal_color = "green" if row['signal'] == 'BUY' else "red"
                confidence_emoji = "🟢" if row['confidence'] >= 75 else "🟡" if row['confidence'] >= 65 else "🟠"

                with st.expander(f"{confidence_emoji} {row['symbol']} - {row['signal']} ({row['confidence']:.1f}% confidence)"):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown("**Entry Setup:**")
                        st.write(f"Signal: :{signal_color}[{row['signal']}]")
                        st.write(f"Price: ₹{row['price']:,.2f}")
                        st.write(f"Confidence: {row['confidence']:.1f}%")
                        st.write(f"Bullish Indicators: {row['bullish']}/6")

                    with col2:
                        st.markdown("**Trade Plan:**")
                        st.write(f"Entry: ₹{row['entry']:,.2f}")
                        st.write(f"Stop Loss: ₹{row['sl']:,.2f}")
                        st.write(f"Target: ₹{row['target']:,.2f}")
                        st.write(f"R:R Ratio: {row['rr_ratio']:.2f}:1")

                    with col3:
                        st.markdown("**Reasoning:**")
                        st.write(row['reason'])

                        # Quick action button
                        if st.button(f"📊 View Chart", key=f"chart_{row['symbol']}"):
                            st.info("Chart view (integrate with Analysis page)")

            # Full table
            st.markdown("### 📋 All Scan Results")

            display_df = scan_df.copy()
            display_df['price'] = display_df['price'].apply(lambda x: f"₹{x:,.2f}")
            display_df['confidence'] = display_df['confidence'].apply(lambda x: f"{x:.1f}%")
            display_df['rr_ratio'] = display_df['rr_ratio'].apply(lambda x: f"{x:.2f}:1")

            st.dataframe(
                display_df[['symbol', 'signal', 'price', 'confidence', 'bullish', 'rr_ratio', 'reason']],
                use_container_width=True,
                hide_index=True
            )

            # Export
            if st.button("📥 Export Results to CSV"):
                csv = scan_df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    f"scan_results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    "text/csv"
                )

        else:
            st.warning("No opportunities found matching your criteria. Try adjusting the filters.")

else:
    st.info("👆 Click 'Scan Now' to find trading opportunities")

st.markdown("---")

# Watchlist section
st.markdown("### ⭐ Watchlist")

st.info("""
Add symbols to your watchlist for continuous monitoring.
Alerts will be sent when signals are detected.
""")

col1, col2 = st.columns([3, 1])

with col1:
    watchlist_symbols = st.multiselect(
        "Select Symbols",
        symbols,
        default=symbols[:5] if len(symbols) >= 5 else symbols
    )

with col2:
    st.markdown("")
    st.markdown("")
    if st.button("Save Watchlist", use_container_width=True):
        st.success("Watchlist saved!")

# Display watchlist status
if watchlist_symbols:
    st.markdown(f"**Monitoring {len(watchlist_symbols)} symbols:** {', '.join(watchlist_symbols)}")

# Scan presets
st.markdown("---")
st.markdown("### 🎨 Scan Presets")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🟢 Oversold Stocks", use_container_width=True):
        st.info("Scanning for oversold conditions (RSI < 30, Price near lower BB)")

with col2:
    if st.button("🔴 Overbought Stocks", use_container_width=True):
        st.info("Scanning for overbought conditions (RSI > 70, Price near upper BB)")

with col3:
    if st.button("📈 Strong Trends", use_container_width=True):
        st.info("Scanning for strong trends (ADX > 30, MACD bullish)")

# Alerts configuration
st.markdown("---")
st.markdown("### 🔔 Alert Settings")

enable_alerts = st.checkbox("Enable Alert Notifications", value=False)

if enable_alerts:
    col1, col2 = st.columns(2)

    with col1:
        alert_confidence = st.slider("Alert on Confidence >", 60, 90, 75, 5)

    with col2:
        alert_method = st.multiselect(
            "Alert Method",
            ["Dashboard Notification", "Email", "Telegram", "Sound"],
            default=["Dashboard Notification"]
        )

    st.info("Alerts will be sent when new opportunities matching your criteria are detected.")

# Footer
st.markdown("---")
st.caption("🔍 Market scanner | Auto-refreshes every 30 seconds")
