"""
Analysis & Signals Page
Technical analysis with indicators and signals
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.dashboard.utils.data_loader import get_ohlcv_data, get_indicator_values, get_available_symbols
from src.dashboard.utils.formatters import format_currency

st.title("🧮 Technical Analysis & Signals")
st.markdown("Deep dive into technical indicators and trading signals")

# Symbol selector
col1, col2 = st.columns([2, 1])
with col1:
    symbols = get_available_symbols()
    selected_symbol = st.selectbox("Select Symbol", symbols)

with col2:
    timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "1d"], index=4)

st.markdown("---")

# Get data
df = get_ohlcv_data(selected_symbol, timeframe=timeframe, days=30)

if len(df) > 0:
    # Indicator toggles
    st.markdown("### 📊 Select Indicators to Display")
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        show_rsi = st.checkbox("RSI", value=True)
    with col2:
        show_macd = st.checkbox("MACD", value=True)
    with col3:
        show_bb = st.checkbox("Bollinger Bands", value=True)
    with col4:
        show_ema = st.checkbox("EMA", value=False)
    with col5:
        show_volume = st.checkbox("Volume", value=True)
    with col6:
        show_sma = st.checkbox("SMA", value=False)

    st.markdown("---")

    # Create subplots
    rows = 1
    if show_rsi:
        rows += 1
    if show_macd:
        rows += 1
    if show_volume:
        rows += 1

    row_heights = [0.6] + [0.2] * (rows - 1) if rows > 1 else [1.0]

    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=row_heights,
        subplot_titles=['Price'] + (['RSI'] if show_rsi else []) + (['MACD'] if show_macd else []) + (['Volume'] if show_volume else [])
    )

    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name=selected_symbol
        ),
        row=1, col=1
    )

    # Bollinger Bands
    if show_bb:
        # Calculate Bollinger Bands
        df['sma'] = df['close'].rolling(window=20).mean()
        df['std'] = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['sma'] + (df['std'] * 2)
        df['bb_lower'] = df['sma'] - (df['std'] * 2)

        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['bb_upper'], name='BB Upper',
                      line=dict(color='rgba(250, 100, 100, 0.5)', dash='dash')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['sma'], name='BB Middle',
                      line=dict(color='rgba(100, 100, 250, 0.5)')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['bb_lower'], name='BB Lower',
                      line=dict(color='rgba(250, 100, 100, 0.5)', dash='dash'),
                      fill='tonexty', fillcolor='rgba(200, 200, 250, 0.2)'),
            row=1, col=1
        )

    # EMA
    if show_ema:
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()

        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['ema_12'], name='EMA 12',
                      line=dict(color='orange', width=1)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['ema_26'], name='EMA 26',
                      line=dict(color='purple', width=1)),
            row=1, col=1
        )

    # SMA
    if show_sma:
        df['sma_50'] = df['close'].rolling(window=50).mean()
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['sma_50'], name='SMA 50',
                      line=dict(color='green', width=1)),
            row=1, col=1
        )

    current_row = 2

    # RSI
    if show_rsi:
        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['rsi'], name='RSI',
                      line=dict(color='purple', width=2)),
            row=current_row, col=1
        )

        # Add reference lines
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=current_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=current_row, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="gray", opacity=0.5, row=current_row, col=1)

        current_row += 1

    # MACD
    if show_macd:
        # Calculate MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['histogram'] = df['macd'] - df['signal']

        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['macd'], name='MACD',
                      line=dict(color='blue', width=2)),
            row=current_row, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['signal'], name='Signal',
                      line=dict(color='orange', width=2)),
            row=current_row, col=1
        )
        fig.add_trace(
            go.Bar(x=df['timestamp'], y=df['histogram'], name='Histogram',
                   marker_color='gray', opacity=0.3),
            row=current_row, col=1
        )

        current_row += 1

    # Volume
    if show_volume:
        colors = ['red' if row['close'] < row['open'] else 'green' for _, row in df.iterrows()]
        fig.add_trace(
            go.Bar(x=df['timestamp'], y=df['volume'], name='Volume',
                   marker_color=colors, opacity=0.5),
            row=current_row, col=1
        )

    # Update layout
    fig.update_layout(
        title=f"{selected_symbol} - {timeframe} Chart",
        xaxis_rangeslider_visible=False,
        height=800,
        hovermode='x unified',
        showlegend=True
    )

    fig.update_xaxes(title_text="Date", row=rows, col=1)

    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("No data available for selected symbol")

st.markdown("---")

# Current indicator values
st.markdown("### 🎯 Current Indicator Values")

indicators = get_indicator_values(selected_symbol, timeframe)

col1, col2 = st.columns(2)

with col1:
    # RSI
    if 'RSI' in indicators:
        rsi_data = indicators['RSI']
        rsi_value = rsi_data['value']

        if rsi_value > 70:
            color = "🔴"
            status = "Overbought"
        elif rsi_value < 30:
            color = "🟢"
            status = "Oversold"
        else:
            color = "🟡"
            status = "Neutral"

        st.markdown(f"""
        <div style='padding: 1rem; border-radius: 8px; background: #f5f5f5;'>
            <h4>{color} RSI (14)</h4>
            <h2>{rsi_value:.1f}</h2>
            <p><strong>{status}</strong></p>
            <p style='font-size: 0.9rem;'>{rsi_data['description']}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")

    # MACD
    if 'MACD' in indicators:
        macd_data = indicators['MACD']
        signal_type = macd_data['signal_type']
        color = "🟢" if signal_type == "BUY" else "🔴" if signal_type == "SELL" else "🟡"

        st.markdown(f"""
        <div style='padding: 1rem; border-radius: 8px; background: #f5f5f5;'>
            <h4>{color} MACD</h4>
            <p><strong>MACD:</strong> {macd_data['macd']:.2f}</p>
            <p><strong>Signal:</strong> {macd_data['signal']:.2f}</p>
            <p><strong>Histogram:</strong> {macd_data['histogram']:.2f}</p>
            <p style='font-size: 0.9rem;'>{macd_data['description']}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")

    # ADX
    if 'ADX' in indicators:
        adx_data = indicators['ADX']
        adx_value = adx_data['value']
        color = "🟢" if adx_value > 25 else "🟡"

        st.markdown(f"""
        <div style='padding: 1rem; border-radius: 8px; background: #f5f5f5;'>
            <h4>{color} ADX</h4>
            <h2>{adx_value:.1f}</h2>
            <p><strong>{adx_data['signal']}</strong></p>
            <p style='font-size: 0.9rem;'>{adx_data['description']}</p>
        </div>
        """, unsafe_allow_html=True)

with col2:
    # Bollinger Bands
    if 'BB' in indicators:
        bb_data = indicators['BB']
        signal = bb_data['signal']
        color = "🟢" if signal == "BUY" else "🔴" if signal == "SELL" else "🟡"

        st.markdown(f"""
        <div style='padding: 1rem; border-radius: 8px; background: #f5f5f5;'>
            <h4>{color} Bollinger Bands</h4>
            <p><strong>Upper:</strong> {format_currency(bb_data['upper'])}</p>
            <p><strong>Middle:</strong> {format_currency(bb_data['middle'])}</p>
            <p><strong>Lower:</strong> {format_currency(bb_data['lower'])}</p>
            <p><strong>Current:</strong> {format_currency(bb_data['current'])}</p>
            <p style='font-size: 0.9rem;'>{bb_data['description']}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")

    # Stochastic
    if 'STOCH' in indicators:
        stoch_data = indicators['STOCH']
        stoch_value = stoch_data['k']

        if stoch_value > 80:
            color = "🔴"
            status = "Overbought"
        elif stoch_value < 20:
            color = "🟢"
            status = "Oversold"
        else:
            color = "🟡"
            status = "Neutral"

        st.markdown(f"""
        <div style='padding: 1rem; border-radius: 8px; background: #f5f5f5;'>
            <h4>{color} Stochastic</h4>
            <h2>{stoch_value:.1f}</h2>
            <p><strong>{status}</strong></p>
            <p style='font-size: 0.9rem;'>{stoch_data['description']}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")

    # ATR
    if 'ATR' in indicators:
        atr_data = indicators['ATR']

        st.markdown(f"""
        <div style='padding: 1rem; border-radius: 8px; background: #f5f5f5;'>
            <h4>📊 ATR (14)</h4>
            <h2>{format_currency(atr_data['value'])}</h2>
            <p><strong>{atr_data['signal']} Volatility</strong></p>
            <p style='font-size: 0.9rem;'>{atr_data['description']}</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Signal aggregation
st.markdown("### 🎲 Signal Aggregation")

st.info("This section shows how all indicators vote to generate the final trading signal")

# Mock aggregation
bullish = 3
bearish = 1
neutral = 2

total = bullish + bearish + neutral
bullish_pct = (bullish / total) * 100
bearish_pct = (bearish / total) * 100
neutral_pct = (neutral / total) * 100

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Bullish Indicators", bullish, f"{bullish_pct:.0f}%")

with col2:
    st.metric("Bearish Indicators", bearish, f"{bearish_pct:.0f}%")

with col3:
    st.metric("Neutral Indicators", neutral, f"{neutral_pct:.0f}%")

# Overall signal
if bullish > bearish:
    overall_signal = "BUY"
    confidence = bullish_pct
    color = "green"
elif bearish > bullish:
    overall_signal = "SELL"
    confidence = bearish_pct
    color = "red"
else:
    overall_signal = "HOLD"
    confidence = 50
    color = "orange"

st.markdown(f"""
<div style='padding: 2rem; border-radius: 12px; background: linear-gradient(135deg, {color}22, {color}44); border: 2px solid {color};'>
    <h2 style='text-align: center;'>Overall Signal: {overall_signal}</h2>
    <h3 style='text-align: center;'>Confidence: {confidence:.1f}%</h3>
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption("📊 Technical analysis with 6 indicators | Real-time calculations")
