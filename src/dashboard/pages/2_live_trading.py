"""
Live Trading Page
Real-time monitoring of active positions and live prices
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.dashboard.utils.data_loader import get_open_positions, get_live_price, get_recent_signals
from src.dashboard.utils.formatters import format_currency, format_percentage, format_duration

# Auto-refresh every 5 seconds
st_autorefresh(interval=5000, key="live_trading_refresh")

st.title("📈 Live Trading Monitor")
st.markdown("Real-time monitoring of active positions and market data")

# Top metrics
positions_df = get_open_positions()
if len(positions_df) > 0:
    total_pnl = positions_df['pnl'].sum()
    total_pnl_pct = (total_pnl / positions_df['entry_value'].sum()) * 100
    winning_positions = len(positions_df[positions_df['pnl'] > 0])
    losing_positions = len(positions_df[positions_df['pnl'] < 0])

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Open P&L", format_currency(total_pnl), format_percentage(total_pnl_pct))

    with col2:
        st.metric("Open Positions", len(positions_df))

    with col3:
        st.metric("Winning", winning_positions, delta_color="normal")

    with col4:
        st.metric("Losing", losing_positions, delta_color="inverse")

    st.markdown("---")

    # Live price ticker
    st.markdown("### 📊 Live Prices")

    ticker_cols = st.columns(min(len(positions_df), 4))
    for idx, (_, position) in enumerate(positions_df.iterrows()):
        if idx < 4:  # Show max 4 tickers
            with ticker_cols[idx]:
                symbol = position['symbol'].replace('.NS', '')
                current_price = position['current_price']
                pnl_pct = position['pnl_pct']

                color = "🟢" if pnl_pct >= 0 else "🔴"
                st.markdown(f"""
                <div style='text-align: center; padding: 1rem; border-radius: 8px; background: {"#e8f5e9" if pnl_pct >= 0 else "#ffebee"}'>
                    <h4>{symbol}</h4>
                    <h2>{color} {format_currency(current_price)}</h2>
                    <p style='font-weight: bold;'>{format_percentage(pnl_pct)}</p>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    # Open positions table
    st.markdown("### 💼 Open Positions")

    # Add action buttons column
    display_df = positions_df.copy()
    display_df['entry_time'] = pd.to_datetime(display_df['entry_time']).dt.strftime('%H:%M')

    # Format currency and percentage columns
    display_df['entry_price'] = display_df['entry_price'].apply(lambda x: f"₹{x:,.2f}")
    display_df['current_price'] = display_df['current_price'].apply(lambda x: f"₹{x:,.2f}")
    display_df['pnl'] = display_df['pnl'].apply(lambda x: f"₹{x:,.2f}")
    display_df['pnl_pct'] = display_df['pnl_pct'].apply(lambda x: f"{x:+.2f}%")
    display_df['stop_loss'] = display_df['stop_loss'].apply(lambda x: f"₹{x:,.2f}")
    display_df['target'] = display_df['target'].apply(lambda x: f"₹{x:,.2f}")

    # Select columns to display
    columns_to_show = ['symbol', 'entry_price', 'current_price', 'qty', 'pnl', 'pnl_pct',
                       'stop_loss', 'target', 'entry_time', 'duration']

    st.dataframe(
        display_df[columns_to_show],
        use_container_width=True,
        hide_index=True
    )

    # Position details (expandable)
    st.markdown("### 📋 Position Details")

    for _, position in positions_df.iterrows():
        with st.expander(f"{position['symbol']} - {format_currency(position['pnl'])} ({format_percentage(position['pnl_pct'])})"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Entry Details:**")
                st.write(f"Entry Price: {format_currency(position['entry_price'])}")
                st.write(f"Quantity: {position['qty']}")
                st.write(f"Entry Value: {format_currency(position['entry_value'])}")
                st.write(f"Entry Time: {position['entry_time']}")
                st.write(f"Duration: {position['duration']}")

            with col2:
                st.markdown("**Current Status:**")
                st.write(f"Current Price: {format_currency(position['current_price'])}")
                st.write(f"Current Value: {format_currency(position['current_value'])}")
                st.write(f"P&L: {format_currency(position['pnl'])} ({format_percentage(position['pnl_pct'])})")
                st.write(f"Stop Loss: {format_currency(position['stop_loss'])} ({format_percentage(position['sl_distance_pct'])})")
                st.write(f"Target: {format_currency(position['target'])} ({format_percentage(position['target_distance_pct'])})")

            # Progress bar to target
            st.markdown("**Progress to Target:**")
            total_distance = position['target'] - position['stop_loss']
            current_distance = position['current_price'] - position['stop_loss']
            progress = max(0, min(100, (current_distance / total_distance) * 100))

            st.progress(progress / 100)
            st.caption(f"{progress:.1f}% to target")

            # Risk-Reward
            st.markdown(f"**Risk-Reward Ratio:** {position['risk_reward']:.2f}:1")

            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"Close Position", key=f"close_{position['symbol']}"):
                    st.warning(f"Close position for {position['symbol']}? (Not implemented in demo)")

            with col2:
                if st.button(f"Modify SL", key=f"modify_sl_{position['symbol']}"):
                    st.info(f"Modify stop-loss for {position['symbol']} (Not implemented in demo)")

            with col3:
                if st.button(f"Modify Target", key=f"modify_target_{position['symbol']}"):
                    st.info(f"Modify target for {position['symbol']} (Not implemented in demo)")

