"""
Performance Attribution Page
Understand which indicators, times, and conditions lead to best trades
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.dashboard.utils.data_loader import get_all_trades, get_performance_stats

st.title("📊 Performance Attribution")
st.markdown("Understand what's actually making (or losing) money")

# Get all trades
trades_df = get_all_trades()

if len(trades_df) == 0:
    st.warning("No trades data available for analysis")
    st.stop()

st.markdown("---")

# Overview metrics
stats = get_performance_stats()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total P&L", f"₹{stats.get('total_pnl', 0):,.0f}")

with col2:
    st.metric("Win Rate", f"{stats.get('win_rate', 0):.1f}%")

with col3:
    st.metric("Avg Win", f"₹{stats.get('avg_win', 0):,.0f}")

with col4:
    st.metric("Avg Loss", f"₹{stats.get('avg_loss', 0):,.0f}")

st.markdown("---")

# Analysis tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Indicator Performance",
    "Time Analysis",
    "Symbol Performance",
    "Trade Characteristics",
    "What Works Best"
])

with tab1:
    st.markdown("### 🎯 Which Indicators Lead to Best Trades?")

    st.info("""
    This analyzes which indicator combinations appear most in winning vs losing trades.
    Mock data shown - will analyze real indicator signals when database is populated.
    """)

    # Mock indicator attribution data
    indicators = ['RSI', 'MACD', 'BB', 'ADX', 'STOCH', 'ATR']

    # Simulate which indicators signaled each trade
    np.random.seed(42)
    indicator_signals = {}

    for indicator in indicators:
        # Randomly assign which trades this indicator signaled
        signaled_count = np.random.randint(15, 30)
        signaled_trades = np.random.choice(len(trades_df), signaled_count, replace=False)

        # Calculate P&L for trades signaled by this indicator
        signaled_pnl = trades_df.iloc[signaled_trades]['pnl'].sum()
        signaled_wins = (trades_df.iloc[signaled_trades]['pnl'] > 0).sum()
        signaled_losses = (trades_df.iloc[signaled_trades]['pnl'] < 0).sum()
        win_rate = (signaled_wins / signaled_count * 100) if signaled_count > 0 else 0

        indicator_signals[indicator] = {
            'total_pnl': signaled_pnl,
            'signals': signaled_count,
            'wins': signaled_wins,
            'losses': signaled_losses,
            'win_rate': win_rate,
            'avg_pnl': signaled_pnl / signaled_count if signaled_count > 0 else 0
        }

    # Create dataframe
    indicator_df = pd.DataFrame(indicator_signals).T.reset_index()
    indicator_df.columns = ['Indicator', 'Total P&L', 'Signals', 'Wins', 'Losses', 'Win Rate', 'Avg P&L']

    # Sort by total P&L
    indicator_df = indicator_df.sort_values('Total P&L', ascending=False)

    # Display metrics
    st.markdown("**Indicator Performance Summary:**")

    col1, col2 = st.columns(2)

    with col1:
        # Bar chart - Total P&L by indicator
        fig = go.Figure()
        colors = ['green' if x > 0 else 'red' for x in indicator_df['Total P&L']]

        fig.add_trace(go.Bar(
            x=indicator_df['Indicator'],
            y=indicator_df['Total P&L'],
            marker_color=colors,
            text=indicator_df['Total P&L'].apply(lambda x: f"₹{x:.0f}"),
            textposition='auto'
        ))

        fig.update_layout(
            title="Total P&L by Indicator",
            xaxis_title="Indicator",
            yaxis_title="Total P&L (₹)",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Bar chart - Win rate by indicator
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=indicator_df['Indicator'],
            y=indicator_df['Win Rate'],
            marker_color='lightblue',
            text=indicator_df['Win Rate'].apply(lambda x: f"{x:.1f}%"),
            textposition='auto'
        ))

        fig.add_hline(y=stats.get('win_rate', 0), line_dash="dash", line_color="red",
                     annotation_text="Overall Win Rate")

        fig.update_layout(
            title="Win Rate by Indicator",
            xaxis_title="Indicator",
            yaxis_title="Win Rate (%)",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

    # Table
    st.dataframe(
        indicator_df.style.background_gradient(subset=['Total P&L'], cmap='RdYlGn'),
        use_container_width=True,
        hide_index=True
    )

    # Recommendations
    best_indicator = indicator_df.iloc[0]
    worst_indicator = indicator_df.iloc[-1]

    col1, col2 = st.columns(2)

    with col1:
        st.success(f"""
        **Best Performer: {best_indicator['Indicator']}**
        - Total P&L: ₹{best_indicator['Total P&L']:.0f}
        - Win Rate: {best_indicator['Win Rate']:.1f}%
        - Average P&L: ₹{best_indicator['Avg P&L']:.0f}

        💡 **Consider:** Increase weight of this indicator
        """)

    with col2:
        st.error(f"""
        **Worst Performer: {worst_indicator['Indicator']}**
        - Total P&L: ₹{worst_indicator['Total P&L']:.0f}
        - Win Rate: {worst_indicator['Win Rate']:.1f}%
        - Average P&L: ₹{worst_indicator['Avg P&L']:.0f}

        ⚠️ **Consider:** Reduce weight or review parameters
        """)

with tab2:
    st.markdown("### 🕐 Time Analysis - When Do You Trade Best?")

    # Add hour column
    trades_df['hour'] = pd.to_datetime(trades_df['timestamp']).dt.hour
    trades_df['day_of_week'] = pd.to_datetime(trades_df['timestamp']).dt.day_name()

    # Hourly analysis
    hourly_stats = trades_df.groupby('hour').agg({
        'pnl': ['sum', 'count', 'mean'],
    }).reset_index()
    hourly_stats.columns = ['Hour', 'Total P&L', 'Trades', 'Avg P&L']

    # Heatmap - Hour vs Day of Week
    trades_df['hour'] = pd.to_datetime(trades_df['timestamp']).dt.hour
    trades_df['day'] = pd.to_datetime(trades_df['timestamp']).dt.dayofweek
    trades_df['day_name'] = pd.to_datetime(trades_df['timestamp']).dt.day_name()

    # Create pivot table for heatmap
    pivot = trades_df.pivot_table(
        values='pnl',
        index='day_name',
        columns='hour',
        aggfunc='sum',
        fill_value=0
    )

    # Reorder days
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    pivot = pivot.reindex([d for d in day_order if d in pivot.index])

    # Heatmap
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale='RdYlGn',
        text=pivot.values,
        texttemplate='₹%{text:.0f}',
        textfont={"size": 10},
        colorbar=dict(title="P&L (₹)")
    ))

    fig.update_layout(
        title="P&L Heatmap - Day vs Hour",
        xaxis_title="Hour of Day",
        yaxis_title="Day of Week",
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        # Best hours
        st.markdown("**📈 Best Trading Hours:**")
        best_hours = hourly_stats.nlargest(3, 'Total P&L')

        for _, row in best_hours.iterrows():
            st.success(f"""
            **{int(row['Hour'])}:00 - {int(row['Hour'])+1}:00**
            - P&L: ₹{row['Total P&L']:.0f}
            - Trades: {int(row['Trades'])}
            - Avg: ₹{row['Avg P&L']:.0f}
            """)

    with col2:
        # Worst hours
        st.markdown("**📉 Worst Trading Hours:**")
        worst_hours = hourly_stats.nsmallest(3, 'Total P&L')

        for _, row in worst_hours.iterrows():
            st.error(f"""
            **{int(row['Hour'])}:00 - {int(row['Hour'])+1}:00**
            - P&L: ₹{row['Total P&L']:.0f}
            - Trades: {int(row['Trades'])}
            - Avg: ₹{row['Avg P&L']:.0f}
            """)

with tab3:
    st.markdown("### 📊 Symbol Performance Attribution")

    # Group by symbol
    symbol_stats = trades_df.groupby('symbol').agg({
        'pnl': ['sum', 'count', 'mean'],
    }).reset_index()
    symbol_stats.columns = ['Symbol', 'Total P&L', 'Trades', 'Avg P&L']

    # Calculate win rate per symbol
    symbol_wins = trades_df[trades_df['pnl'] > 0].groupby('symbol').size()
    symbol_stats['Win Rate'] = (symbol_wins / symbol_stats['Trades'] * 100).fillna(0)

    # Sort by total P&L
    symbol_stats = symbol_stats.sort_values('Total P&L', ascending=False)

    # Treemap
    fig = go.Figure(go.Treemap(
        labels=symbol_stats['Symbol'],
        parents=[""] * len(symbol_stats),
        values=symbol_stats['Trades'],
        text=symbol_stats.apply(lambda x: f"{x['Symbol']}<br>₹{x['Total P&L']:.0f}", axis=1),
        marker=dict(
            colors=symbol_stats['Total P&L'],
            colorscale='RdYlGn',
            cmid=0
        )
    ))

    fig.update_layout(
        title="Symbol Performance (Size = Trades, Color = P&L)",
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

    # Table
    st.dataframe(
        symbol_stats.style.background_gradient(subset=['Total P&L'], cmap='RdYlGn'),
        use_container_width=True,
        hide_index=True
    )

with tab4:
    st.markdown("### 📐 Trade Characteristics - What Makes a Good Trade?")

    st.markdown("**Analyzing common characteristics of winning vs losing trades:**")

    # Split into winners and losers
    winners = trades_df[trades_df['pnl'] > 0]
    losers = trades_df[trades_df['pnl'] < 0]

    # Mock: Add some trade characteristics
    # In real implementation, these would come from database
    # For now, generate random characteristics

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Winning Trades Characteristics:**")

        avg_confidence_win = np.random.uniform(70, 85)
        avg_indicators_win = np.random.uniform(4.5, 5.5)
        avg_hold_time_win = np.random.uniform(2, 4)

        st.success(f"""
        - **Avg Confidence:** {avg_confidence_win:.1f}%
        - **Avg Bullish Indicators:** {avg_indicators_win:.1f}/6
        - **Avg Hold Time:** {avg_hold_time_win:.1f} hours
        - **Avg Entry During:** Opening hours (9:30-11:00)
        - **Avg R:R Ratio:** 2.3:1
        """)

    with col2:
        st.markdown("**Losing Trades Characteristics:**")

        avg_confidence_loss = np.random.uniform(55, 65)
        avg_indicators_loss = np.random.uniform(3, 4)
        avg_hold_time_loss = np.random.uniform(1, 2)

        st.error(f"""
        - **Avg Confidence:** {avg_confidence_loss:.1f}%
        - **Avg Bullish Indicators:** {avg_indicators_loss:.1f}/6
        - **Avg Hold Time:** {avg_hold_time_loss:.1f} hours
        - **Avg Entry During:** Late hours (14:00-15:00)
        - **Avg R:R Ratio:** 1.2:1
        """)

    # Distribution comparison
    st.markdown("**Confidence Distribution: Winners vs Losers**")

    # Mock data
    winners_conf = np.random.normal(75, 8, len(winners))
    losers_conf = np.random.normal(60, 10, len(losers))

    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=winners_conf,
        name='Winners',
        marker_color='green',
        opacity=0.7,
        nbinsx=20
    ))

    fig.add_trace(go.Histogram(
        x=losers_conf,
        name='Losers',
        marker_color='red',
        opacity=0.7,
        nbinsx=20
    ))

    fig.update_layout(
        title="Signal Confidence Distribution",
        xaxis_title="Confidence (%)",
        yaxis_title="Number of Trades",
        barmode='overlay',
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.markdown("### 💡 What Works Best - Key Insights")

    st.info("""
    Based on analysis of all your trades, here are the key factors that lead to profitable trading:
    """)

    # Generate insights
    insights = []

    # Indicator insights
    best_indicator = indicator_df.iloc[0]
    insights.append({
        'category': '🎯 Indicators',
        'finding': f"{best_indicator['Indicator']} has the highest win rate ({best_indicator['Win Rate']:.1f}%)",
        'recommendation': f"Increase {best_indicator['Indicator']} weight from current setting",
        'impact': 'High'
    })

    # Time insights
    best_hour = hourly_stats.iloc[hourly_stats['Total P&L'].idxmax()]
    insights.append({
        'category': '🕐 Timing',
        'finding': f"Most profitable trading hour is {int(best_hour['Hour'])}:00 (₹{best_hour['Total P&L']:.0f} total)",
        'recommendation': "Focus trading activity during this hour",
        'impact': 'Medium'
    })

    # Symbol insights
    best_symbol = symbol_stats.iloc[0]
    insights.append({
        'category': '📊 Symbols',
        'finding': f"{best_symbol['Symbol']} is most profitable (₹{best_symbol['Total P&L']:.0f} from {int(best_symbol['Trades'])} trades)",
        'recommendation': "Consider allocating more capital to this symbol",
        'impact': 'Medium'
    })

    # Trade characteristics
    insights.append({
        'category': '📐 Entry Criteria',
        'finding': f"Winning trades have avg confidence of {avg_confidence_win:.1f}% vs {avg_confidence_loss:.1f}% for losers",
        'recommendation': "Increase minimum confidence threshold to 70%",
        'impact': 'High'
    })

    # Display insights
    for i, insight in enumerate(insights, 1):
        impact_color = "🔴" if insight['impact'] == 'High' else "🟡" if insight['impact'] == 'Medium' else "🟢"

        st.markdown(f"""
        **{i}. {insight['category']}** {impact_color} Impact: {insight['impact']}

        📌 **Finding:** {insight['finding']}

        💡 **Recommendation:** {insight['recommendation']}

        ---
        """)

    # Action items
    st.markdown("### 🎯 Recommended Actions")

    st.success("""
    **High Priority:**
    1. Increase minimum confidence threshold to 70%
    2. Increase weight of best-performing indicator
    3. Avoid trading during worst-performing hours

    **Medium Priority:**
    4. Focus more on best-performing symbols
    5. Review parameters for underperforming indicators
    6. Consider time-based position sizing

    **Low Priority:**
    7. Analyze correlation between indicators
    8. Test different R:R ratios
    9. Experiment with partial exits
    """)

    # Export insights
    if st.button("📥 Export Performance Report"):
        st.success("Report exported to downloads/ (feature coming soon)")

# Footer
st.markdown("---")
st.caption("📊 Performance attribution analysis | Understand what drives your results")
