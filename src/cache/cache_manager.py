"""
Redis Cache Layer
High-performance caching for market data and indicators

Pattern: Cache-Aside Pattern
- Read: Check cache first, fetch from source on miss
- Write: Update cache after fetching from source
- TTL: Automatic expiration based on data type
"""

from typing import Optional, Dict, Any
import json
import pickle
from datetime import datetime, timedelta
import pandas as pd

from src.utils import get_logger

logger = get_logger(__name__)

# Conditional Redis import
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class CacheManager:
    """
    Redis cache manager for trading data

    Pattern: Singleton Pattern
    - Single cache instance
    - Thread-safe connections
    - Automatic serialization
    """

    _instance: Optional['CacheManager'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._redis_client = None
        self._enabled = False

        # TTL configurations (in seconds)
        self.TTL_CONFIG = {
            'quote': 5,           # 5 seconds for real-time quotes
            'ohlcv_1m': 60,      # 1 minute for 1m bars
            'ohlcv_5m': 300,     # 5 minutes for 5m bars
            'ohlcv_15m': 900,    # 15 minutes for 15m bars
            'ohlcv_1h': 3600,    # 1 hour for hourly bars
            'ohlcv_1d': 86400,   # 24 hours for daily bars
            'indicator': 300,     # 5 minutes for indicators
            'symbol_info': 3600,  # 1 hour for symbol info
        }

        self._initialize_redis()

    def _initialize_redis(self):
        """Initialize Redis connection"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available. Install with: pip install redis")
            return

        try:
            import os
            # Get Redis host from environment (for Docker) or default to localhost
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', '6379'))

            # Try to connect to Redis
            self._redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=0,
                decode_responses=False,  # We'll handle serialization
                socket_connect_timeout=2,
                socket_timeout=2
            )

            # Test connection
            self._redis_client.ping()
            self._enabled = True
            logger.info("Redis cache enabled and connected")

        except (redis.ConnectionError, Exception) as e:
            logger.warning(f"Redis connection failed: {e}. Running without cache.")
            self._redis_client = None
            self._enabled = False

    def is_enabled(self) -> bool:
        """Check if cache is enabled"""
        return self._enabled

    # ========================================
    # Core Cache Operations
    # ========================================

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self._enabled:
            return None

        try:
            value = self._redis_client.get(key)
            if value:
                # Deserialize
                return pickle.loads(value)
            return None

        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
        """
        if not self._enabled:
            return

        try:
            # Serialize
            serialized = pickle.dumps(value)

            if ttl:
                self._redis_client.setex(key, ttl, serialized)
            else:
                self._redis_client.set(key, serialized)

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")

    def delete(self, key: str):
        """Delete key from cache"""
        if not self._enabled:
            return

        try:
            self._redis_client.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")

    def clear_pattern(self, pattern: str):
        """
        Clear all keys matching pattern

        Args:
            pattern: Key pattern (e.g., "ohlcv:RELIANCE:*")
        """
        if not self._enabled:
            return

        try:
            keys = self._redis_client.keys(pattern)
            if keys:
                self._redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} keys matching {pattern}")
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")

    # ========================================
    # Domain-Specific Cache Operations
    # ========================================

    def get_ohlcv(self, symbol: str, timeframe: str,
                  start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """
        Get OHLCV data from cache

        Args:
            symbol: Stock symbol
            timeframe: Timeframe
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame or None
        """
        key = self._make_ohlcv_key(symbol, timeframe, start_date, end_date)
        return self.get(key)

    def set_ohlcv(self, symbol: str, timeframe: str,
                  start_date: datetime, end_date: datetime, data: pd.DataFrame):
        """Cache OHLCV data"""
        key = self._make_ohlcv_key(symbol, timeframe, start_date, end_date)
        ttl_key = f'ohlcv_{timeframe}'
        ttl = self.TTL_CONFIG.get(ttl_key, 3600)
        self.set(key, data, ttl)

    def get_indicator(self, indicator_name: str, symbol: str,
                     timeframe: str, params: Dict[str, Any]) -> Optional[Any]:
        """Get cached indicator result"""
        key = self._make_indicator_key(indicator_name, symbol, timeframe, params)
        return self.get(key)

    def set_indicator(self, indicator_name: str, symbol: str,
                     timeframe: str, params: Dict[str, Any], result: Any):
        """Cache indicator result"""
        key = self._make_indicator_key(indicator_name, symbol, timeframe, params)
        ttl = self.TTL_CONFIG.get('indicator', 300)
        self.set(key, result, ttl)

    def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached quote"""
        key = f"quote:{symbol}"
        return self.get(key)

    def set_quote(self, symbol: str, quote: Dict[str, Any]):
        """Cache quote"""
        key = f"quote:{symbol}"
        ttl = self.TTL_CONFIG.get('quote', 5)
        self.set(key, quote, ttl)

    # ========================================
    # Helper Methods
    # ========================================

    def _make_ohlcv_key(self, symbol: str, timeframe: str,
                       start_date: datetime, end_date: datetime) -> str:
        """Generate cache key for OHLCV data"""
        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')
        return f"ohlcv:{symbol}:{timeframe}:{start_str}:{end_str}"

    def _make_indicator_key(self, indicator_name: str, symbol: str,
                           timeframe: str, params: Dict[str, Any]) -> str:
        """Generate cache key for indicator"""
        params_str = json.dumps(params, sort_keys=True)
        return f"indicator:{indicator_name}:{symbol}:{timeframe}:{params_str}"

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self._enabled:
            return {'enabled': False}

        try:
            info = self._redis_client.info()
            return {
                'enabled': True,
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', '0'),
                'keys': self._redis_client.dbsize(),
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'enabled': False, 'error': str(e)}


# ========================================
# Convenience Functions
# ========================================

_global_cache: Optional[CacheManager] = None


def get_cache() -> CacheManager:
    """Get global cache instance"""
    global _global_cache

    if _global_cache is None:
        _global_cache = CacheManager()

    return _global_cache


# ========================================
# Cache Decorator
# ========================================

def cached(ttl: Optional[int] = None, key_prefix: str = "func"):
    """
    Decorator for caching function results

    Args:
        ttl: Time to live in seconds
        key_prefix: Key prefix for cache
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache = get_cache()

            if not cache.is_enabled():
                # Cache not available, execute function
                return func(*args, **kwargs)

            # Generate cache key from function name and args
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result

            # Cache miss, execute function
            logger.debug(f"Cache miss for {cache_key}")
            result = func(*args, **kwargs)

            # Store in cache
            cache.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator
