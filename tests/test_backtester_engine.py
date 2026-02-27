from app.backtester.engine import Backtester  # module does not exist yet -> RED

# Two deterministic candles:
#   Day 1 close = 100  → buy: 1000 / 100 = 10.0 shares
#   Day 2 close = 110  → sell: 10.0 × 110 = 1100.0
#   Return = (1100 - 1000) / 1000 = 0.10  →  10 %
CANDLES = [
    {"timestamp": "2024-01-01", "open": 99.0,  "high": 101.0, "low": 98.0,  "close": 100.0, "volume": 1_000_000},
    {"timestamp": "2024-01-02", "open": 100.5, "high": 111.0, "low": 100.0, "close": 110.0, "volume": 1_200_000},
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
