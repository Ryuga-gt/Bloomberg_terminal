"""
data.indian_symbol_mapper
=========================

Indian market symbol mapping utilities for NSE/BSE symbols to Yahoo Finance format.

Provides:
- Symbol mapping (NSE:/BSE: prefix → Yahoo Finance ticker)
- Exchange detection
- Currency detection
- Market hours and status for Indian exchanges
- Preset Indian watchlist
"""

from typing import Optional

# ---------------------------------------------------------------------------
# Try to import pytz; fall back gracefully if not installed
# ---------------------------------------------------------------------------
try:
    import pytz
    _PYTZ_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PYTZ_AVAILABLE = False

from datetime import datetime, date, timedelta

# ---------------------------------------------------------------------------
# Explicit symbol mapping: NSE/BSE prefixed → Yahoo Finance ticker
# ---------------------------------------------------------------------------

_SYMBOL_MAP: dict = {
    # Indices
    "NSE:NIFTY":      "^NSEI",
    "NSE:BANKNIFTY":  "^NSEBANK",
    "BSE:SENSEX":     "^BSESN",
    # NSE equities
    "NSE:RELIANCE":   "RELIANCE.NS",
    "NSE:HDFCBANK":   "HDFCBANK.NS",
    "NSE:TCS":        "TCS.NS",
    "NSE:INFY":       "INFY.NS",
    "NSE:SBIN":       "SBIN.NS",
    "NSE:ICICIBANK":  "ICICIBANK.NS",
    "NSE:LT":         "LT.NS",
    "NSE:ITC":        "ITC.NS",
    # BSE equities
    "BSE:RELIANCE":   "RELIANCE.BO",
    "BSE:HDFCBANK":   "HDFCBANK.BO",
}

# ---------------------------------------------------------------------------
# Indian market hours
# ---------------------------------------------------------------------------

INDIAN_MARKET_HOURS: dict = {
    "timezone": "Asia/Kolkata",
    "open":     "09:15",
    "close":    "15:30",
    "exchange": ["NSE", "BSE"],
}

# ---------------------------------------------------------------------------
# Preset Indian watchlist
# ---------------------------------------------------------------------------

INDIAN_WATCHLIST: list = [
    {"symbol": "NSE:NIFTY",     "name": "NIFTY 50",                   "yahoo": "^NSEI"},
    {"symbol": "NSE:BANKNIFTY", "name": "Bank NIFTY",                 "yahoo": "^NSEBANK"},
    {"symbol": "BSE:SENSEX",    "name": "BSE SENSEX",                 "yahoo": "^BSESN"},
    {"symbol": "NSE:RELIANCE",  "name": "Reliance Industries",        "yahoo": "RELIANCE.NS"},
    {"symbol": "NSE:HDFCBANK",  "name": "HDFC Bank",                  "yahoo": "HDFCBANK.NS"},
    {"symbol": "NSE:TCS",       "name": "Tata Consultancy Services",  "yahoo": "TCS.NS"},
    {"symbol": "NSE:INFY",      "name": "Infosys",                    "yahoo": "INFY.NS"},
    {"symbol": "NSE:ICICIBANK", "name": "ICICI Bank",                 "yahoo": "ICICIBANK.NS"},
    {"symbol": "NSE:SBIN",      "name": "State Bank of India",        "yahoo": "SBIN.NS"},
]

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def map_symbol(symbol: str) -> str:
    """
    Convert an NSE/BSE-prefixed symbol to its Yahoo Finance equivalent.

    Rules
    -----
    1. If the symbol is in the explicit map, return the mapped value.
    2. If the symbol starts with ``NSE:``, append ``.NS`` to the base ticker.
    3. If the symbol starts with ``BSE:``, append ``.BO`` to the base ticker.
    4. Otherwise return the symbol unchanged.

    Parameters
    ----------
    symbol : str
        E.g. ``"NSE:RELIANCE"``, ``"BSE:SENSEX"``, ``"AAPL"``.

    Returns
    -------
    str
        Yahoo Finance ticker string.

    Examples
    --------
    >>> map_symbol("NSE:NIFTY")
    '^NSEI'
    >>> map_symbol("NSE:WIPRO")
    'WIPRO.NS'
    >>> map_symbol("AAPL")
    'AAPL'
    """
    upper = symbol.upper()

    # Check explicit map first (case-insensitive key lookup)
    if upper in _SYMBOL_MAP:
        return _SYMBOL_MAP[upper]

    if upper.startswith("NSE:"):
        base = symbol[4:]  # preserve original case for the ticker part
        return f"{base}.NS"

    if upper.startswith("BSE:"):
        base = symbol[4:]
        return f"{base}.BO"

    return symbol


