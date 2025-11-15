# NON-AI TRADING SYSTEM - COMPLETE ARCHITECTURE
## Indian Stock Market | Paper Trading Focus | Rule-Based System

---

## SYSTEM OVERVIEW

**System Type:** Rule-Based Algorithmic Trading System  
**Market:** Indian Stocks (NSE/BSE)  
**Mode:** Paper Trading (Simulated)  
**Execution Frequency:** End-of-Day (EOD)  
**Capital:** ₹1,00,000 (configurable)  
**Technology Stack:** Python-based, SQLite database, Free APIs

---

## PHASE 1: FOUNDATION LAYER (Week 1-2)

### 1.1 DATA ACQUISITION MODULE

**Purpose:** Fetch reliable Indian stock market data

**Components:**

**A. Data Source Manager**
- Primary Source: Yahoo Finance India (yfinance library)
- Secondary Source: NSEpy library
- Tertiary Source: Alpha Vantage (free tier)
- Fallback mechanism when primary fails

**B. Stock Universe Definition**
- Start with Nifty 50 stocks
- Expandable to Nifty 100, Nifty 500
- Sector-wise grouping (IT, Banking, Pharma, Auto, FMCG, etc.)
- Configurable watchlist

**C. Data Types to Collect**
- Historical OHLCV (Open, High, Low, Close, Volume)
- Corporate actions (splits, bonuses, dividends)
- Current market price
- 52-week high/low
- Market cap and basic fundamentals

**D. Data Storage Structure**
- Historical data: Parquet files or SQLite tables
- Naming convention: SYMBOL_YYYYMMDD.parquet
- Minimum 2 years of daily data for each stock
- Update mechanism: Daily after market close (3:30 PM IST)

**E. Data Quality Checks**
- Missing data detection
- Outlier detection (prices, volumes)
- Forward-fill for missing values
- Validation against known events (market holidays)

**Free API Details:**
- **yfinance:** Unlimited calls, add .NS suffix (RELIANCE.NS)
- **nsepy:** Direct NSE data, no authentication needed
- **Alpha Vantage:** 5 calls/min, 500 calls/day (backup only)

**Paid Backup Options (for future):**
- Upstox API: ₹2000/month
- Zerodha Kite Connect: ₹2000/month
- Fyers API: ₹1500/month

**Deliverables:**
- Data fetcher script with fallback mechanism
- Data validation module
- Automated daily data updater
- Data health check report

---

### 1.2 DATABASE ARCHITECTURE

**Purpose:** Store all trading data, portfolio state, and performance metrics

**Database Choice:** SQLite (file-based, no server needed)

**Table Structures:**

**A. Holdings Table**
- Tracks current positions
- Fields: symbol, quantity, average_buy_price, invested_amount, current_price, current_value, unrealized_pnl, unrealized_pnl_percent, sector, last_updated
- Primary key: symbol
- Updated: After every trade and EOD

**B. Trades Table**
- Complete trade history
- Fields: trade_id (auto-increment), timestamp, symbol, action (BUY/SELL), quantity, price, gross_amount, brokerage, taxes, net_amount, reason/strategy_name, pnl_realized (for sells), trade_type (ENTRY/EXIT/PARTIAL)
- Records both entry and exit
- Never delete records (audit trail)

**C. Daily Portfolio Snapshot**
- Daily portfolio performance
- Fields: date, total_invested, total_current_value, total_unrealized_pnl, total_unrealized_pnl_percent, realized_pnl_today, cash_balance, total_capital, number_of_holdings, number_of_sectors
- One record per day
- Used for performance charts

**D. Signals Table**
- Trading signals generated (executed or not)
- Fields: signal_id, date, time, symbol, signal_type (BUY/SELL/HOLD), entry_price, stop_loss, target_price, confidence_score, strategy_name, reasoning, executed (boolean), rejection_reason
- Helps analyze missed opportunities
- Review which signals were profitable

**E. Strategy Performance Table**
- Track each strategy's performance
- Fields: strategy_name, total_trades, winning_trades, losing_trades, win_rate, total_pnl, average_win, average_loss, risk_reward_ratio, max_drawdown, sharpe_ratio, last_updated
- Updated after each trade completion

**F. Risk Metrics Table**
- Daily risk tracking
- Fields: date, max_portfolio_risk, current_portfolio_risk, largest_position_percent, sector_concentrations (JSON), correlation_risk_score, var_95, drawdown_from_peak
- Prevents over-exposure

**G. Market Data Cache**
- Recent OHLCV data for quick access
- Fields: symbol, date, open, high, low, close, volume, adjusted_close
- Keep last 500 days per symbol
- Faster than reading parquet files repeatedly

**Deliverables:**
- Database schema SQL file
- Database initialization script
- Data migration script (if schema changes)
- Database backup mechanism

