# Trading System Dashboard

Beautiful, real-time Streamlit dashboard for monitoring your algorithmic trading system.

## 🚀 Quick Start

### Local Development (Without Docker)

```bash
# Install dependencies
pip install -r requirements_dashboard.txt

# Run dashboard
streamlit run src/dashboard/app.py
```

Dashboard will be available at: **http://localhost:8501**

### With Docker

```bash
# Start all services including dashboard
make up

# Or manually
docker-compose up -d dashboard
```

Dashboard will be available at: **http://localhost:8501**

---

## 📊 Pages Overview

### 1. 🏠 Home
- **Portfolio Overview:** Quick stats and KPIs
- **Recent Activity:** Latest trades, signals, and events
- **Quick Actions:** Navigate to key pages

### 2. 📈 Live Trading
- **Real-time Monitoring:** Open positions with live P&L updates
- **Live Price Ticker:** Real-time prices for active positions
- **Position Details:** Entry, current status, stop-loss, targets
- **Live Charts:** Candlestick charts with indicators
- **Latest Signals:** Recent buy/sell signals
- **Auto-refresh:** Every 5 seconds

### 3. 📜 Trade History
- **Complete Trade Log:** All past trades with filtering
- **Performance Metrics:** Win rate, profit factor, avg win/loss
- **P&L Distribution:** Histogram of trade outcomes
- **Win/Loss Breakdown:** Pie chart visualization
- **Symbol Performance:** Best/worst performing stocks
- **Time Analysis:** Performance by hour of day
- **Export to CSV:** Download trade history

### 4. 🧮 Analysis & Signals
- **Interactive Charts:** Candlestick with 6 technical indicators
- **Indicator Toggle:** Show/hide RSI, MACD, Bollinger Bands, EMA, SMA, Volume
- **Multi-Timeframe:** 1m, 5m, 15m, 1h, 1d analysis
- **Current Indicator Values:** Real-time RSI, MACD, BB, ADX, Stochastic, ATR
- **Signal Aggregation:** See how all indicators vote
- **Overall Signal:** Buy/Sell/Hold with confidence score

### 5. ⚠️ Risk Monitoring
- **Risk Gauges:** Portfolio risk and daily loss meters
- **Position Limits:** Monitor position size vs limits
- **Stop-Loss Monitor:** Distance to stop-loss for each position
- **Circuit Breakers:** Daily loss, max positions, risk per trade
- **Risk-Reward Distribution:** R:R ratio for all positions
- **Real-time Alerts:** Visual warnings when approaching limits

### 6. 🔍 System Health *(Coming Soon)*
- Service status monitoring
- Performance metrics (CPU, memory, latency)
- Live logs viewer
- Error dashboard

### 7. ⚙️ Settings *(Coming Soon)*
- Adjust risk parameters
- Modify indicator weights
- Symbol watchlist management
- Notification settings

### 8. 📊 Analytics & Reports *(Coming Soon)*
- Equity curve visualization
- Monthly performance calendar
- Statistical analysis
- Export PDF reports

---

## 🎨 Features

### Real-time Updates
- **Auto-refresh:** Dashboard updates every 5-10 seconds
- **Live prices:** Real-time market data
- **Live P&L:** Instant profit/loss calculations

### Interactive Visualizations
- **Plotly Charts:** Zoomable, interactive candlestick charts
- **Hover Tooltips:** Detailed info on hover
- **Multiple Timeframes:** Switch between 1m to 1d charts
- **Indicator Overlays:** Toggle indicators on/off

### Advanced Tables
- **Sorting:** Click column headers to sort
- **Filtering:** Filter by date, symbol, status
- **Pagination:** Navigate large datasets
- **Export:** Download as CSV

### Risk Management
- **Visual Alerts:** Color-coded warnings
- **Progress Bars:** Distance to stop-loss/target
- **Gauges:** Portfolio risk meters
- **Circuit Breakers:** Auto-stop on limit breach

### Responsive Design
- **Mobile Friendly:** Works on tablets and phones
- **Dark/Light Theme:** Toggle between themes
- **Compact Layout:** Efficient use of screen space

---

## 🛠️ Configuration

### Sidebar Settings

**Auto-refresh:**
- Toggle on/off
- Adjust interval (5-60 seconds)

**Theme:**
- Light mode (default)
- Dark mode

### Quick Stats (Sidebar)
- Portfolio value and change
- Today's P&L
- Open positions count
- System status indicators

---

## 📱 Usage Tips

### Navigation
- Use **sidebar menu** to switch between pages
- Click **Quick Actions** on home for fast navigation
- Use browser **back button** to return