def detect_exchange(symbol: str) -> str:
    """
    Detect the exchange for a given symbol.

    Parameters
    ----------
    symbol : str
        E.g. ``"NSE:RELIANCE"``, ``"BSE:SENSEX"``, ``"AAPL"``.

    Returns
    -------
    str
        ``"NSE"``, ``"BSE"``, or ``"GLOBAL"``.
    """
    upper = symbol.upper()
    if upper.startswith("NSE:"):
        return "NSE"
    if upper.startswith("BSE:"):
        return "BSE"
    return "GLOBAL"


def get_currency(symbol: str) -> str:
    """
    Return the currency for a given symbol.

    Parameters
    ----------
    symbol : str
        Ticker symbol, optionally prefixed with ``NSE:`` or ``BSE:``.

    Returns
    -------
    str
        ``"INR"`` for Indian symbols, ``"USD"`` for all others.
    """
    if is_indian_symbol(symbol):
        return "INR"
    return "USD"


def is_indian_symbol(symbol: str) -> bool:
    """
    Return ``True`` if the symbol belongs to an Indian exchange.

    Parameters
    ----------
    symbol : str
        Ticker symbol.

    Returns
    -------
    bool
    """
    upper = symbol.upper()
    return upper.startswith("NSE:") or upper.startswith("BSE:")


def get_market_status(exchange: str = "NSE") -> dict:
    """
    Return the current market status for the given Indian exchange.

    Parameters
    ----------
    exchange : str, optional
        ``"NSE"`` or ``"BSE"``.  Default ``"NSE"``.

    Returns
    -------
    dict
        Keys: ``exchange``, ``status``, ``current_time_ist``, ``timezone``,
        and optionally ``next_open`` (when market is closed).

    Notes
    -----
    Market is open Monday–Friday 09:15–15:30 IST.
    ``pytz`` is used for timezone conversion; if it is not installed the
    function falls back to a best-effort UTC+5:30 offset calculation.
    """
    exchange = exchange.upper()

    if _PYTZ_AVAILABLE:
        ist_tz = pytz.timezone("Asia/Kolkata")
        now_ist = datetime.now(ist_tz)
    else:
        # Fallback: UTC + 5h30m
        from datetime import timezone as _tz
        utc_now = datetime.now(_tz.utc)
        ist_offset = timedelta(hours=5, minutes=30)
        now_ist = utc_now + ist_offset

    current_time_str = now_ist.strftime("%H:%M")
    current_date = now_ist.date()
    weekday = now_ist.weekday()  # 0=Monday … 6=Sunday

    open_h, open_m = 9, 15
    close_h, close_m = 15, 30

    is_weekday = weekday < 5  # Mon–Fri
    current_minutes = now_ist.hour * 60 + now_ist.minute
    open_minutes = open_h * 60 + open_m
    close_minutes = close_h * 60 + close_m

    is_open = is_weekday and open_minutes <= current_minutes < close_minutes

    result: dict = {
        "exchange":         exchange,
        "status":           "open" if is_open else "closed",
        "current_time_ist": current_time_str,
        "timezone":         "Asia/Kolkata",
    }

    if not is_open:
        # Calculate next open date/time
        next_open_date = _next_market_open_date(current_date, weekday, current_minutes, open_minutes)
        result["next_open"] = f"{next_open_date} 09:15 IST"

    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _next_market_open_date(
    current_date: date,
    weekday: int,
    current_minutes: int,
    open_minutes: int,
) -> str:
    """
    Return the next market open date as ``'YYYY-MM-DD'``.

    Parameters
    ----------
    current_date : date
    weekday : int
        0=Monday … 6=Sunday
    current_minutes : int
        Current time expressed as total minutes since midnight.
    open_minutes : int
        Market open time expressed as total minutes since midnight.
    """
    # If today is a weekday and market hasn't opened yet, open is today
    if weekday < 5 and current_minutes < open_minutes:
        return current_date.strftime("%Y-%m-%d")

    # Otherwise find the next weekday
    days_ahead = 1
    candidate = current_date + timedelta(days=days_ahead)
    while candidate.weekday() >= 5:  # skip Sat/Sun
        days_ahead += 1
        candidate = current_date + timedelta(days=days_ahead)

    return candidate.strftime("%Y-%m-%d")
