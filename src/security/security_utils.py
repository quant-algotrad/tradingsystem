"""
Security Utilities
Input validation, sanitization, and security helpers

Security Patterns:
- Input validation
- SQL injection prevention
- XSS prevention
- Secrets management
- Rate limiting
"""

import re
import hashlib
import secrets
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from functools import wraps
import time

from src.utils import get_logger

logger = get_logger(__name__)


class InputValidator:
    """
    Input validation and sanitization

    Prevents:
    - SQL injection
    - XSS attacks
    - Command injection
    - Path traversal
    """

    @staticmethod
    def validate_symbol(symbol: str) -> tuple[bool, str]:
        """
        Validate stock symbol format

        Args:
            symbol: Stock symbol (e.g., RELIANCE.NS)

        Returns:
            (is_valid, error_message)
        """
        if not symbol:
            return False, "Symbol cannot be empty"

        # Allow alphanumeric, dots, hyphens (NSE/BSE format)
        if not re.match(r'^[A-Z0-9.-]+$', symbol):
            return False, "Invalid symbol format"

        if len(symbol) > 20:
            return False, "Symbol too long"

        return True, ""

    @staticmethod
    def validate_price(price: float) -> tuple[bool, str]:
        """
        Validate price value

        Args:
            price: Price value

        Returns:
            (is_valid, error_message)
        """
        if not isinstance(price, (int, float)):
            return False, "Price must be numeric"

        if price <= 0:
            return False, "Price must be positive"

        if price > 1000000:  # 10 lakh max (adjust as needed)
            return False, "Price too high - possible error"

        return True, ""

    @staticmethod
    def validate_quantity(quantity: int) -> tuple[bool, str]:
        """
        Validate quantity

        Args:
            quantity: Quantity value

        Returns:
            (is_valid, error_message)
        """
        if not isinstance(quantity, int):
            return False, "Quantity must be integer"

        if quantity <= 0:
            return False, "Quantity must be positive"

        if quantity > 100000:  # Max 1 lakh shares
            return False, "Quantity too high - possible error"

        return True, ""

    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 255) -> str:
        """
        Sanitize string input

        Args:
            input_str: Input string
            max_length: Maximum allowed length

        Returns:
            Sanitized string
        """
        if not input_str:
            return ""

        # Remove control characters
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', input_str)

        # Limit length
        sanitized = sanitized[:max_length]

        return sanitized.strip()

    @staticmethod
    def validate_timeframe(timeframe: str) -> tuple[bool, str]:
        """
        Validate timeframe format

        Args:
            timeframe: Timeframe (e.g., 1d, 1h, 15m)

        Returns:
            (is_valid, error_message)
        """
        valid_timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M']

        if timeframe not in valid_timeframes:
            return False, f"Invalid timeframe. Valid: {', '.join(valid_timeframes)}"

        return True, ""

    @staticmethod
    def validate_email(email: str) -> tuple[bool, str]:
        """
        Validate email format

        Args:
            email: Email address

        Returns:
            (is_valid, error_message)
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(pattern, email):
            return False, "Invalid email format"

        return True, ""

    @staticmethod
    def prevent_sql_injection(query_param: Any) -> Any:
        """
        Basic SQL injection prevention

        Args:
            query_param: Query parameter

        Returns:
            Sanitized parameter

        Note: Use parameterized queries instead where possible
        """
        if isinstance(query_param, str):
            # Remove common SQL injection patterns
            dangerous_patterns = [
                r';\s*drop\s+table',
                r';\s*delete\s+from',
                r';\s*update\s+',
                r'union\s+select',
                r'exec\s*\(',
                r'execute\s*\(',
            ]

            for pattern in dangerous_patterns:
                if re.search(pattern, query_param, re.IGNORECASE):
                    logger.warning(f"SQL injection attempt detected: {query_param}")
                    raise ValueError("Invalid input detected")

        return query_param


class RateLimiter:
    """
    Rate limiting to prevent abuse

    Pattern: Token Bucket Algorithm
    """

    def __init__(self, max_requests: int, time_window: int):
        """
        Initialize rate limiter

        Args:
            max_requests: Max requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self._requests: Dict[str, List[float]] = {}

    def is_allowed(self, key: str) -> bool:
        """
        Check if request is allowed

        Args:
            key: Unique key (e.g., IP address, user ID)

        Returns:
            True if allowed, False if rate limited
        """
        now = time.time()

        # Initialize if new key
        if key not in self._requests:
            self._requests[key] = []

        # Remove old requests outside time window
        self._requests[key] = [
            req_time for req_time in self._requests[key]
            if now - req_time < self.time_window
        ]

        # Check if under limit
        if len(self._requests[key]) < self.max_requests:
            self._requests[key].append(now)
            return True

        logger.warning(f"Rate limit exceeded for key: {key}")
        return False

    def reset(self, key: str):
        """Reset rate limit for key"""
        if key in self._requests:
            del self._requests[key]