else:
    st.info("No open positions currently")

st.markdown("---")

# Pending signals
st.markdown("### 🎯 Latest Signals")

signals_df = get_recent_signals(limit=5)

if len(signals_df) > 0:
    for _, signal in signals_df.iterrows():
        col1, col2, col3, col4 = st.columns([2, 1, 1, 2])

        with col1:
            signal_type = signal['signal']
            color = "green" if signal_type == "BUY" else "red"
            st.markdown(f"**{signal['symbol']}** - :{color}[{signal_type}]")

        with col2:
            st.write(f"Price: {format_currency(signal['price'])}")

        with col3:
            confidence = signal['confidence']
            if confidence >= 75:
                st.success(f"{confidence:.1f}% confidence")
            elif confidence >= 60:
                st.warning(f"{confidence:.1f}% confidence")
            else:
                st.error(f"{confidence:.1f}% confidence")

        with col4:
            st.caption(f"Bullish: {signal['bullish']} | Bearish: {signal['bearish']} | Neutral: {signal['neutral']}")

        st.caption(f"Reason: {signal['reason']}")
        st.markdown("---")
else:
    st.info("No recent signals")

# Live charts section
st.markdown("### 📈 Live Charts")

selected_symbol = st.selectbox("Select Symbol", positions_df['symbol'].tolist() if len(positions_df) > 0 else ['RELIANCE.NS'])

if selected_symbol:
    # Get OHLCV data
    from src.dashboard.utils.data_loader import get_ohlcv_data

    df = get_ohlcv_data(selected_symbol, timeframe='1h', days=1)

    if len(df) > 0:
        # Create candlestick chart
        fig = go.Figure(data=[go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name=selected_symbol
        )])

        # Add volume bars
        fig.add_trace(go.Bar(
            x=df['timestamp'],
            y=df['volume'],
            name='Volume',
            yaxis='y2',
            opacity=0.3
        ))

        # Add stop-loss and target lines if position exists
        position = positions_df[positions_df['symbol'] == selected_symbol]
        if len(position) > 0:
            position = position.iloc[0]

            # Stop loss line
            fig.add_hline(
                y=position['stop_loss'],
                line_dash="dash",
                line_color="red",
                annotation_text=f"Stop Loss: {format_currency(position['stop_loss'])}",
                annotation_position="right"
            )

            # Target line
            fig.add_hline(
                y=position['target'],
                line_dash="dash",
                line_color="green",
                annotation_text=f"Target: {format_currency(position['target'])}",
                annotation_position="right"
            )

            # Entry line
            fig.add_hline(
                y=position['entry_price'],
                line_dash="dot",
                line_color="blue",
                annotation_text=f"Entry: {format_currency(position['entry_price'])}",
                annotation_position="right"
            )

        fig.update_layout(
            title=f"{selected_symbol} - Live Chart",
            yaxis_title="Price (₹)",
            yaxis2=dict(title="Volume", overlaying='y', side='right'),
            xaxis_rangeslider_visible=False,
            height=500,
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No chart data available")

# Footer
st.markdown("---")
st.caption("🔄 Auto-refreshes every 5 seconds | Last updated: " + pd.Timestamp.now().strftime("%H:%M:%S"))
