"""
Risk Monitoring Page
Track risk exposure, limits, and portfolio health
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.dashboard.utils.data_loader import get_risk_metrics, get_open_positions
from src.dashboard.utils.formatters import format_currency, format_percentage

st.title("⚠️ Risk Monitoring")
st.markdown("Monitor risk exposure and ensure trading within safe limits")

# Get risk metrics
risk_metrics = get_risk_metrics()

# Top risk metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    portfolio_risk = risk_metrics['portfolio_risk']
    risk_pct = portfolio_risk['usage_pct']
    color = "🟢" if risk_pct < 50 else "🟡" if risk_pct < 75 else "🔴"

    st.markdown(f"""
    <div style='padding: 1.5rem; border-radius: 10px; background: {"#e8f5e9" if risk_pct < 50 else "#fff3e0" if risk_pct < 75 else "#ffebee"}'>
        <div style='font-size: 0.9rem; opacity: 0.8;'>Portfolio Risk</div>
        <div style='font-size: 2rem; font-weight: bold;'>{color} {risk_pct:.0f}%</div>
        <div style='font-size: 0.9rem;'>{format_currency(portfolio_risk['current'])} / {format_currency(portfolio_risk['max'])}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    daily_loss = risk_metrics['daily_loss']
    loss_pct = abs(daily_loss['usage_pct'])
    color = "🟢" if loss_pct < 20 else "🟡" if loss_pct < 50 else "🔴"

    st.markdown(f"""
    <div style='padding: 1.5rem; border-radius: 10px; background: {"#e8f5e9" if loss_pct < 20 else "#fff3e0" if loss_pct < 50 else "#ffebee"}'>
        <div style='font-size: 0.9rem; opacity: 0.8;'>Daily Loss</div>
        <div style='font-size: 2rem; font-weight: bold;'>{color} {loss_pct:.0f}%</div>
        <div style='font-size: 0.9rem;'>{format_currency(daily_loss['current'])} / {format_currency(daily_loss['max'])}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    max_dd = risk_metrics['max_drawdown']
    dd_pct = max_dd['current_pct']
    color = "🟢" if dd_pct < 3 else "🟡" if dd_pct < 7 else "🔴"

    st.markdown(f"""
    <div style='padding: 1.5rem; border-radius: 10px; background: {"#e8f5e9" if dd_pct < 3 else "#fff3e0" if dd_pct < 7 else "#ffebee"}'>
        <div style='font-size: 0.9rem; opacity: 0.8;'>Max Drawdown</div>
        <div style='font-size: 2rem; font-weight: bold;'>{color} {dd_pct:.1f}%</div>
        <div style='font-size: 0.9rem;'>{format_currency(max_dd['current'])} ({max_dd['max_pct']:.0f}% limit)</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    sharpe = risk_metrics['sharpe_ratio']
    color = "🟢" if sharpe > 1.5 else "🟡" if sharpe > 1.0 else "🔴"

    st.markdown(f"""
    <div style='padding: 1.5rem; border-radius: 10px; background: {"#e8f5e9" if sharpe > 1.5 else "#fff3e0" if sharpe > 1.0 else "#ffebee"}'>
        <div style='font-size: 0.9rem; opacity: 0.8;'>Sharpe Ratio</div>
        <div style='font-size: 2rem; font-weight: bold;'>{color} {sharpe:.2f}</div>
        <div style='font-size: 0.9rem;'>Risk-adjusted returns</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Risk gauges
st.markdown("### 📊 Risk Gauges")

col1, col2 = st.columns(2)

with col1:
    # Portfolio risk gauge
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=risk_metrics['portfolio_risk']['usage_pct'],
        title={'text': "Portfolio Risk Usage"},
        delta={'reference': 50},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgreen"},
                {'range': [50, 75], 'color': "yellow"},
                {'range': [75, 100], 'color': "red"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Daily loss gauge
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=abs(risk_metrics['daily_loss']['usage_pct']),
        title={'text': "Daily Loss Usage"},
        delta={'reference': 20},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkred"},
            'steps': [
                {'range': [0, 20], 'color': "lightgreen"},
                {'range': [20, 50], 'color': "yellow"},
                {'range': [50, 100], 'color': "red"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 80
            }
        }
    ))
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Position limits
st.markdown("### 💼 Position Limits Monitor")

positions_df = get_open_positions()

if len(positions_df) > 0:
    # Calculate position limits
    max_position_value = 10000  # ₹10,000 max per position (20% of ₹50,000)

    positions_df['limit_usage'] = (positions_df['current_value'] / max_position_value) * 100
    positions_df['status'] = positions_df['limit_usage'].apply(
        lambda x: '🟢 OK' if x < 75 else '🟡 Warning' if x < 95 else '🔴 Near Limit'
    )

    # Display table
    display_df = positions_df[['symbol', 'current_value', 'limit_usage', 'status']].copy()
    display_df['current_value'] = display_df['current_value'].apply(format_currency)
    display_df['limit_usage'] = display_df['limit_usage'].apply(lambda x: f"{x:.1f}%")

    display_df.columns = ['Symbol', 'Position Value', 'Limit Usage', 'Status']

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Visual chart
    fig = go.Figure()

    colors = ['green' if x < 75 else 'orange' if x < 95 else 'red'
             for x in positions_df['limit_usage']]

    fig.add_trace(go.Bar(
        x=positions_df['symbol'],
        y=positions_df['limit_usage'],
        marker_color=colors,
        text=positions_df['limit_usage'].apply(lambda x: f"{x:.1f}%"),
        textposition='auto',
    ))

    # Add reference lines
    fig.add_hline(y=75, line_dash="dash", line_color="orange", annotation_text="Warning (75%)")
    fig.add_hline(y=95, line_dash="dash", line_color="red", annotation_text="Limit (95%)")

    fig.update_layout(
        title="Position Size vs Limit",
        xaxis_title="Symbol",
        yaxis_title="Usage (%)",
        height=400,
        yaxis_range=[0, 110]
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("No open positions to monitor")

st.markdown("---")

# Stop-loss monitoring
st.markdown("### 🛡️ Stop-Loss Monitor")

if len(positions_df) > 0:
    st.markdown("Distance to stop-loss for each position:")

    for _, position in positions_df.iterrows():
        sl_distance = position['sl_distance_pct']

        # Color based on distance
        if abs(sl_distance) < 1:
            color = "red"
            icon = "🔴"
            alert = "⚠️ **DANGER: Very close to stop-loss!**"
        elif abs(sl_distance) < 2:
            color = "orange"
            icon = "🟡"
            alert = "⚡ **WARNING: Approaching stop-loss**"
        else:
            color = "green"
            icon = "🟢"
            alert = None

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown(f"{icon} **{position['symbol']}**")
            if alert:
                st.warning(alert)

        with col2:
            st.write(f"Current: {format_currency(position['current_price'])}")
            st.write(f"Stop Loss: {format_currency(position['stop_loss'])}")

        with col3:
            st.write(f"Distance: {format_percentage(sl_distance)}")

            # Progress bar
            progress = max(0, min(100, abs(sl_distance) * 20))  # Scale to 0-100
            st.progress(progress / 100)

        st.markdown("---")

else:
    st.info("No positions to monitor")

# Circuit breakers
st.markdown("### 🚨 Circuit Breakers")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style='padding: 1rem; border-radius: 8px; background: #e8f5e9; border-left: 4px solid green;'>
        <h4>✅ Max Daily Loss</h4>
        <p><strong>Limit:</strong> ₹2,500 (5%)</p>
        <p><strong>Current:</strong> ₹450 (18% used)</p>
        <p><strong>Status:</strong> <span style='color: green;'>OK</span></p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style='padding: 1rem; border-radius: 8px; background: #e8f5e9; border-left: 4px solid green;'>
        <h4>✅ Max Positions</h4>
        <p><strong>Limit:</strong> 6 positions</p>
        <p><strong>Current:</strong> 4 positions</p>
        <p><strong>Status:</strong> <span style='color: green;'>OK</span></p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style='padding: 1rem; border-radius: 8px; background: #e8f5e9; border-left: 4px solid green;'>
        <h4>✅ Risk Per Trade</h4>
        <p><strong>Limit:</strong> 1% (₹500)</p>
        <p><strong>Avg:</strong> 0.8% (₹400)</p>
        <p><strong>Status:</strong> <span style='color: green;'>OK</span></p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Risk-Reward distribution
st.markdown("### ⚖️ Risk-Reward Distribution")

if len(positions_df) > 0:
    avg_rr = positions_df['risk_reward'].mean()

    col1, col2 = st.columns([2, 1])

    with col1:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=positions_df['symbol'],
            y=positions_df['risk_reward'],
            marker_color='lightblue',
            text=positions_df['risk_reward'].apply(lambda x: f"{x:.1f}:1"),
            textposition='auto'
        ))

        fig.add_hline(y=1.5, line_dash="dash", line_color="green",
                     annotation_text="Minimum R:R (1.5:1)")

        fig.update_layout(
            title="Risk-Reward Ratio by Position",
            xaxis_title="Symbol",
            yaxis_title="Risk-Reward Ratio",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.metric("Average R:R", f"{avg_rr:.2f}:1")

        if avg_rr >= 2.0:
            st.success("✅ Excellent risk-reward setup")
        elif avg_rr >= 1.5:
            st.info("✅ Good risk-reward setup")
        else:
            st.warning("⚠️ Below recommended minimum")

        st.markdown("---")

        st.markdown("**Recommendations:**")
        st.write("- Minimum R:R: 1.5:1")
        st.write("- Ideal R:R: 2:1 or higher")
        st.write("- Current average: " + f"{avg_rr:.2f}:1")

# Footer
st.markdown("---")
st.caption("⚠️ Risk monitoring and portfolio safety | Real-time updates")