### Charts
- **Zoom:** Click and drag to zoom
- **Pan:** Click pan icon, then drag
- **Reset:** Double-click to reset zoom
- **Toggle Indicators:** Use checkboxes above chart

### Tables
- **Sort:** Click column headers
- **Filter:** Use dropdown filters at top
- **Export:** Click download button for CSV
- **Pagination:** Use page selector for large datasets

### Real-time Monitoring
- Live Trading page auto-refreshes every 5 seconds
- Check "Last updated" timestamp
- Manually refresh with browser refresh (F5)

---

## 🔧 Customization

### Modify Data Source

Edit `src/dashboard/utils/data_loader.py`:

```python
def get_quick_stats():
    # Replace mock data with actual database queries
    # Example: Query TimescaleDB for real portfolio value
    pass
```

### Add New Pages

Create new file: `src/dashboard/pages/X_📄_PageName.py`

```python
import streamlit as st

st.title("My New Page")
st.write("Content here")
```

Streamlit auto-discovers pages in the `pages/` directory!

### Modify Styling

Edit CSS in `src/dashboard/app.py`:

```python
st.markdown("""
<style>
.kpi-card {
    background: your-custom-gradient;
}
</style>
""", unsafe_allow_html=True)
```

---

## 🐛 Troubleshooting

### Dashboard won't start

```bash
# Check if port 8501 is available
lsof -i :8501

# Kill process using port
kill -9 <PID>

# Restart dashboard
streamlit run src/dashboard/app.py
```

### Data not loading

**Check service connections:**

```python
# Test Redis connection
redis-cli ping

# Test TimescaleDB connection
psql -h localhost -U trading -d trading_data
```

**Verify environment variables:**

```bash
echo $REDIS_HOST
echo $TIMESCALE_HOST
```

### Charts not displaying

**Clear Streamlit cache:**

```bash
# Press 'c' in terminal running Streamlit
# Or add to app:
st.cache_data.clear()
```

**Check browser console:**
- Open Developer Tools (F12)
- Look for JavaScript errors
- Try different browser

### Slow performance

**Reduce refresh interval:**
- Increase auto-refresh from 5s to 30s
- Disable auto-refresh when not needed

**Optimize queries:**
- Add indexes to database tables
- Use pagination for large datasets
- Cache expensive calculations

---

## 📊 Data Flow

```
Dashboard (Streamlit)
      ↓
Data Loader Utils
      ↓
   ┌──────┬────────┐
   ↓      ↓        ↓
Redis  TimescaleDB  Kafka
   ↓      ↓        ↓
(Cache) (History) (Events)
```

### Mock Data vs Real Data

**Currently using mock data for:**
- Open positions
- Trade history
- Indicator values

**To use real data:**

1. Ensure services are running:
   ```bash
   docker-compose up -d redis timescaledb
   ```

2. Update `data_loader.py` to query databases

3. Populate database with trades:
   ```bash
   python -m src.integration.trading_pipeline
   ```

---

## 🚦 Status Indicators

### Service Status
- 🟢 **Green:** Running normally
- 🟡 **Yellow:** Warning / degraded
- 🔴 **Red:** Stopped / error

### Market Status
- 🟢 **Market Open:** 9:15 AM - 3:30 PM IST
- 🔴 **Market Closed:** Outside trading hours

### Position Status
- 🟢 **Profit:** Positive P&L
- 🔴 **Loss:** Negative P&L
- 🟡 **Breakeven:** Zero P&L

### Risk Status
- 🟢 **OK:** < 75% of limit
- 🟡 **Warning:** 75-95% of limit
- 🔴 **Danger:** > 95% of limit

---

## 📞 Support

### Documentation
- [Streamlit Docs](https://docs.streamlit.io/)
- [Plotly Docs](https://plotly.com/python/)
- [Main README](../../README.md)

### Common Issues
- **Port already in use:** Change port in docker-compose.yml
- **Connection refused:** Check if services are running
- **No data displayed:** Verify database has data

---

## 🎯 Roadmap

### Completed ✅
- Home page with KPIs
- Live trading monitor
- Trade history with analytics
- Technical analysis with charts
- Risk monitoring dashboard

### In Progress 🚧
- System health monitoring
- Settings configuration
- Analytics & reports

### Planned 📋
- User authentication
- Mobile app (PWA)
- Real-time alerts
- Strategy backtester UI
- News sentiment integration
- Multi-user support

---

## 📄 License

Same as main project (MIT License)

---

## 🙏 Credits

Built with:
- **Streamlit** - Dashboard framework
- **Plotly** - Interactive charts
- **Pandas** - Data manipulation

---

**Happy Trading! 📈**

Access dashboard at: **http://localhost:8501**
