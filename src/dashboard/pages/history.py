"""
Trade History Page
Analyze all past trades with filtering and statistics
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.dashboard.utils.data_loader import get_all_trades, get_performance_stats
from src.dashboard.utils.formatters import format_currency, format_percentage

st.title("📜 Trade History")
st.markdown("Complete history of all trades with performance analytics")

# Filters
st.markdown("### 🔍 Filters")
col1, col2, col3, col4 = st.columns(4)

with col1:
    date_range = st.selectbox("Date Range", ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time", "Custom"])

with col2:
    symbols = ['All', 'RELIANCE.NS', 'TCS.NS', 'HDFC.NS', 'INFY.NS', 'ICICIBANK.NS']
    selected_symbol = st.selectbox("Symbol", symbols)

with col3:
    trade_type = st.selectbox("Type", ["All", "BUY", "SELL"])

with col4:
    status = st.selectbox("Status", ["All", "Profit", "Loss", "Breakeven"])

# Calculate date range
if date_range == "Last 7 Days":
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()
elif date_range == "Last 30 Days":
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
elif date_range == "Last 90 Days":
    start_date = datetime.now() - timedelta(days=90)
    end_date = datetime.now()
elif date_range == "Custom":
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date")
    with col2:
        end_date = st.date_input("End Date")
else:
    start_date = None
    end_date = None

st.markdown("---")

# Performance metrics
st.markdown("### 📊 Performance Metrics")

stats = get_performance_stats()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Trades", stats.get('total_trades', 0))

with col2:
    win_rate = stats.get('win_rate', 0)
    st.metric("Win Rate", f"{win_rate:.1f}%",
             f"{stats.get('winning_trades', 0)}W/{stats.get('losing_trades', 0)}L")

with col3:
    st.metric("Avg Win", format_currency(stats.get('avg_win', 0)))

with col4:
    st.metric("Avg Loss", format_currency(stats.get('avg_loss', 0)))

with col5:
    st.metric("Profit Factor", f"{stats.get('profit_factor', 0):.2f}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_pnl = stats.get('total_pnl', 0)
    st.metric("Total P&L", format_currency(total_pnl),
             format_percentage(stats.get('total_pnl_pct', 0)))

with col2:
    st.metric("Largest Win", format_currency(stats.get('largest_win', 0)))

with col3:
    st.metric("Largest Loss", format_currency(stats.get('largest_loss', 0)))

with col4:
    st.metric("Avg Hold Time", stats.get('avg_hold_time', '0h'))

st.markdown("---")

# Trades table
st.markdown("### 📋 All Trades")

# Get trades data
trades_df = get_all_trades(start_date=start_date, end_date=end_date,
                           symbol=selected_symbol, status=status)

if len(trades_df) > 0:
    # Add color coding for P&L
    def color_pnl_row(row):
        if row['pnl'] > 0:
            return ['background-color: #e8f5e9'] * len(row)
        elif row['pnl'] < 0:
            return ['background-color: #ffebee'] * len(row)
        else:
            return [''] * len(row)

    # Display with pagination
    rows_per_page = st.selectbox("Rows per page", [10, 25, 50, 100], index=1)

    # Calculate pages
    total_rows = len(trades_df)
    total_pages = (total_rows + rows_per_page - 1) // rows_per_page

    page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)

    # Get page data
    start_idx = (page - 1) * rows_per_page
    end_idx = min(start_idx + rows_per_page, total_rows)
    page_df = trades_df.iloc[start_idx:end_idx]

    st.dataframe(
        page_df,
        use_container_width=True,
        hide_index=True
    )

    st.caption(f"Showing {start_idx + 1}-{end_idx} of {total_rows} trades")

    # Export button
    csv = trades_df.to_csv(index=False)
    st.download_button(
        label="📥 Download as CSV",
        data=csv,
        file_name=f"trades_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

else:
    st.info("No trades found with the selected filters")

st.markdown("---")

# Charts
st.markdown("### 📈 Trade Analytics")

if len(trades_df) > 0:
    tab1, tab2, tab3, tab4 = st.tabs(["P&L Distribution", "Win/Loss Breakdown", "Symbol Performance", "Time Analysis"])

    with tab1:
        # P&L histogram
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=trades_df['pnl'],
            nbinsx=20,
            name='P&L Distribution',
            marker_color='lightblue'
        ))
        fig.update_layout(
            title="P&L Distribution",
            xaxis_title="P&L (₹)",
            yaxis_title="Number of Trades",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        # Summary stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Mean P&L", format_currency(trades_df['pnl'].mean()))
        with col2:
            st.metric("Median P&L", format_currency(trades_df['pnl'].median()))
        with col3:
            st.metric("Std Dev", format_currency(trades_df['pnl'].std()))

    with tab2:
        # Win/Loss pie chart
        wins = len(trades_df[trades_df['pnl'] > 0])
        losses = len(trades_df[trades_df['pnl'] < 0])
        breakeven = len(trades_df[trades_df['pnl'] == 0])

        fig = go.Figure(data=[go.Pie(
            labels=['Wins', 'Losses', 'Breakeven'],
            values=[wins, losses, breakeven],
            marker_colors=['#00C853', '#FF1744', '#9E9E9E'],
            hole=0.4
        )])
        fig.update_layout(
            title="Win/Loss Distribution",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Wins", wins, f"{(wins/len(trades_df)*100):.1f}%")
        with col2:
            st.metric("Losses", losses, f"{(losses/len(trades_df)*100):.1f}%")
        with col3:
            st.metric("Breakeven", breakeven, f"{(breakeven/len(trades_df)*100):.1f}%")

    with tab3:
        # Group by symbol
        symbol_pnl = trades_df.groupby('symbol')['pnl'].agg(['sum', 'count', 'mean']).reset_index()
        symbol_pnl.columns = ['Symbol', 'Total P&L', 'Trades', 'Avg P&L']
        symbol_pnl = symbol_pnl.sort_values('Total P&L', ascending=False)

        # Bar chart
        fig = go.Figure()
        colors = ['green' if x > 0 else 'red' for x in symbol_pnl['Total P&L']]
        fig.add_trace(go.Bar(
            x=symbol_pnl['Symbol'],
            y=symbol_pnl['Total P&L'],
            marker_color=colors,
            name='Total P&L'
        ))
        fig.update_layout(
            title="P&L by Symbol",
            xaxis_title="Symbol",
            yaxis_title="Total P&L (₹)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        # Table
        st.dataframe(symbol_pnl, use_container_width=True, hide_index=True)

    with tab4:
        # Parse timestamps
        trades_df['hour'] = pd.to_datetime(trades_df['timestamp']).dt.hour

        # Group by hour
        hourly_pnl = trades_df.groupby('hour')['pnl'].agg(['sum', 'count', 'mean']).reset_index()
        hourly_pnl.columns = ['Hour', 'Total P&L', 'Trades', 'Avg P&L']

        # Line chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hourly_pnl['Hour'],
            y=hourly_pnl['Total P&L'],
            mode='lines+markers',
            name='Total P&L',
            line=dict(color='blue', width=2)
        ))
        fig.update_layout(
            title="P&L by Hour of Day",
            xaxis_title="Hour",
            yaxis_title="Total P&L (₹)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        # Best/worst hours
        best_hour = hourly_pnl.loc[hourly_pnl['Total P&L'].idxmax()]
        worst_hour = hourly_pnl.loc[hourly_pnl['Total P&L'].idxmin()]

        col1, col2 = st.columns(2)
        with col1:
            st.success(f"**Best Hour:** {int(best_hour['Hour'])}:00 - {format_currency(best_hour['Total P&L'])} ({int(best_hour['Trades'])} trades)")
        with col2:
            st.error(f"**Worst Hour:** {int(worst_hour['Hour'])}:00 - {format_currency(worst_hour['Total P&L'])} ({int(worst_hour['Trades'])} trades)")

# Footer
st.markdown("---")
st.caption("📊 Trade history and performance analytics")
