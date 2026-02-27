import math
import pytest

from app.backtester.engine import Backtester

# Two deterministic candles:
#   Day 1 close = 100  → buy: 1000 / 100 = 10.0 shares
#   Day 2 close = 110  → sell: 10.0 × 110 = 1100.0
#   Return = (1100 - 1000) / 1000 = 0.10  →  10 %
CANDLES = [
    {"timestamp": "2024-01-01", "open": 99.0,  "high": 101.0, "low": 98.0,  "close": 100.0, "volume": 1_000_000},
    {"timestamp": "2024-01-02", "open": 100.5, "high": 111.0, "low": 100.0, "close": 110.0, "volume": 1_200_000},
]

# Three deterministic candles for equity_curve test:
#   shares = 1000 / 100 = 10.0
#   curve  = [10.0×100, 10.0×105, 10.0×110] = [1000.0, 1050.0, 1100.0]
CANDLES_3 = [
    {"timestamp": "2024-01-01", "open": 99.0,  "high": 101.0, "low": 98.0,  "close": 100.0, "volume": 1_000_000},
    {"timestamp": "2024-01-02", "open": 100.0, "high": 106.0, "low": 99.5,  "close": 105.0, "volume": 1_100_000},
    {"timestamp": "2024-01-03", "open": 105.0, "high": 111.0, "low": 104.5, "close": 110.0, "volume": 1_200_000},
]

# Four candles with a drawdown for max_drawdown_pct test:
#   shares = 1000 / 100 = 10.0
#   equity_curve = [1000.0, 1200.0, 900.0, 1300.0]
#   running peak: [1000.0, 1200.0, 1200.0, 1300.0]
#   drawdowns:    [0,      0,      (900-1200)/1200, 0] = [0, 0, -0.25, 0]
#   max_drawdown_pct = -25.0
CANDLES_4 = [
    {"timestamp": "2024-01-01", "open": 99.0,  "high": 101.0, "low": 98.0,  "close": 100.0, "volume": 1_000_000},
    {"timestamp": "2024-01-02", "open": 100.0, "high": 121.0, "low": 99.5,  "close": 120.0, "volume": 1_100_000},
    {"timestamp": "2024-01-03", "open": 120.0, "high": 121.0, "low": 89.0,  "close": 90.0,  "volume": 1_500_000},
    {"timestamp": "2024-01-04", "open": 90.0,  "high": 131.0, "low": 89.5,  "close": 130.0, "volume": 1_200_000},
]


def test_backtester_buy_and_hold_final_equity():
    bt = Backtester(initial_cash=1000)
    result = bt.run(CANDLES, mode="buy_and_hold")
    assert result["final_equity"] == 1100.0


def test_backtester_buy_and_hold_return_pct():
    bt = Backtester(initial_cash=1000)
    result = bt.run(CANDLES, mode="buy_and_hold")
    assert result["return_pct"] == 10.0


def test_backtester_requires_at_least_two_candles():
    bt = Backtester(initial_cash=1000)
    try:
        bt.run([CANDLES[0]], mode="buy_and_hold")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_backtester_initial_cash_preserved_with_no_candles_raises():
    bt = Backtester(initial_cash=500)
    try:
        bt.run([], mode="buy_and_hold")
        assert False, "expected ValueError"
    except ValueError:
        pass


# ---------------------------------------------------------------------------
# equity_curve — RED: run() does not return equity_curve key yet
# ---------------------------------------------------------------------------

def test_backtester_equity_curve_length():
    bt = Backtester(initial_cash=1000)
    result = bt.run(CANDLES_3, mode="buy_and_hold")
    # KeyError: 'equity_curve' — feature missing -> RED
    assert len(result["equity_curve"]) == 3


def test_backtester_equity_curve_starts_at_initial_cash():
    bt = Backtester(initial_cash=1000)
    result = bt.run(CANDLES_3, mode="buy_and_hold")
    assert result["equity_curve"][0] == 1000.0


def test_backtester_equity_curve_ends_at_final_equity():
    bt = Backtester(initial_cash=1000)
    result = bt.run(CANDLES_3, mode="buy_and_hold")
    assert result["equity_curve"][-1] == 1100.0


# ---------------------------------------------------------------------------
# max_drawdown_pct — RED: run() does not return max_drawdown_pct key yet
# ---------------------------------------------------------------------------

def test_backtester_max_drawdown_pct():
    bt = Backtester(initial_cash=1000)
    result = bt.run(CANDLES_4, mode="buy_and_hold")
    # KeyError: 'max_drawdown_pct' — feature missing -> RED
    # peak=1200, trough=900 → (900-1200)/1200 * 100 = -25.0
    assert result["max_drawdown_pct"] == -25.0


def test_backtester_max_drawdown_pct_zero_when_monotonic():
    bt = Backtester(initial_cash=1000)
    result = bt.run(CANDLES_3, mode="buy_and_hold")
    # equity_curve = [1000, 1050, 1100] — never drops → drawdown = 0.0
    assert result["max_drawdown_pct"] == 0.0


