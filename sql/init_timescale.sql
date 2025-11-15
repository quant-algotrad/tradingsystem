-- TimescaleDB Initialization Script
-- Optimized time-series database for market data

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ========================================
-- Market Data Tables
-- ========================================

-- OHLCV Data (optimized for time-series)
CREATE TABLE IF NOT EXISTS market_data_ohlcv (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,  -- '1m', '5m', '15m', '1h', '1d'
    open DECIMAL(12, 2) NOT NULL,
    high DECIMAL(12, 2) NOT NULL,
    low DECIMAL(12, 2) NOT NULL,
    close DECIMAL(12, 2) NOT NULL,
    volume BIGINT NOT NULL,
    source VARCHAR(50),
    quality_score DECIMAL(3, 2),  -- 0-1 data quality
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create hypertable (TimescaleDB magic!)
SELECT create_hypertable('market_data_ohlcv', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Create indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_time
    ON market_data_ohlcv (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_ohlcv_timeframe
    ON market_data_ohlcv (timeframe, time DESC);

-- Real-time Quotes
CREATE TABLE IF NOT EXISTS market_data_quotes (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    bid DECIMAL(12, 2),
    ask DECIMAL(12, 2),
    bid_size INT,
    ask_size INT,
    last_price DECIMAL(12, 2),
    last_volume INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

SELECT create_hypertable('market_data_quotes', 'time',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_quotes_symbol_time
    ON market_data_quotes (symbol, time DESC);

-- ========================================
-- Indicator Data (cached calculations)
-- ========================================

CREATE TABLE IF NOT EXISTS indicator_values (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    indicator_name VARCHAR(50) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    value DECIMAL(12, 4),
    signal VARCHAR(10),  -- 'BUY', 'SELL', 'NEUTRAL'
    strength DECIMAL(5, 2),  -- 0-100
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

SELECT create_hypertable('indicator_values', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_indicators_symbol_name_time
    ON indicator_values (symbol, indicator_name, time DESC);

-- ========================================
-- Signal Data
-- ========================================

CREATE TABLE IF NOT EXISTS signals (
    time TIMESTAMPTZ NOT NULL,
    signal_id UUID NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    signal_type VARCHAR(10) NOT NULL,  -- 'BUY', 'SELL', 'NEUTRAL'
    confidence DECIMAL(5, 2) NOT NULL,  -- 0-100
    strength DECIMAL(5, 2),
    strategy_name VARCHAR(100),
    timeframe VARCHAR(10),
    bullish_signals INT DEFAULT 0,
    bearish_signals INT DEFAULT 0,
    neutral_signals INT DEFAULT 0,
    reasons TEXT[],
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (time, signal_id)
);

SELECT create_hypertable('signals', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_signals_symbol_time
    ON signals (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_signals_type_time
    ON signals (signal_type, time DESC);

-- ========================================
-- Trade Data
-- ========================================

CREATE TABLE IF NOT EXISTS trades (
    time TIMESTAMPTZ NOT NULL,
    trade_id UUID NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    action VARCHAR(10) NOT NULL,  -- 'BUY', 'SELL', 'SHORT', 'COVER'
    quantity INT NOT NULL,
    price DECIMAL(12, 2) NOT NULL,
    order_type VARCHAR(10) DEFAULT 'MARKET',
    position_type VARCHAR(10),  -- 'SWING', 'INTRADAY'
    strategy VARCHAR(100),
    stop_loss DECIMAL(12, 2),
    target_price DECIMAL(12, 2),
    risk_amount DECIMAL(12, 2),
    status VARCHAR(20) DEFAULT 'PENDING',
    filled_quantity INT DEFAULT 0,
    filled_price DECIMAL(12, 2),
    pnl DECIMAL(12, 2),
    pnl_percent DECIMAL(8, 4),
    decision_score DECIMAL(5, 2),
    execution_time TIMESTAMPTZ,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (time, trade_id)
);

SELECT create_hypertable('trades', 'time',
    chunk_time_interval => INTERVAL '1 week',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_trades_symbol_time
    ON trades (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_trades_status
    ON trades (status, time DESC);

-- ========================================
-- Position Data
-- ========================================

CREATE TABLE IF NOT EXISTS positions (
    time TIMESTAMPTZ NOT NULL,
    position_id UUID NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    position_type VARCHAR(10),  -- 'LONG', 'SHORT'
    quantity INT NOT NULL,
    entry_price DECIMAL(12, 2) NOT NULL,
    current_price DECIMAL(12, 2),
    stop_loss DECIMAL(12, 2),
    target_price DECIMAL(12, 2),
    unrealized_pnl DECIMAL(12, 2),
    unrealized_pnl_percent DECIMAL(8, 4),
    status VARCHAR(20) DEFAULT 'OPEN',
    opened_at TIMESTAMPTZ NOT NULL,
    closed_at TIMESTAMPTZ,
    strategy VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (time, position_id)
);

SELECT create_hypertable('positions', 'time',
    chunk_time_interval => INTERVAL '1 week',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_positions_symbol_status
    ON positions (symbol, status, time DESC);

-- ========================================
-- Risk Events
-- ========================================

CREATE TABLE IF NOT EXISTS risk_events (
    time TIMESTAMPTZ NOT NULL,
    event_id UUID NOT NULL,
    risk_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,  -- 'INFO', 'WARNING', 'CRITICAL'
    metric_name VARCHAR(100) NOT NULL,
    current_value DECIMAL(12, 2),
    limit_value DECIMAL(12, 2),
    utilization_percent DECIMAL(5, 2),
    symbol VARCHAR(20),
    action_taken VARCHAR(100),
    message TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (time, event_id)
);

SELECT create_hypertable('risk_events', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_risk_severity_time
    ON risk_events (severity, time DESC);

-- ========================================
-- Portfolio Snapshots
-- ========================================

CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    time TIMESTAMPTZ NOT NULL PRIMARY KEY,
    total_capital DECIMAL(15, 2) NOT NULL,
    available_cash DECIMAL(15, 2) NOT NULL,
    invested_amount DECIMAL(15, 2),
    unrealized_pnl DECIMAL(12, 2),
    realized_pnl DECIMAL(12, 2),
    daily_pnl DECIMAL(12, 2),
    daily_pnl_percent DECIMAL(8, 4),
    open_positions_count INT,
    total_trades_count INT,
    win_rate DECIMAL(5, 2),
    sharpe_ratio DECIMAL(8, 4),
    max_drawdown DECIMAL(8, 4),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

SELECT create_hypertable('portfolio_snapshots', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- ========================================
-- Continuous Aggregates (Pre-computed Views)
-- ========================================

-- Daily OHLCV summary
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_ohlcv
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS bucket,
    symbol,
    first(open, time) AS open,
    max(high) AS high,
    min(low) AS low,
    last(close, time) AS close,
    sum(volume) AS volume
FROM market_data_ohlcv
WHERE timeframe = '1m' OR timeframe = '5m'
GROUP BY bucket, symbol;

-- Refresh policy (update every hour)
SELECT add_continuous_aggregate_policy('daily_ohlcv',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Hourly signal summary
CREATE MATERIALIZED VIEW IF NOT EXISTS hourly_signals
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    symbol,
    signal_type,
    count(*) AS signal_count,
    avg(confidence) AS avg_confidence,
    max(strength) AS max_strength
FROM signals
GROUP BY bucket, symbol, signal_type;

SELECT add_continuous_aggregate_policy('hourly_signals',
    start_offset => INTERVAL '2 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- ========================================
-- Retention Policies (Auto-delete old data)
-- ========================================

-- Keep 1-minute data for 7 days
SELECT add_retention_policy('market_data_ohlcv',
    INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Keep quotes for 1 day
SELECT add_retention_policy('market_data_quotes',
    INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Keep indicators for 30 days
SELECT add_retention_policy('indicator_values',
    INTERVAL '30 days',
    if_not_exists => TRUE
);

-- Keep signals for 90 days
SELECT add_retention_policy('signals',
    INTERVAL '90 days',
    if_not_exists => TRUE
);

-- Keep trades forever (no retention policy)

-- ========================================
-- Helper Functions
-- ========================================

-- Get latest price for symbol
CREATE OR REPLACE FUNCTION get_latest_price(p_symbol VARCHAR)
RETURNS DECIMAL AS $$
    SELECT close
    FROM market_data_ohlcv
    WHERE symbol = p_symbol
    ORDER BY time DESC
    LIMIT 1;
$$ LANGUAGE SQL;

-- Get daily P&L
CREATE OR REPLACE FUNCTION get_daily_pnl()
RETURNS TABLE(
    date DATE,
    realized_pnl DECIMAL,
    unrealized_pnl DECIMAL,
    total_pnl DECIMAL
) AS $$
    SELECT
        time::DATE as date,
        sum(CASE WHEN status = 'FILLED' THEN pnl ELSE 0 END) as realized_pnl,
        sum(CASE WHEN status = 'OPEN' THEN pnl ELSE 0 END) as unrealized_pnl,
        sum(pnl) as total_pnl
    FROM trades
    WHERE time >= CURRENT_DATE
    GROUP BY time::DATE
    ORDER BY date DESC;
$$ LANGUAGE SQL;

-- ========================================
-- Initial Data
-- ========================================

-- Insert initial portfolio snapshot
INSERT INTO portfolio_snapshots (
    time, total_capital, available_cash, invested_amount,
    unrealized_pnl, realized_pnl, daily_pnl, daily_pnl_percent,
    open_positions_count, total_trades_count, win_rate
) VALUES (
    NOW(), 50000.00, 50000.00, 0.00,
    0.00, 0.00, 0.00, 0.00,
    0, 0, 0.00
) ON CONFLICT (time) DO NOTHING;

-- ========================================
-- Grants (if needed)
-- ========================================

-- Grant permissions to trading user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trading;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trading;

-- ========================================
-- Info
-- ========================================

-- Display table sizes
DO $$
BEGIN
    RAISE NOTICE 'TimescaleDB initialized successfully!';
    RAISE NOTICE 'Tables created: market_data_ohlcv, market_data_quotes, indicator_values, signals, trades, positions, risk_events, portfolio_snapshots';
    RAISE NOTICE 'Continuous aggregates: daily_ohlcv, hourly_signals';
    RAISE NOTICE 'Initial capital: ₹50,000';
END $$;
