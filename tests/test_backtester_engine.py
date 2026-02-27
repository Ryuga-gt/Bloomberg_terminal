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
