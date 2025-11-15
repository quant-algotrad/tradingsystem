"""
Cache Module
High-performance Redis caching layer for market data

Features:
- Redis-based caching with automatic TTL
- Cache-Aside pattern
- Domain-specific cache operations
- Graceful degradation if Redis unavailable
"""

from .cache_manager import (
    CacheManager,
    get_cache,
    cached,
    REDIS_AVAILABLE
)

__all__ = [
    'CacheManager',
    'get_cache',
    'cached',
    'REDIS_AVAILABLE'
]

__version__ = '1.0.0'
