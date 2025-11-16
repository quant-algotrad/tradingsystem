"""
Security Module
Comprehensive security utilities and helpers

Components:
- Input validation
- Rate limiting
- Secrets management
- Security audit logging

Usage:
    from src.security import InputValidator, rate_limit, SecretsManager

    # Validate input
    valid, msg = InputValidator.validate_symbol("RELIANCE.NS")

    # Rate limit
    @rate_limit(max_requests=10, time_window=60)
    def my_api_call():
        pass

    # Mask secrets
    masked = SecretsManager.mask_secret(api_key)
"""

from .security_utils import (
    InputValidator,
    RateLimiter,
    rate_limit,
    SecretsManager,
    SecurityAudit,
    validate_trade_input
)

__all__ = [
    'InputValidator',
    'RateLimiter',
    'rate_limit',
    'SecretsManager',
    'SecurityAudit',
    'validate_trade_input',
]

__version__ = '1.0.0'
