"""
Database Connection Utility
Provides database connection and query execution methods
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple


class DatabaseConnector:
    """Database connection and query manager"""

    def __init__(self, db_path=None):
        """
        Initialize database connector

        Args:
            db_path: Path to database file (default: ../data/trading_system.db)
        """
        if db_path is None:
            base_dir = Path(__file__).parent.parent.parent
            db_path = base_dir / 'data' / 'trading_system.db'

        self.db_path = Path(db_path)
        self.conn = None
        self.cursor = None

    def connect(self):
        """Establish database connection"""
        try:
            if not self.db_path.exists():
                raise FileNotFoundError(f"Database not found: {self.db_path}")

            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Enable column access by name
            self.cursor = self.conn.cursor()
            return True

        except Exception as e:
            print(f"[ERROR] Database connection failed: {e}")
            return False

    def execute_query(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """
        Execute SELECT query and return results

        Args:
            query: SQL SELECT query
            params: Query parameters (tuple)

        Returns:
            List of Row objects
        """
        try:
            if not self.conn:
                self.connect()

            self.cursor.execute(query, params)
            return self.cursor.fetchall()

        except Exception as e:
            print(f"[ERROR] Query execution failed: {e}")
            return []

    def execute_update(self, query: str, params: Tuple = ()) -> int:
        """
        Execute INSERT/UPDATE/DELETE query

        Args:
            query: SQL query
            params: Query parameters (tuple)

        Returns:
            Number of affected rows
        """
        try:
            if not self.conn:
                self.connect()

            self.cursor.execute(query, params)
            self.conn.commit()
            return self.cursor.rowcount

        except Exception as e:
            print(f"[ERROR] Update execution failed: {e}")
            if self.conn:
                self.conn.rollback()
            return 0

    def execute_many(self, query: str, params_list: List[Tuple]) -> int:
        """
        Execute query for multiple parameter sets (bulk insert/update)

        Args:
            query: SQL query
            params_list: List of parameter tuples

        Returns:
            Number of affected rows
        """
        try:
            if not self.conn:
                self.connect()

            self.cursor.executemany(query, params_list)
            self.conn.commit()
            return self.cursor.rowcount

        except Exception as e:
            print(f"[ERROR] Bulk execution failed: {e}")
            if self.conn:
                self.conn.rollback()
            return 0

    def get_portfolio_capital(self) -> float:
        """Get current portfolio capital"""
        query = """
            SELECT ending_capital
            FROM daily_portfolio
            ORDER BY date DESC
            LIMIT 1
        """
        result = self.execute_query(query)
        return result[0]['ending_capital'] if result else 50000.0

    def get_available_cash(self) -> float:
        """Get available cash for trading"""
        query = """
            SELECT available_cash
            FROM daily_portfolio
            ORDER BY date DESC
            LIMIT 1
        """
        result = self.execute_query(query)
        return result[0]['available_cash'] if result else 50000.0

    def get_open_positions(self, position_type: str = None) -> List[sqlite3.Row]:
        """
        Get all open positions

        Args:
            position_type: Filter by SWING/INTRADAY/OPTIONS (optional)

        Returns:
            List of position records
        """
        if position_type == 'SWING':
            return self.execute_query("SELECT * FROM holdings")
        elif position_type == 'INTRADAY':
            return self.execute_query(
                "SELECT * FROM intraday_positions WHERE status = 'OPEN'"
            )
        elif position_type == 'OPTIONS':
            return self.execute_query(
                "SELECT * FROM options_positions WHERE status = 'OPEN'"
            )
        else:
            # Return all positions
            swing = self.execute_query("SELECT * FROM holdings")
            intraday = self.execute_query(
                "SELECT * FROM intraday_positions WHERE status = 'OPEN'"
            )
            options = self.execute_query(
                "SELECT * FROM options_positions WHERE status = 'OPEN'"
            )
            return list(swing) + list(intraday) + list(options)

    def get_daily_pnl(self, date: str = None) -> Dict[str, Any]:
        """
        Get daily P&L metrics

        Args:
            date: Date in YYYY-MM-DD format (default: today)

        Returns:
            Dictionary with P&L metrics
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        query = "SELECT * FROM daily_portfolio WHERE date = ?"
        result = self.execute_query(query, (date,))

        if result:
            row = result[0]
            return {
                'date': row['date'],
                'starting_capital': row['starting_capital'],
                'ending_capital': row['ending_capital'],
                'daily_pnl': row['daily_pnl'],
                'daily_pnl_percent': row['daily_pnl_percent'],
                'cumulative_pnl': row['cumulative_pnl'],
                'win_rate': row['win_rate']
            }
        return {}

    def get_pending_signals(self) -> List[sqlite3.Row]:
        """Get all pending signals"""
        return self.execute_query(
            "SELECT * FROM signals WHERE status = 'PENDING' ORDER BY signal_strength DESC"
        )

    def get_pending_orders(self) -> List[sqlite3.Row]:
        """Get pending orders from queue"""
        return self.execute_query(
            "SELECT * FROM order_queue WHERE status = 'PENDING' ORDER BY priority ASC, created_at ASC"
        )

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Convenience function for quick queries
def quick_query(query: str, params: Tuple = ()) -> List[sqlite3.Row]:
    """
    Execute quick query without managing connection

    Args:
        query: SQL query
        params: Query parameters

    Returns:
        List of results
    """
    with DatabaseConnector() as db:
        return db.execute_query(query, params)


# Example usage
if __name__ == '__main__':
    # Test connection
    db = DatabaseConnector()

    if db.connect():
        print("[SUCCESS] Database connected")

        # Get portfolio capital
        capital = db.get_portfolio_capital()
        print(f"Portfolio Capital: ₹{capital:,.2f}")

        # Get available cash
        cash = db.get_available_cash()
        print(f"Available Cash: ₹{cash:,.2f}")

        # Get open positions
        positions = db.get_open_positions()
        print(f"Open Positions: {len(positions)}")

        # Get daily P&L
        pnl = db.get_daily_pnl()
        if pnl:
            print(f"Daily P&L: ₹{pnl['daily_pnl']:,.2f} ({pnl['daily_pnl_percent']:.2f}%)")

        db.close()