---

## PHASE 2: STRATEGY LAYER (Week 3-5)

### 2.1 TECHNICAL INDICATOR ENGINE

**Purpose:** Calculate all technical indicators needed for strategies

**Component Structure:**

**A. Trend Indicators**
- Moving Averages: SMA (20, 50, 200), EMA (9, 21, 50, 200)
- MACD (12, 26, 9): Line, Signal, Histogram
- ADX (14): Trend strength
- Ichimoku Cloud: Tenkan, Kijun, Senkou Span A/B, Chikou
- Parabolic SAR
- Supertrend

**B. Momentum Indicators**
- RSI (14): Relative Strength Index
- Stochastic Oscillator (14, 3, 3)
- CCI (Commodity Channel Index)
- ROC (Rate of Change)
- Williams %R

**C. Volatility Indicators**
- Bollinger Bands (20, 2): Upper, Middle, Lower
- ATR (Average True Range - 14)
- Keltner Channels
- Standard Deviation
- Volatility Percentile (comparing recent to historical)

**D. Volume Indicators**
- Volume Moving Average (20, 50 days)
- OBV (On-Balance Volume)
- Volume Price Trend
- Accumulation/Distribution Line
- Volume Rate of Change

**E. Support/Resistance Levels**
- Pivot Points (Standard, Fibonacci, Camarilla)
- 52-week High/Low
- Fibonacci Retracement levels
- Recent swing highs/lows (20-day, 50-day)

**Technical Requirements:**
- Calculate indicators only once per day (EOD)
- Store calculated values in database
- Vectorized calculations (using pandas/numpy)
- Handle missing data gracefully
- Library: TA-Lib or pandas-ta

**Deliverables:**
- Indicator calculation module
- Indicator validation tests
- Performance benchmarks (calculation speed)
- Indicator library documentation

---

### 2.2 STRATEGY MODULES

**Purpose:** Define trading logic and generate signals

**Recommended Strategies (Start with 2, expand to 4-5):**

**STRATEGY 1: TREND FOLLOWING + RSI CONFIRMATION**

**Logic:**
- Identify uptrend: Price above 50 EMA AND 50 EMA above 200 EMA
- Wait for pullback: RSI drops below 40 (oversold in uptrend)
- Entry trigger: RSI crosses back above 40 + Volume > 20-day average
- Additional filter: ADX > 25 (strong trend)

**Exit Rules:**
- Stop Loss: 2% below entry OR below recent swing low
- Target 1 (50% position): +5% gain
- Target 2 (remaining 50%): Trailing stop at 50 EMA
- Force exit: Price closes below 50 EMA

**Risk-Reward:** Minimum 2:1 (Target 5%, Stop 2.5%)

**Best For:** Trending markets, large-cap stocks

---

**STRATEGY 2: MEAN REVERSION (BOLLINGER BANDS)**

**Logic:**
- Identify range-bound market: ADX < 25
- Wait for extreme: Price touches or breaks below Lower Bollinger Band
- Entry confirmation: RSI < 30 (oversold)
- Volume confirmation: Above average (panic selling)

**Exit Rules:**
- Target 1: Middle Bollinger Band (50% position)
- Target 2: Upper Bollinger Band (remaining 50%)
- Stop Loss: 3% below entry OR below recent support
- Time-based exit: Exit if no profit in 10 trading days

**Risk-Reward:** Minimum 1.5:1

**Best For:** Range-bound markets, mid-cap stocks

---

**STRATEGY 3: BREAKOUT WITH VOLUME**

**Logic:**
- Identify consolidation: Price in narrow range for 10+ days (Bollinger Band squeeze)
- Entry trigger: Price breaks above recent high with volume > 2x average
- Confirmation: Close above breakout level
- Additional filter: RSI between 50-70 (not overbought)

**Exit Rules:**
- Stop Loss: Just below consolidation range (typically 3-4%)
- Target 1: Height of consolidation range (50% position)
- Target 2: 1.5x consolidation height (remaining 50%)
- Trailing stop: Move to breakeven after +3%

**Risk-Reward:** Minimum 2:1

**Best For:** High-beta stocks, volatile stocks

---

**STRATEGY 4: MOMENTUM SWING (OPTIONAL)**

**Logic:**
- Identify strong momentum: Stock up 5%+ in single day on high volume
- Entry: Next day if opens strong and holds above previous close
- Confirmation: RSI > 60, MACD bullish crossover

**Exit Rules:**
- Stop Loss: Previous day's low (typically 4-5%)
- Target: +10-15% (aggressive)
- Trailing stop: Once up 5%, trail at -3% from highest price
- Time-based: Maximum hold 5 days

**Risk-Reward:** Minimum 2:1

