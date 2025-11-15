"""
Database Initialization Module
Creates and initializes the SQLite database for the Non-AI Trading System
Capital: ₹50,000 | Tables: 12
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path


class DatabaseInitializer:
    """Handles database creation and initialization"""

    def __init__(self, db_path=None):
        """
        Initialize database connection

        Args:
            db_path: Path to database file (default: ../data/trading_system.db)
        """
        if db_path is None:
            # Default path: /home/user/tradingsystem/data/trading_system.db
            base_dir = Path(__file__).parent.parent.parent
            db_path = base_dir / 'data' / 'trading_system.db'

        self.db_path = Path(db_path)
        self.schema_path = Path(__file__).parent / 'schema.sql'
        self.conn = None
        self.cursor = None

    def create_database(self):
        """Create database and all tables from schema.sql"""
        try:
            # Ensure data directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # Connect to database (creates if doesn't exist)
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()

            print(f"[INFO] Connected to database: {self.db_path}")

            # Read and execute schema SQL
            if not self.schema_path.exists():
                raise FileNotFoundError(f"Schema file not found: {self.schema_path}")

            with open(self.schema_path, 'r') as f:
                schema_sql = f.read()

            # Execute schema (creates all tables and indexes)
            self.cursor.executescript(schema_sql)
            self.conn.commit()

            print("[SUCCESS] Database schema created successfully!")

            # Verify tables
            self._verify_tables()

            # Initialize with starting capital
            self._initialize_portfolio()

            return True

        except Exception as e:
            print(f"[ERROR] Database creation failed: {e}")
            if self.conn:
                self.conn.rollback()
            return False

    def _verify_tables(self):
        """Verify all 12 tables were created"""
        expected_tables = [
            'holdings',
            'trades',
            'daily_portfolio',
            'signals',
            'strategy_performance',
            'risk_metrics',
            'market_data',
            'intraday_positions',
            'stop_loss_tracker',
            'options_positions',
            'multi_timeframe_signals',
            'order_queue'
        ]

        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        actual_tables = [row[0] for row in self.cursor.fetchall()]

        print(f"\n[INFO] Tables created: {len(actual_tables)}")
        for table in actual_tables:
            print(f"  ✓ {table}")

        # Check if all expected tables exist
        missing_tables = set(expected_tables) - set(actual_tables)
        if missing_tables:
            print(f"\n[WARNING] Missing tables: {missing_tables}")
        else:
            print("\n[SUCCESS] All 12 tables created successfully!")

    def _initialize_portfolio(self):
        """Initialize portfolio with starting capital"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Check if portfolio already initialized
            self.cursor.execute(
                "SELECT COUNT(*) FROM daily_portfolio WHERE date = ?",
                (today,)
            )
            if self.cursor.fetchone()[0] > 0:
                print("[INFO] Portfolio already initialized for today")
                return

            # Insert initial portfolio snapshot
            initial_capital = 50000.0  # ₹50,000 starting capital

            self.cursor.execute("""
                INSERT INTO daily_portfolio (
                    date, starting_capital, ending_capital,
                    daily_pnl, daily_pnl_percent,
                    cumulative_pnl, cumulative_pnl_percent,
                    deployed_capital, available_cash,
                    num_positions, num_trades,
                    winning_trades, losing_trades, win_rate,
                    max_drawdown, sharpe_ratio, total_charges,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                today, initial_capital, initial_capital,
                0.0, 0.0,  # daily_pnl, daily_pnl_percent
                0.0, 0.0,  # cumulative_pnl, cumulative_pnl_percent
                0.0, initial_capital,  # deployed_capital, available_cash
                0, 0,  # num_positions, num_trades
                0, 0, 0.0,  # winning_trades, losing_trades, win_rate
                0.0, 0.0, 0.0,  # max_drawdown, sharpe_ratio, total_charges
                current_time
            ))

            # Initialize risk metrics
            self.cursor.execute("""
                INSERT INTO risk_metrics (
                    date, daily_loss, daily_loss_percent,
                    weekly_loss, weekly_loss_percent,
                    monthly_drawdown, monthly_drawdown_percent,
                    max_position_exposure, total_exposure, exposure_percent,
                    num_positions, num_sectors, sector_concentration,
                    risk_limit_breached, circuit_breaker_triggered,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                today, 0.0, 0.0,
                0.0, 0.0,
                0.0, 0.0,
                0.0, 0.0, 0.0,
                0, 0, '{}',
                0, 0,
                current_time
            ))

            self.conn.commit()
            print(f"[SUCCESS] Portfolio initialized with ₹{initial_capital:,.2f} capital")

        except Exception as e:
            print(f"[ERROR] Portfolio initialization failed: {e}")
            self.conn.rollback()

    def get_table_info(self, table_name):
        """Get column information for a table"""
        try:
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = self.cursor.fetchall()

            print(f"\n[INFO] Table: {table_name}")
            print(f"{'Column':<30} {'Type':<15} {'Not Null':<10} {'Default':<15}")
            print("-" * 70)
            for col in columns:
                col_id, name, col_type, not_null, default_val, pk = col
                print(f"{name:<30} {col_type:<15} {str(not_null):<10} {str(default_val):<15}")

            return columns

        except Exception as e:
            print(f"[ERROR] Failed to get table info: {e}")
            return None

    def get_database_stats(self):
        """Get database statistics"""
        try:
            stats = {}

            # Get table counts
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row[0] for row in self.cursor.fetchall()]

            print("\n" + "="*60)
            print("DATABASE STATISTICS")
            print("="*60)
            print(f"Database Path: {self.db_path}")
            print(f"Total Tables: {len(tables)}")
            print(f"Database Size: {self.db_path.stat().st_size / 1024:.2f} KB")
            print("\nTable Row Counts:")
            print("-" * 60)

            for table in tables:
                self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = self.cursor.fetchone()[0]
                stats[table] = count
                print(f"{table:<35} {count:>10} rows")

            print("="*60)

            return stats

        except Exception as e:
            print(f"[ERROR] Failed to get database stats: {e}")
            return None

    def reset_database(self):
        """Drop all tables and recreate (CAUTION: Deletes all data)"""
        try:
            # Get all table names
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in self.cursor.fetchall()]

            # Drop all tables
            for table in tables:
                self.cursor.execute(f"DROP TABLE IF EXISTS {table}")

            self.conn.commit()
            print("[WARNING] All tables dropped. Database reset.")

            # Recreate from schema
            return self.create_database()

        except Exception as e:
            print(f"[ERROR] Database reset failed: {e}")
            self.conn.rollback()
            return False

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("[INFO] Database connection closed")


def main():
    """Main function to initialize database"""
    print("="*60)
    print("NON-AI TRADING SYSTEM - DATABASE INITIALIZATION")
    print("Capital: ₹50,000 | Tables: 12")
    print("="*60)

    # Initialize database
    db = DatabaseInitializer()

    # Create database and tables
    success = db.create_database()

    if success:
        # Show database statistics
        db.get_database_stats()

        # Example: Show info for key tables
        print("\n")
        db.get_table_info('holdings')

    # Close connection
    db.close()

    return success


if __name__ == '__main__':
    main()
