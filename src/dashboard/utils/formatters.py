"""
Formatting Utilities
Format numbers, dates, percentages, etc. for display
"""

from typing import Union, Optional
from datetime import datetime, timedelta


def format_currency(value: Union[int, float], symbol: str = "₹") -> str:
    """
    Format number as currency

    Args:
        value: Numeric value
        symbol: Currency symbol (default: ₹)

    Returns:
        Formatted string like "₹2,450.50"
    """
    try:
        if value >= 0:
            return f"{symbol}{value:,.2f}"
        else:
            return f"-{symbol}{abs(value):,.2f}"
    except:
        return f"{symbol}0.00"


def format_percentage(value: Union[int, float], decimals: int = 2, show_sign: bool = True) -> str:
    """
    Format number as percentage

    Args:
        value: Numeric value (e.g., 1.23 for 1.23%)
        decimals: Number of decimal places
        show_sign: Whether to show +/- sign

    Returns:
        Formatted string like "+1.23%"
    """
    try:
        if show_sign:
            return f"{value:+.{decimals}f}%"
        else:
            return f"{value:.{decimals}f}%"
    except:
        return "0.00%"


def format_number(value: Union[int, float], decimals: int = 2, compact: bool = False) -> str:
    """
    Format number with thousand separators

    Args:
        value: Numeric value
        decimals: Number of decimal places
        compact: Use compact notation (K, M, B)

    Returns:
        Formatted string like "2,450.50" or "2.45K"
    """
    try:
        if compact:
            if abs(value) >= 1_000_000_000:
                return f"{value/1_000_000_000:.{decimals}f}B"
            elif abs(value) >= 1_000_000:
                return f"{value/1_000_000:.{decimals}f}M"
            elif abs(value) >= 1_000:
                return f"{value/1_000:.{decimals}f}K"
            else:
                return f"{value:.{decimals}f}"
        else:
            return f"{value:,.{decimals}f}"
    except:
        return "0"


def format_duration(seconds: int) -> str:
    """
    Format duration in human-readable format

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string like "2h 35m" or "3 days"
    """
    try:
        td = timedelta(seconds=seconds)
        days = td.days
        hours = td.seconds // 3600
        minutes = (td.seconds % 3600) // 60

        if days > 0:
            return f"{days} day{'s' if days > 1 else ''}"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m"
        else:
            return f"{seconds}s"
    except:
        return "0s"


def format_timestamp(dt: Union[datetime, str], format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime as string

    Args:
        dt: Datetime object or string
        format_str: Format string

    Returns:
        Formatted datetime string
    """
    try:
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)
        return dt.strftime(format_str)
    except:
        return str(dt)


def format_time_ago(dt: Union[datetime, str]) -> str:
    """
    Format datetime as "time ago" string

    Args:
        dt: Datetime object or string

    Returns:
        String like "2 hours ago", "3 days ago"
    """
    try:
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)

        now = datetime.now()
        diff = now - dt

        seconds = diff.total_seconds()

        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            days = int(seconds / 86400)
            return f"{days} day{'s' if days > 1 else ''} ago"
    except:
        return "unknown"


def color_pnl(value: Union[int, float]) -> str:
    """
    Get color for P&L value

    Args:
        value: P&L value

    Returns:
        CSS color class or HTML color
    """
    if value > 0:
        return "profit"  # Green
    elif value < 0:
        return "loss"    # Red
    else:
        return "neutral" # Gray


def format_signal(signal: str) -> str:
    """
    Format signal with emoji

    Args:
        signal: Signal type (BUY, SELL, HOLD)

    Returns:
        Formatted string with emoji
    """
    signal_map = {
        'BUY': '🟢 BUY',
        'SELL': '🔴 SELL',
        'HOLD': '🟡 HOLD',
        'NEUTRAL': '⚪ NEUTRAL'
    }
    return signal_map.get(signal.upper(), signal)


def format_confidence(confidence: float) -> str:
    """
    Format confidence score with visual indicator

    Args:
        confidence: Confidence score (0-100)

    Returns:
        Formatted string with emoji indicator
    """
    if confidence >= 75:
        return f"🟢 {confidence:.1f}% (High)"
    elif confidence >= 60:
        return f"🟡 {confidence:.1f}% (Medium)"
    else:
        return f"🔴 {confidence:.1f}% (Low)"


def format_status(status: str) -> str:
    """
    Format status with emoji

    Args:
        status: Status string

    Returns:
        Formatted string with emoji
    """
    status_map = {
        'RUNNING': '🟢 Running',
        'STOPPED': '🔴 Stopped',
        'WARNING': '🟡 Warning',
        'ERROR': '🔴 Error',
        'PENDING': '🟡 Pending',
        'COMPLETED': '🟢 Completed',
        'FAILED': '🔴 Failed'
    }
    return status_map.get(status.upper(), status)


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate long text

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_risk_reward(ratio: float) -> str:
    """
    Format risk-reward ratio

    Args:
        ratio: Risk-reward ratio

    Returns:
        Formatted string like "2.5:1"
    """
    return f"{ratio:.1f}:1"


def get_trend_emoji(current: float, previous: float) -> str:
    """
    Get trend emoji based on comparison

    Args:
        current: Current value
        previous: Previous value

    Returns:
        Emoji (↑, ↓, →)
    """
    if current > previous:
        return "↑"
    elif current < previous:
        return "↓"
    else:
        return "→"


def format_trade_type(trade_type: str) -> str:
    """
    Format trade type with emoji

    Args:
        trade_type: Trade type (BUY, SELL, LONG, SHORT)

    Returns:
        Formatted string
    """
    type_map = {
        'BUY': '📈 BUY',
        'SELL': '📉 SELL',
        'LONG': '📈 LONG',
        'SHORT': '📉 SHORT'
    }
    return type_map.get(trade_type.upper(), trade_type)