**Best For:** Small-cap/mid-cap, momentum traders

---

**Strategy Component Structure:**

Each strategy module must have:

**A. Signal Generator**
- Takes OHLCV data + indicators as input
- Returns: BUY/SELL/HOLD signal with confidence score (0-1)
- Includes reasoning (which conditions met)

**B. Entry Logic**
- Specific entry trigger conditions
- Entry price logic (market order, limit order)
- Position sizing recommendation
- Stop loss calculation
- Target price calculation

**C. Exit Logic**
- Stop loss triggers
- Take profit triggers
- Trailing stop logic
- Time-based exits
- Fundamental deterioration exits

**D. Market Condition Filter**
- Market regime detector (trending/ranging/volatile)
- Disable strategy in unfavorable conditions
- Example: Don't trade mean reversion in strong trends

**E. Configuration Parameters**
- All thresholds as configurable variables
- Easy backtesting with different parameters
- Parameter ranges for optimization

**Deliverables:**
- 2-4 coded strategy modules
- Strategy flowcharts/diagrams
- Strategy configuration files
- Strategy performance metrics

---

### 2.3 SIGNAL AGGREGATOR

**Purpose:** Combine signals from multiple strategies and prioritize

**Components:**

**A. Signal Collector**
- Run all active strategies on all watchlist stocks
- Collect all BUY/SELL signals
- Timestamp each signal
- Store in signals database table

**B. Signal Scoring System**
- Confidence score (from strategy): 0-1
- Strategy historical performance weight
- Technical setup quality score
- Risk-reward ratio score
- Composite score = weighted average

