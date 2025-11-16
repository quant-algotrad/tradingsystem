"""
Data Loader - Intelligent switch between Real and Mock data

Automatically uses real database data when available,
falls back to mock data for development/testing
"""

import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.utils import get_logger

logger = get_logger(__name__)

# Try real data first
try:
    from .data_loader_real import *
    from .data_loader_real import get_db_connection

    # Test connection
    _test_conn = get_db_connection()
    if _test_conn:
        _test_conn.close()
        USE_REAL_DATA = True
        logger.info("✅ Dashboard using REAL data from database")
    else:
        raise ConnectionError("Database unavailable")

except Exception as e:
    # Fallback to mock data
    USE_REAL_DATA = False
    logger.warning(f"⚠️ Dashboard using MOCK data (database unavailable): {e}")

    # Import all mock functions
    from .data_loader_mock import *


def is_using_real_data() -> bool:
    """Check if using real data"""
    return USE_REAL_DATA