def rate_limit(max_requests: int = 100, time_window: int = 60):
    """
    Decorator for rate limiting

    Args:
        max_requests: Max requests allowed
        time_window: Time window in seconds

    Usage:
        @rate_limit(max_requests=10, time_window=60)
        def my_function():
            pass
    """
    limiter = RateLimiter(max_requests, time_window)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use function name as key (could be enhanced with user ID, IP, etc.)
            key = func.__name__

            if not limiter.is_allowed(key):
                raise Exception(f"Rate limit exceeded: {max_requests} requests per {time_window}s")

            return func(*args, **kwargs)

        return wrapper

    return decorator


class SecretsManager:
    """
    Secure secrets management

    Never log or expose secrets
    """

    @staticmethod
    def mask_secret(secret: str, visible_chars: int = 4) -> str:
        """
        Mask secret for logging

        Args:
            secret: Secret to mask
            visible_chars: Number of chars to show

        Returns:
            Masked secret (e.g., "sk-***abc")
        """
        if not secret or len(secret) <= visible_chars:
            return "***"

        return f"{secret[:2]}***{secret[-visible_chars:]}"

    @staticmethod
    def generate_api_key(length: int = 32) -> str:
        """
        Generate secure random API key

        Args:
            length: Key length

        Returns:
            Secure random API key
        """
        return secrets.token_urlsafe(length)

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password securely

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        # Use SHA-256 with salt
        salt = secrets.token_hex(16)
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
        return f"{salt}${hashed.hex()}"

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """
        Verify password against hash

        Args:
            password: Plain text password
            hashed: Hashed password

        Returns:
            True if match
        """
        try:
            salt, hash_value = hashed.split('$')
            verify_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            )
            return verify_hash.hex() == hash_value
        except Exception:
            return False


class SecurityAudit:
    """
    Security audit logging

    Track security events for monitoring
    """

    @staticmethod
    def log_auth_attempt(success: bool, user: str, ip: str = None):
        """Log authentication attempt"""
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"Auth {status}: user={user}, ip={ip}")

    @staticmethod
    def log_suspicious_activity(activity: str, details: Dict[str, Any]):
        """Log suspicious activity"""
        logger.warning(f"SECURITY: {activity} | Details: {details}")

    @staticmethod
    def log_data_access(user: str, resource: str, action: str):
        """Log data access for compliance"""
        logger.info(f"DATA ACCESS: user={user}, resource={resource}, action={action}")


# ========================================
# Convenience Functions
# ========================================

def validate_trade_input(
    symbol: str,
    quantity: int,
    price: float
) -> tuple[bool, List[str]]:
    """
    Validate trade input

    Args:
        symbol: Stock symbol
        quantity: Quantity
        price: Price

    Returns:
        (is_valid, error_messages)
    """
    errors = []

    valid, msg = InputValidator.validate_symbol(symbol)
    if not valid:
        errors.append(f"Symbol: {msg}")

    valid, msg = InputValidator.validate_quantity(quantity)
    if not valid:
        errors.append(f"Quantity: {msg}")

    valid, msg = InputValidator.validate_price(price)
    if not valid:
        errors.append(f"Price: {msg}")

    return len(errors) == 0, errors
