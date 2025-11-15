"""
Trading System Admin Dashboard
Main Streamlit Application

Launch with: streamlit run src/dashboard/app.py
"""

import streamlit as st
from streamlit_autorefresh import st_autorefresh
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils import get_logger

logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Trading System Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/tradingsystem',
        'Report a bug': 'https://github.com/yourusername/tradingsystem/issues',
        'About': '# Algorithmic Trading System\nBuilt with Streamlit, Kafka, Redis, and TimescaleDB'
    }
)

# Custom CSS
def load_custom_css():
    """Load custom CSS styling"""
    st.markdown("""
    <style>
    /* Main container */
    .main {
        padding: 1rem;
    }

    /* KPI Cards */
    .kpi-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .kpi-card-green {
        background: linear-gradient(135deg, #00C853 0%, #00E676 100%);
    }

    .kpi-card-red {
        background: linear-gradient(135deg, #FF1744 0%, #FF5252 100%);
    }

    .kpi-card-blue {
        background: linear-gradient(135deg, #2196F3 0%, #42A5F5 100%);
    }

    .kpi-card-orange {
        background: linear-gradient(135deg, #FF9800 0%, #FFB74D 100%);
    }

    .kpi-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }

    .kpi-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }

    .kpi-change {
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }

    /* Status indicators */
    .status-online {
        color: #00C853;
        font-weight: bold;
    }

    .status-offline {
        color: #FF1744;
        font-weight: bold;
    }

    .status-warning {
        color: #FF9800;
        font-weight: bold;
    }

    /* Profit/Loss colors */
    .profit {
        color: #00C853;
        font-weight: bold;
    }

    .loss {
        color: #FF1744;
        font-weight: bold;
    }

    /* Market status badge */
    .market-open {
        background-color: #00C853;
        color: white;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }

    .market-closed {
        background-color: #FF1744;
        color: white;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }

    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }

    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
    }

    /* Metric cards */
    div[data-testid="metric-container"] {
        background-color: rgba(28, 131, 225, 0.1);
        border-left: 4px solid #1c83e1;
        padding: 1rem;
        border-radius: 8px;
    }

    /* Tables */
    .dataframe {
        font-size: 0.9rem;
    }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Notification badge */
    .notification-badge {
        background-color: #FF1744;
        color: white;
        border-radius: 50%;
        padding: 0.2rem 0.5rem;
        font-size: 0.7rem;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

load_custom_css()

# Sidebar
def render_sidebar():
    """Render sidebar with system info"""
    with st.sidebar:
        # Logo/Title
        st.markdown("# 📊 Trading System")
        st.markdown("---")

        # Quick stats
        try:
            from src.dashboard.utils.data_loader import get_quick_stats
            stats = get_quick_stats()

            st.markdown("### Quick Stats")
            st.metric("Portfolio Value", f"₹{stats.get('portfolio_value', 50000):,.0f}",
                     f"{stats.get('portfolio_change', 0):+.2f}%")
            st.metric("Today's P&L", f"₹{stats.get('daily_pnl', 0):,.0f}",
                     f"{stats.get('daily_pnl_pct', 0):+.2f}%")
            st.metric("Open Positions", stats.get('open_positions', 0))

        except Exception as e:
            st.warning("Could not load quick stats")
            logger.error(f"Sidebar stats error: {e}")

        st.markdown("---")

        # System status
        st.markdown("### System Status")
        try:
            from src.dashboard.utils.data_loader import get_system_status
            status = get_system_status()

            # Market status
            market_status = status.get('market_status', 'CLOSED')
            if market_status == 'OPEN':
                st.markdown('<div class="market-open">🟢 Market Open</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="market-closed">🔴 Market Closed</div>', unsafe_allow_html=True)

            st.markdown("")

            # Services status
            for service, service_status in status.get('services', {}).items():
                emoji = "🟢" if service_status == "running" else "🔴"
                st.text(f"{emoji} {service}")

        except Exception as e:
            st.markdown('<div class="market-closed">⚠️ Unknown</div>', unsafe_allow_html=True)
            logger.error(f"System status error: {e}")

        st.markdown("---")

        # Auto-refresh toggle
        st.markdown("### Settings")
        auto_refresh = st.checkbox("Auto-refresh", value=True)

        if auto_refresh:
            refresh_interval = st.slider("Refresh interval (seconds)", 5, 60, 10)
            st_autorefresh(interval=refresh_interval * 1000, key="dashboard_refresh")

        # Theme toggle
        theme = st.selectbox("Theme", ["Light", "Dark"], index=0)

        st.markdown("---")

        # Footer
        st.markdown("""
        <div style='text-align: center; opacity: 0.7; font-size: 0.8rem;'>
            <p>Trading System v1.0</p>
            <p>Made with ❤️ for Mac M4</p>
        </div>
        """, unsafe_allow_html=True)

render_sidebar()

# Main content
st.title("🏠 Trading System Dashboard")
st.markdown("Welcome to your algorithmic trading system admin panel")

# Top bar with key metrics
col1, col2, col3, col4 = st.columns(4)

try:
    from src.dashboard.utils.data_loader import get_overview_metrics
    metrics = get_overview_metrics()

    with col1:
        st.markdown(f"""
        <div class="kpi-card kpi-card-blue">
            <div class="kpi-label">Portfolio Value</div>
            <div class="kpi-value">₹{metrics.get('portfolio_value', 50000):,.0f}</div>
            <div class="kpi-change">+₹{metrics.get('portfolio_gain', 0):,.0f} ({metrics.get('portfolio_gain_pct', 0):+.1f}%)</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        pnl = metrics.get('daily_pnl', 0)
        card_class = "kpi-card-green" if pnl >= 0 else "kpi-card-red"
        st.markdown(f"""
        <div class="kpi-card {card_class}">
            <div class="kpi-label">Today's P&L</div>
            <div class="kpi-value">₹{pnl:,.0f}</div>
            <div class="kpi-change">{metrics.get('daily_pnl_pct', 0):+.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card kpi-card-orange">
            <div class="kpi-label">Open Positions</div>
            <div class="kpi-value">{metrics.get('open_positions', 0)}</div>
            <div class="kpi-change">Total: {metrics.get('total_trades', 0)} trades</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        win_rate = metrics.get('win_rate', 0)
        card_class = "kpi-card-green" if win_rate >= 60 else "kpi-card-orange"
        st.markdown(f"""
        <div class="kpi-card {card_class}">
            <div class="kpi-label">Win Rate</div>
            <div class="kpi-value">{win_rate:.1f}%</div>
            <div class="kpi-change">{metrics.get('wins', 0)}W / {metrics.get('losses', 0)}L</div>
        </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Could not load metrics: {e}")
    logger.error(f"Metrics error: {e}")

st.markdown("---")

# Quick actions
st.markdown("### 🚀 Quick Actions")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📈 View Live Trading", use_container_width=True):
        st.switch_page("pages/2_📈_Live_Trading.py")

with col2:
    if st.button("📜 Trade History", use_container_width=True):
        st.switch_page("pages/3_📜_Trade_History.py")

with col3:
    if st.button("🧮 Analysis & Signals", use_container_width=True):
        st.switch_page("pages/4_🧮_Analysis.py")

with col4:
    if st.button("⚠️ Risk Monitor", use_container_width=True):
        st.switch_page("pages/5_⚠️_Risk_Monitor.py")

st.markdown("---")

# Recent activity
st.markdown("### 📊 Recent Activity")

tab1, tab2, tab3 = st.tabs(["Recent Trades", "Latest Signals", "System Events"])

with tab1:
    try:
        from src.dashboard.utils.data_loader import get_recent_trades
        trades = get_recent_trades(limit=5)

        if len(trades) > 0:
            st.dataframe(
                trades,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "pnl": st.column_config.NumberColumn(
                        "P&L",
                        format="₹%.2f"
                    ),
                    "pnl_pct": st.column_config.NumberColumn(
                        "P&L %",
                        format="%.2f%%"
                    )
                }
            )
        else:
            st.info("No recent trades")
    except Exception as e:
        st.error(f"Could not load recent trades: {e}")

with tab2:
    try:
        from src.dashboard.utils.data_loader import get_recent_signals
        signals = get_recent_signals(limit=5)

        if len(signals) > 0:
            st.dataframe(signals, use_container_width=True, hide_index=True)
        else:
            st.info("No recent signals")
    except Exception as e:
        st.error(f"Could not load signals: {e}")

with tab3:
    try:
        from src.dashboard.utils.data_loader import get_recent_events
        events = get_recent_events(limit=10)

        if len(events) > 0:
            for event in events:
                timestamp = event.get('timestamp', '')
                level = event.get('level', 'INFO')
                message = event.get('message', '')

                if level == 'ERROR':
                    st.error(f"🔴 {timestamp} - {message}")
                elif level == 'WARNING':
                    st.warning(f"🟡 {timestamp} - {message}")
                else:
                    st.info(f"🔵 {timestamp} - {message}")
        else:
            st.info("No recent events")
    except Exception as e:
        st.warning(f"Could not load events: {e}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; opacity: 0.6; padding: 2rem 0;'>
    <p>Trading System Dashboard | Built with Streamlit</p>
    <p>⚠️ Paper Trading Mode Active - No real money at risk</p>
</div>
""", unsafe_allow_html=True)