# ---------------------------------------------------------------------------
# transaction_cost_pct + slippage_pct
# RED: run() does not accept these kwargs yet →
#      TypeError: run() got an unexpected keyword argument 'transaction_cost_pct'
#
# Formula (same arithmetic the implementation must follow):
#   effective_buy  = close[0] * (1 + slippage_pct / 100)
#   cash_after_entry_cost = initial_cash * (1 - transaction_cost_pct / 100)
#   shares = cash_after_entry_cost / effective_buy
#   effective_sell = close[-1] * (1 - slippage_pct / 100)
#   gross_exit     = shares * effective_sell
#   final_equity   = gross_exit * (1 - transaction_cost_pct / 100)
# ---------------------------------------------------------------------------

def test_backtester_transaction_cost_and_slippage_reduce_final_equity():
    initial_cash        = 1000.0
    transaction_cost_pct = 1.0
    slippage_pct         = 1.0
    raw_buy_price        = CANDLES[0]["close"]   # 100.0
    raw_sell_price       = CANDLES[-1]["close"]  # 110.0

    # Expected — computed with same formula the implementation must use
    effective_buy        = raw_buy_price  * (1 + slippage_pct / 100)          # 101.0
    cash_after_entry_cost = initial_cash  * (1 - transaction_cost_pct / 100)  # 990.0
    shares               = cash_after_entry_cost / effective_buy               # 990/101
    effective_sell       = raw_sell_price * (1 - slippage_pct / 100)          # 108.9
    gross_exit           = shares * effective_sell
    expected_final_equity = gross_exit * (1 - transaction_cost_pct / 100)

    bt = Backtester(initial_cash=initial_cash)
    result = bt.run(
        CANDLES,
        mode="buy_and_hold",
        transaction_cost_pct=transaction_cost_pct,
        slippage_pct=slippage_pct,
    )
    assert result["final_equity"] == expected_final_equity


def test_backtester_zero_costs_matches_no_cost_result():
    """Passing explicit zeros must reproduce the original no-cost behaviour."""
    bt_plain = Backtester(initial_cash=1000)
    bt_zeros = Backtester(initial_cash=1000)
    plain  = bt_plain.run(CANDLES, mode="buy_and_hold")
    zeroed = bt_zeros.run(
        CANDLES,
        mode="buy_and_hold",
        transaction_cost_pct=0.0,
        slippage_pct=0.0,
    )
    assert zeroed["final_equity"] == plain["final_equity"]


# ---------------------------------------------------------------------------
# returns_series
# RED: run() does not return returns_series key yet →
#      KeyError: 'returns_series'
#
# Formula:
#   returns[0]   = 0.0  (base period, no prior)
#   returns[i]   = (equity[i] - equity[i-1]) / equity[i-1]   for i >= 1
#
# For CANDLES_3 equity = [1000.0, 1050.0, 1100.0]:
#   returns[0] = 0.0
#   returns[1] = (1050 - 1000) / 1000 = 0.05           (exact)
#   returns[2] = (1100 - 1050) / 1050 = 1/21 ≈ 0.047619 (approx)
# ---------------------------------------------------------------------------

def test_returns_series_length_matches_equity_curve():
    bt = Backtester(initial_cash=1000)
    result = bt.run(CANDLES_3, mode="buy_and_hold")
    # KeyError: 'returns_series' → RED
    assert len(result["returns_series"]) == len(result["equity_curve"])


def test_returns_series_first_element_is_zero():
    bt = Backtester(initial_cash=1000)
    result = bt.run(CANDLES_3, mode="buy_and_hold")
    assert result["returns_series"][0] == 0.0


def test_returns_series_second_element():
    bt = Backtester(initial_cash=1000)
    result = bt.run(CANDLES_3, mode="buy_and_hold")
    # (1050 - 1000) / 1000 = 0.05 — exact in IEEE 754
    assert result["returns_series"][1] == 0.05


def test_returns_series_third_element():
    bt = Backtester(initial_cash=1000)
    result = bt.run(CANDLES_3, mode="buy_and_hold")
    # (1100 - 1050) / 1050 = 1/21 — not exactly representable, use approx
    assert result["returns_series"][2] == pytest.approx(1 / 21, rel=1e-9)


# ---------------------------------------------------------------------------
# volatility_pct
# RED: run() does not return volatility_pct key yet →
#      KeyError: 'volatility_pct'
#
# Definition: sample std dev of returns_series × 100
#   mean = sum(r) / n
#   variance = sum((r - mean)²) / (n - 1)   ← Bessel-corrected
#   volatility_pct = sqrt(variance) * 100
#
# For CANDLES_3 returns = [0.0, 0.05, 1/21]:
#   All irrational in binary float → pytest.approx required
# ---------------------------------------------------------------------------

def test_volatility_pct_equals_sample_std_dev_of_returns_times_100():
    bt = Backtester(initial_cash=1000)
    result = bt.run(CANDLES_3, mode="buy_and_hold")

    # Compute expected value with same formula the implementation must use
    r = result["returns_series"]                     # [0.0, 0.05, 1/21]
    n = len(r)
    mean = sum(r) / n
    variance = sum((x - mean) ** 2 for x in r) / (n - 1)
    expected_volatility_pct = math.sqrt(variance) * 100

    # KeyError: 'volatility_pct' — feature missing → RED
    assert result["volatility_pct"] == pytest.approx(expected_volatility_pct, rel=1e-9)
