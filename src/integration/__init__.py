"""
Integration Module
Complete trading workflow integration with all components

Components:
- Trading Pipeline: End-to-end trading flow
- Combines: Data Fetching + Caching + Indicators + Signals + Decisions

Patterns:
- Facade Pattern: Simplifies complex workflows
- Pipeline Pattern: Sequential data processing
- Caching: Performance optimization

Usage:
    from src.integration import evaluate_symbol_quick, scan_for_opportunities

    # Quick symbol evaluation
    decision = evaluate_symbol_quick("RELIANCE.NS")

    # Scan for opportunities
    opportunities = scan_for_opportunities(["RELIANCE.NS", "TCS.NS", "INFY.NS"])
"""

from .trading_pipeline import (
    TradingPipeline,
    get_trading_pipeline,
    evaluate_symbol_quick,
    scan_for_opportunities
)

__all__ = [
    'TradingPipeline',
    'get_trading_pipeline',
    'evaluate_symbol_quick',
    'scan_for_opportunities'
]

__version__ = '1.0.0'