**C. Signal Prioritization**
- Rank signals by composite score
- Consider available capital
- Consider existing positions (don't add to losing positions)
- Consider sector exposure limits
- Filter out low-quality signals (score < threshold)

**D. Conflict Resolution**
- Multiple strategies signal same stock: Take highest confidence
- Conflicting signals (BUY vs SELL): Favor SELL (protect capital)
- Signal vs existing position conflict: Review position, may exit

**E. Signal Validation**
- Check if stock is tradeable (not suspended, not in ban list)
- Verify sufficient liquidity (average volume > threshold)
- Check circuit limits (not upper/lower circuit)
- Verify data quality (no missing/stale data)

**Output:**
- Ranked list of actionable signals
- Top 5-10 signals for the day
- Reasoning for each signal

**Deliverables:**
- Signal aggregation module
- Signal ranking algorithm
- Signal validation checks
- Daily signal report generator

---

## PHASE 3: RISK MANAGEMENT LAYER (Week 5-6)

### 3.1 POSITION SIZING ENGINE

**Purpose:** Calculate optimal position size for each trade

**Components:**

**A. Fixed Percentage Risk Model**
- Risk per trade: 1% of total capital (configurable 0.5-2%)
- Formula: Position Size = (Account Risk Amount) / (Entry Price - Stop Loss)
- Example: Capital ₹1,00,000, Risk 1% = ₹1,000
  - Entry: ₹500, Stop Loss: ₹490, Risk per share: ₹10
  - Position size: ₹1,000 / ₹10 = 100 shares

**B. Maximum Position Size Caps**
- No single position > 20% of total capital
- Adjust quantity if calculated size exceeds cap
- Prevents over-concentration

**C. Volatility-Adjusted Sizing**
- Reduce position size for high-volatility stocks
- Use ATR (Average True Range) as volatility measure
- Formula: Base Size * (Average ATR / Current ATR)
- Higher volatility = smaller position

**D. Sector Exposure Limits**
- Maximum 30% capital in single sector
- Check sector exposure before position sizing
- Reject trade if sector limit breached

**E. Strategy-Based Adjustments**
- High-confidence signals: 1.5x normal size (max 1.5% risk)
- Low-confidence signals: 0.5x normal size (0.5% risk)
- Winning streak adjustment: Can increase to 1.5% risk
- Losing streak adjustment: Reduce to 0.5% risk

**F. Liquidity Checks**
- Position size < 2% of stock's average daily volume
- Ensures easy entry and exit
- Prevents market impact

**Deliverables:**
- Position sizing calculator
- Risk parameter configuration
- Position size validation module
- Risk reports

---

### 3.2 RISK LIMITS MANAGER

**Purpose:** Enforce overall portfolio risk limits

**Risk Limits:**

**A. Per-Trade Limits**
- Maximum risk per trade: 1-2% of capital
- Maximum position size: 20% of capital
- Minimum risk-reward ratio: 1.5:1
- Reject trades not meeting criteria

**B. Daily Limits**
- Maximum daily loss: 3% of capital
- Maximum trades per day: 5 trades
- Stop trading if daily limit hit
- Resume next day

**C. Weekly Limits**
- Maximum weekly loss: 6% of capital
- Review strategy performance if limit hit
- Consider reducing position sizes

**D. Monthly Limits**
- Maximum monthly drawdown: 10% of capital
- Trigger full system review if breached
- May pause trading for strategy reassessment

**E. Position Limits**
- Maximum open positions: 8-10 stocks
- Maximum positions per sector: 3-4 stocks
- Diversification requirement: Minimum 3 sectors

**F. Drawdown Protections**
- Current drawdown from peak: Track continuously
- If drawdown > 5%: Reduce position sizes by 50%
- If drawdown > 10%: Stop new trades, hold existing
- If drawdown > 15%: Exit all positions, system pause

**G. Correlation Risk**
- Track correlation between holdings
- Maximum average correlation: 0.7
- Reject new position if increases correlation risk

**Deliverables:**
- Risk limits enforcement module
- Risk breach alert system
- Automatic trading halt mechanism
- Risk dashboard

---

### 3.3 BROKERAGE & TAX CALCULATOR

**Purpose:** Accurately calculate all trading costs (Indian regulations)

**Cost Components:**

**A. Brokerage Charges**
- Discount brokers: ₹20 per order (flat) OR 0.03% (whichever lower)
- Full-service brokers: 0.5-1% per transaction
- Configuration: Set your broker's charges

**B. Securities Transaction Tax (STT)**
- Equity Delivery Buy: 0.1% of transaction value
- Equity Delivery Sell: 0.1% of transaction value
- Total STT on delivery: 0.2% (buy + sell)

**C. Exchange Transaction Charges**
- NSE: 0.00325% of transaction value
- BSE: 0.003% of transaction value

**D. GST (Goods and Services Tax)**
- 18% on (Brokerage + Transaction charges)

**E. SEBI Charges**
- ₹10 per crore of transaction value
- Usually negligible for retail

**F. Stamp Duty**
- 0.015% on buy side (or ₹1500 per crore)
- Varies by state
- Maharashtra: 0.015%

**G. Depository Participant (DP) Charges**
- Charged only on sell side
- Typically ₹13-20 per scrip (not per share)
- Per transaction, not daily

**Total Approximate Cost:**
- Intraday: ~0.05% (both sides)
- Delivery: ~0.5-0.7% (both sides)
- For paper trading: Use 0.5% as conservative estimate

**Calculation Logic:**
- Calculate on every trade execution
- Deduct from cash balance
- Track total costs paid (impacts returns)
- Include in P&L calculations

**Deliverables:**
- Comprehensive cost calculator
- Configuration for different brokers
- Cost impact analyzer
- Fee breakdown reports

---

## PHASE 4: EXECUTION LAYER (Week 7-8)

### 4.1 PAPER TRADING ENGINE

**Purpose:** Simulate real trading without actual money

**Components:**

**A. Simulated Order Execution**
- Order types: Market orders (use closing price)
- Execution price: EOD closing price
- Slippage simulation: Add 0.1% slippage to market orders
- Partial fills: Not applicable for EOD trading
- Order rejection scenarios: Circuit limits, insufficient funds

**B. Portfolio State Manager**
- Track cash balance
- Track all holdings (quantity, avg price)
- Update after each trade
- Calculate unrealized P&L for open positions
- Calculate realized P&L for closed trades

**C. Trade Execution Workflow**
1. Receive BUY signal from strategy
2. Validate signal (still valid at EOD?)
3. Check risk limits (can we take this trade?)
4. Calculate position size
5. Check sufficient cash
6. Execute simulated buy
7. Update holdings table
8. Record in trades table
9. Deduct cash (price * quantity + charges)
10. Log execution

**D. Exit Execution Workflow**
1. Check all open positions
2. Evaluate exit conditions (stop loss, target, strategy exit)
3. For positions meeting exit:
   - Execute simulated sell
   - Calculate P&L
   - Update holdings (reduce/remove)
   - Record in trades table
   - Add cash (price * quantity - charges)
   - Log execution with P&L

**E. EOD Reconciliation**
- Update current prices for all holdings
- Recalculate unrealized P&L
- Update portfolio value
- Check if any stop losses hit
- Check if any targets reached
- Generate daily summary

**F. Order Logs**
- Every order attempt logged (success/failure)
- Rejection reasons tracked
- Audit trail maintained
- Used for debugging and analysis

**Deliverables:**
- Paper trading simulator
- Order execution module
- Portfolio reconciliation script
- Execution logs

---

### 4.2 DAILY WORKFLOW ORCHESTRATOR

**Purpose:** Automate the entire daily trading workflow

**Daily Schedule (Indian Market Hours):**

**Morning Routine (Before 9:15 AM):**
- System health check
- Check data availability
- Check API connectivity
- Load watchlist stocks

**Market Hours (9:15 AM - 3:30 PM):**
- No action (EOD system)
- Optional: Monitor for breaking news

**Post-Market Routine (After 3:30 PM):**

**Step 1: Data Update (3:35 PM - 3:45 PM)**
- Fetch today's OHLCV data for all stocks
- Validate data completeness
- Update database
- Check for corporate actions

**Step 2: Indicator Calculation (3:45 PM - 3:50 PM)**
- Calculate all technical indicators
- Update indicator cache
- Flag any calculation errors

**Step 3: Exit Management (3:50 PM - 4:00 PM)**
- Check all open positions against exit rules
- Identify positions to close
- Execute exit orders (simulated)
- Update holdings and cash balance

**Step 4: Signal Generation (4:00 PM - 4:10 PM)**
- Run all strategies on all stocks
- Collect BUY signals
- Score and rank signals
- Generate top opportunities list

**Step 5: Entry Management (4:10 PM - 4:20 PM)**
- Validate top signals
- Check risk limits
- Calculate position sizes
- Execute entry orders (simulated)
- Update holdings and cash balance

**Step 6: EOD Reconciliation (4:20 PM - 4:30 PM)**
- Update all position values
- Calculate portfolio P&L
- Save daily snapshot
- Update performance metrics

**Step 7: Reporting (4:30 PM - 4:35 PM)**
- Generate daily summary email/notification
- Update dashboards
- Save logs
- Backup database

**Error Handling:**
- Retry mechanism for data failures
- Skip trades on data errors (safety first)
- Log all errors with timestamps
- Send alert notifications for critical errors

**Deliverables:**
- Orchestration script
- Scheduling configuration
- Error handling framework
- Notification system

---

### 4.3 MONITORING & ALERTS

**Purpose:** Track system health and performance

**Monitoring Components:**

**A. System Health Monitors**
- Data fetching success rate
- API response times
- Database connection status
- Disk space availability
- Script execution status

**B. Trading Activity Monitors**
- Signals generated today
- Trades executed today
- Rejected signals (and reasons)
- Open positions count
- Cash balance status

**C. Performance Monitors**
- Daily P&L
- Drawdown level
- Win rate (rolling 20 trades)
- Risk-reward achieved
- Strategy-wise performance

**D. Alert Triggers**
- Data fetch failure (immediate alert)
- Daily loss limit reached (immediate alert)
- Drawdown > 5% (warning alert)
- Unusual position size (validation alert)
- Database errors (immediate alert)
- No trades in 5 days (review alert)
- Strategy underperforming (weekly alert)

**E. Alert Channels**
- Email notifications
- Telegram bot messages (optional)
- SMS for critical alerts (optional)
- Log file entries (always)

**Deliverables:**
- Monitoring dashboard
- Alert system
- Log aggregator
- Health check script

---

## PHASE 5: ANALYSIS & OPTIMIZATION (Week 9-10)

### 5.1 BACKTESTING FRAMEWORK

**Purpose:** Test strategies on historical data before live deployment

**Components:**

**A. Historical Simulation**
- Load historical data (2-3 years minimum)
- Replay day-by-day
- Generate signals using strategy rules
- Execute simulated trades
- Track portfolio evolution
- Do NOT use future data (look-ahead bias)

**B. Backtesting Metrics**
- Total Return %
- Annual Return %
- Maximum Drawdown
- Sharpe Ratio (risk-adjusted return)
- Sortino Ratio (downside risk)
- Win Rate %
- Average Win vs Average Loss
- Profit Factor (Gross Profit / Gross Loss)
- Maximum consecutive losses
- Number of trades
- Average holding period
- Recovery time from drawdowns

**C. Walk-Forward Testing**
- Train on 60% data → Test on next 20% → Validate on final 20%
- Rolling window approach
- Prevents overfitting
- More realistic performance estimate

**D. Sensitivity Analysis**
- Test strategy with different parameters
- Example: RSI threshold 30 vs 35 vs 40
- Find robust parameter ranges
- Avoid curve-fitting to historical data

**E. Monte Carlo Simulation**
- Randomize trade sequence
- Test portfolio under different scenarios
- Estimate probability of drawdowns
- Calculate confidence intervals for returns

**F. Comparison Reports**
- Strategy vs Buy-and-Hold (Nifty 50)
- Strategy vs Strategy comparisons
- Best and worst periods
- Correlation with market returns

**Deliverables:**
- Backtesting engine
- Performance metrics calculator
- Backtest report generator
- Parameter optimization module

---

### 5.2 PERFORMANCE ANALYTICS

**Purpose:** Understand what's working and what's not

**Analysis Components:**

**A. Trade Analysis**
- Win rate by strategy
- Win rate by sector
- Win rate by market condition
- Win rate by day of week
- Average holding period by outcome
- Slippage analysis (expected vs actual)

**B. Strategy Analysis**
- Which strategies are performing?
- Which strategies are underperforming?
- Strategy correlation (diversification)
- Strategy drawdown contribution
- Strategy risk-reward achievement

**C. Portfolio Analysis**
- Sector exposure over time
- Position concentration
- Correlation between holdings
- Turnover rate
- Cash utilization
- Opportunity cost (missed signals)

**D. Risk Analysis**
- Realized risk vs planned risk
- Drawdown periods and recovery
- Value at Risk (VaR)
- Conditional VaR (worst-case losses)
- Risk-adjusted returns
- Risk limit breaches

**E. Time-Based Analysis**
- Monthly returns heatmap
- Rolling performance windows
- Drawdown periods visualization
- Equity curve with buy-hold comparison
- Underwater chart (drawdown visualization)

**F. Signal Quality Analysis**
- Signal-to-trade conversion rate
- Why signals were rejected
- Signals that weren't taken but would've won
- Signals that were taken but shouldn't have been
- Optimal signal threshold tuning

**Deliverables:**
- Analytics dashboard
- Monthly performance reports
- Strategy review reports
- Optimization recommendations

---

### 5.3 OPTIMIZATION ENGINE

**Purpose:** Continuously improve strategies and parameters

**Optimization Approach:**

**A. Parameter Tuning**
- Grid search over parameter ranges
- Example: RSI threshold [25, 30, 35, 40]
- Test all combinations on historical data
- Select parameters with best risk-adjusted returns
- Avoid overfitting (test on out-of-sample)

**B. Strategy Selection**
- Enable/disable strategies based on performance
- Pause underperforming strategies (3 months negative)
- Allocate more capital to winning strategies
- Retire permanently broken strategies

**C. Market Regime Adaptation**
- Detect market regime (bull/bear/sideways)
- Use different strategies for different regimes
- Trend strategies in bull markets
- Mean reversion in sideways markets
- Capital preservation in bear markets

**D. Continuous Improvement Cycle**
1. Analyze last month's performance
2. Identify issues (excessive losses, missed opportunities)
3. Propose improvements (parameter changes, new filters)
4. Backtest improvements
5. If better → Deploy next month
6. If worse → Discard, try alternatives
7. Repeat monthly

**E. A/B Testing**
- Run two versions of strategy side-by-side
- Allocate 50% capital to each
- Compare performance over 3 months
- Keep winner, discard loser

**F. Documentation**
- Document all changes made
- Document reasoning
- Track performance before/after
- Build knowledge base

**Deliverables:**
- Parameter optimization script
- Strategy selection algorithm
- A/B testing framework
- Optimization logs

---

## PHASE 6: REPORTING & VISUALIZATION (Week 11-12)

### 6.1 DAILY REPORTS

**Daily Email Report Contents:**

**A. Portfolio Summary**
- Current total capital (cash + holdings value)
- Change from yesterday (₹ and %)
- Unrealized P&L on open positions
- Number of open positions
- Largest position (stock and %)
- Sector breakdown

**B. Today's Activity**
- Trades executed (entries and exits)
- Entry details: Stock, quantity, price, reasoning
- Exit details: Stock, quantity, price, P&L, reasoning
- Total brokerage paid today
- Cash balance remaining

**C. Signals Generated**
- Top 5 signals considered
- Signals executed vs rejected
- Rejection reasons

**D. Open Positions Status**
- List of all holdings
- Current price vs entry price
- Unrealized P&L per position
- Days held
- Approaching stop loss or target?

**E. Risk Metrics**
- Current drawdown from peak
- Daily risk utilized (% of limit)
- Portfolio risk level
- Any risk limit breaches

**Deliverables:**
- Email report generator
- HTML email template
- PDF report option
- Report scheduling

---

### 6.2 DASHBOARD (WEEKLY/MONTHLY VIEW)

**Dashboard Components:**

**A. Performance Overview**
- Equity curve (capital over time)
- Benchmark comparison (Nifty 50)
- Monthly returns heatmap
- Year-to-date return
- All-time return
- Maximum drawdown indicator

**B. Portfolio Composition**
- Pie chart: Sector allocation
- Bar chart: Top holdings by value
- Table: All holdings with details
- Cash percentage
- Number of positions trend

**C. Strategy Performance**
- Strategy-wise P&L contribution
- Strategy-wise win rates
- Strategy-wise trade counts
- Active vs paused strategies

**D. Risk Dashboard**
- Current vs maximum drawdown
- Risk utilization gauge
- Sector concentration chart
- Position size distribution
- Correlation heatmap

**E. Trade Statistics**
- Total trades executed
- Win rate %
- Average win size
- Average loss size
- Profit factor
- Best trade / Worst trade
- Average holding period

**F. Market Conditions**
- Nifty 50 trend status
- VIX (volatility index)
- Advancing vs Declining stocks
- Sector performance
- Market regime indicator

**Technology:**
- Python libraries: matplotlib, plotly, dash
- Simple HTML dashboard (update daily)
- Or use Google Sheets for easy viewing

**Deliverables:**
- Dashboard web page
- Dashboard update script
- Mobile-friendly view
- Dashboard documentation

---

### 6.3 MONTHLY REVIEW REPORT

**Monthly Report Contents:**

**A. Executive Summary**
- Monthly return %
- Vs benchmark performance
- Number of trades taken
- Win rate for the month
- Largest win and loss
- End-of-month capital

**B. Detailed Performance**
- Week-by-week breakdown
- Strategy-wise contribution
- Sector-wise contribution
- Best performing stocks
- Worst performing stocks

**C. Risk Review**
- Maximum drawdown reached
- Risk limits hit (if any)
- Average position size
- Risk-reward achieved vs target

**D. Trade Analysis**
- All trades table
- Winners vs losers analysis
- Average holding period
- Slippage analysis
- Cost analysis (total fees paid)

**E. Strategy Review**
- Which strategies worked well?
- Which strategies underperformed?
- Any strategy paused?
- Any parameter changes made?

**F. Market Conditions Review**
- How was the market in general?
- Market regime (bull/bear/sideways)
- Significant events impacted trading?
- Volatility levels

**G. Lessons Learned**
- What went well?
- What could be improved?
- Mistakes made?
- Action items for next month

**H. Forward-Looking**
- Strategy changes planned
- Parameter adjustments
- Watchlist updates
- Capital allocation changes

**Deliverables:**
- Monthly report template
- Automated report generator
- PDF export functionality
- Email delivery

---

## PHASE 7: ADVANCED FEATURES (Week 13+)

### 7.1 FUNDAMENTAL FILTERS

**Purpose:** Add fundamental screening to improve signal quality

**Fundamental Criteria:**

**A. Financial Health Filters**
- Debt-to-Equity ratio < 1.0
- Current ratio > 1.5
- Interest coverage > 3x
- Positive operating cash flow

**B. Growth Filters**
- Revenue growth > 10% YoY
- Profit growth > 10% YoY
- ROE > 15%
- ROCE > 15%

**C. Valuation Filters**
- P/E ratio reasonable for sector
- P/B ratio < 5
- PEG ratio < 2
- Avoid expensive stocks in downtrends

**D. Quality Filters**
- Promoter holding > 50%
- No promoter pledge concerns
- No regulatory issues
- Good corporate governance ratings

**Data Sources:**
- Screener.in (manual scraping, free)
- Tickertape (manual, free)
- BSE/NSE announcements (free)
- Paid: Capitaline, Ace Equity (₹10,000+/year)

**Implementation:**
- Quarterly fundamental data update
- Filter signals: Only trade fundamentally sound stocks
- Reject signals for weak fundamentals

**Deliverables:**
- Fundamental data scraper
- Fundamental filter module
- Stock screening dashboard
- Quarterly update process

---

### 7.2 NEWS & EVENT MONITORING

**Purpose:** Avoid trading around major events, incorporate sentiment

**Components:**

**A. Corporate Actions Calendar**
- Earnings announcement dates
- Dividend ex-dates
- Bonus/split announcements
- AGM dates
- Pause trading 2 days before/after major events

**B. News Sentiment (Basic)**
- Scrape business news websites (MoneyControl, ET)
- Simple keyword matching (profit, loss, growth, scandal)
- Positive/Negative/Neutral classification
- Avoid stocks with recent negative news

**C. Market Events Calendar**
- Union Budget dates
- RBI policy dates
- Major economic data releases
- Global events (Fed meetings, etc.)
- Reduce overall position sizes before major events

**Implementation:**
- Daily news scraping
- Event calendar maintenance
- Pre-event risk reduction
- Post-event opportunity scanning

**Deliverables:**
- News scraper module
- Event calendar integration
- Sentiment analysis (basic)
- Event-based risk adjustment

---

### 7.3 TRANSITION TO LIVE TRADING (FUTURE)

**When to Consider Live Trading:**
- Minimum 6 months of consistent paper trading
- Overall positive returns
- Tested through different market conditions
- Maximum drawdown acceptable
- Clear understanding of all system components
- Confidence in risk management

**Transition Plan:**

**Phase 1: Micro Capital (3 months)**
- Start with ₹10,000-25,000 real money
- Test actual broker integration
- Experience real slippage
- Handle real emotions
- Verify all systems work with real broker

**Phase 2: Fractional Capital (3 months)**
- If Phase 1 successful, increase to ₹50,000-1,00,000
- Now taking more trades
- Better statistical significance
- Still learning, still adjusting

**Phase 3: Full Capital (Ongoing)**
- If Phase 2 successful, deploy full capital
- Maintain discipline learned in paper trading
- Continue monitoring and optimization
- Never stop learning

**Broker Integration Requirements:**
- Broker API selection (Zerodha, Upstox, Fyers)
- API authentication setup
- Order placement integration
- Order status tracking
- Position reconciliation
- Real-time price feeds
- Error handling for API failures

**Deliverables:**
- Broker API integration module
- Live order execution (when ready)
- Real-time monitoring
- Failsafe mechanisms

---

## SYSTEM ARCHITECTURE SUMMARY

```
┌─────────────────────────────────────────────────────────────┐
│                   ORCHESTRATOR (Daily Scheduler)            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ├─→ 1. Data Layer
                              │   ├─ yfinance API
                              │   ├─ NSEpy API
                              │   ├─ Data Validator
                              │   └─ Database (SQLite)
                              │
                              ├─→ 2. Indicator Layer
                              │   ├─ Trend Indicators
                              │   ├─ Momentum Indicators
                              │   ├─ Volatility Indicators
                              │   └─ Volume Indicators
                              │
                              ├─→ 3. Strategy Layer
                              │   ├─ Strategy 1: Trend + RSI
                              │   ├─ Strategy 2: Mean Reversion
                              │   ├─ Strategy 3: Breakout
                              │   ├─ Signal Aggregator
                              │   └─ Signal Validator
                              │
                              ├─→ 4. Risk Layer
                              │   ├─ Position Sizer
                              │   ├─ Risk Limits Manager
                              │   ├─ Brokerage Calculator
                              │   └─ Portfolio Risk Monitor
                              │
                              ├─→ 5. Execution Layer
                              │   ├─ Paper Trading Engine
                              │   ├─ Order Manager
                              │   ├─ Portfolio Manager
                              │   └─ EOD Reconciliation
                              │
                              ├─→ 6. Analysis Layer
                              │   ├─ Performance Analytics
                              │   ├─ Backtesting Engine
                              │   ├─ Optimization Engine
                              │   └─ Report Generator
                              │
                              └─→ 7. Monitoring Layer
                                  ├─ System Health Monitor
                                  ├─ Alert System
                                  ├─ Dashboard
                                  └─ Logging System
```

---

## KEY SUCCESS FACTORS

1. **Start Simple:** Begin with 1-2 strategies, expand gradually
2. **Focus on Risk:** Risk management is MORE important than returns
3. **Data Quality:** Garbage in = Garbage out
4. **Discipline:** Follow your rules religiously
5. **Patience:** Don't expect overnight success
6. **Documentation:** Document everything you learn
7. **Continuous Learning:** Markets evolve, so must your system
8. **Realistic Expectations:** Aim for consistent 15-20% annual returns
9. **Avoid Over-Trading:** Less is often more
10. **Preserve Capital:** Protect your downside first

---

## TIMELINE SUMMARY

- **Week 1-2:** Data pipeline + Database setup
- **Week 3-4:** Technical indicators + Strategy development
- **Week 5-6:** Risk management + Position sizing
- **Week 7-8:** Paper trading engine + Daily orchestration
- **Week 9-10:** Backtesting + Performance analytics
- **Week 11-12:** Reports + Dashboard
- **Week 13+:** Advanced features + Optimization

**Total Time to Functional System:** 10-12 weeks of focused work

---

## COST BREAKDOWN (Paper Trading Phase)

**FREE Components:**
- Data APIs: ₹0 (yfinance, NSEpy)
- Database: ₹0 (SQLite)
- Development: ₹0 (Python, open-source libraries)
- Hosting: ₹0 (run on personal computer)

**Optional Paid (Future):**
- Reliable data API: ₹2,000-3,000/month
- Cloud hosting: ₹500-2,000/month
- Fundamental data: ₹10,000+/year

**Total Paper Trading Phase: ₹0**

---

## EXPECTED OUTCOMES

After 6-12 months of paper trading:
- Understand what works and what doesn't
- Realistic expectation of returns (10-25% annually)
- Experience different market conditions
- Build confidence in system
- Identify weak points to improve
- Ready for live trading (if successful)

---

## NEXT STEPS

1. Set up development environment (Python, libraries)
2. Create project folder structure
3. Initialize database with schema
4. Start with data pipeline (Week 1)
5. Follow roadmap week by week
6. Don't skip steps
7. Test thoroughly at each phase
8. Document learnings

---

**END OF NON-AI TRADING SYSTEM ARCHITECTURE**
