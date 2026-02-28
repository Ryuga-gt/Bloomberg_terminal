"""
RED tests for ai.evaluator.StrategyEvaluator contract.

Contract:
  - Class StrategyEvaluator
  - Method evaluate(strategy_class, candles: list[dict]) -> dict
  - Must return:
        final_equity
        sharpe_ratio
        calmar_ratio
        fitness_score

  fitness_score := sharpe_ratio - (abs(max_drawdown_pct) / 100)
"""

import math

from ai.evaluator import StrategyEvaluator

# ---------------------------------------------------------------------------
# Shared candle fixtures
# ---------------------------------------------------------------------------

# Rising: 100 -> 110 -> 120
CANDLES_RISING = [
    {"timestamp": "2024-01-01", "open": 99.0,  "high": 101.0, "low": 98.0,  "close": 100.0, "volume": 1_000_000},
    {"timestamp": "2024-01-02", "open": 100.5, "high": 111.0, "low": 100.0, "close": 110.0, "volume": 1_200_000},
    {"timestamp": "2024-01-03", "open": 105.0, "high": 121.0, "low": 104.5, "close": 120.0, "volume": 1_300_000},
]

# With drawdown: 100 -> 120 -> 90 -> 130
CANDLES_DRAWDOWN = [
    {"timestamp": "2024-01-01", "open": 99.0,  "high": 101.0, "low": 98.0,  "close": 100.0, "volume": 1_000_000},
    {"timestamp": "2024-01-02", "open": 100.0, "high": 121.0, "low": 99.5,  "close": 120.0, "volume": 1_100_000},
    {"timestamp": "2024-01-03", "open": 120.0, "high": 121.0, "low": 89.0,  "close": 90.0,  "volume": 1_500_000},
    {"timestamp": "2024-01-04", "open": 90.0,  "high": 131.0, "low": 89.5,  "close": 130.0, "volume": 1_200_000},
]

# Flat: no movement
CANDLES_FLAT = [
    {"timestamp": "2024-01-01", "open": 99.0, "high": 101.0, "low": 98.0, "close": 100.0, "volume": 1_000_000},
    {"timestamp": "2024-01-02", "open": 99.0, "high": 101.0, "low": 98.0, "close": 100.0, "volume": 1_000_000},
]


# ---------------------------------------------------------------------------
# Minimal strategy classes used as fixtures
# ---------------------------------------------------------------------------

class AlwaysLongStrategy:
    """BUY on candle 0, HOLD all remaining — stays fully invested."""
    def generate(self, candles: list[dict]) -> list[str]:
        return ["BUY"] + ["HOLD"] * (len(candles) - 1)


class AlwaysFlatStrategy:
    """Never buys — stays in cash the whole time."""
    def generate(self, candles: list[dict]) -> list[str]:
        return ["HOLD"] * len(candles)


# ---------------------------------------------------------------------------
# StrategyEvaluator instantiation
# ---------------------------------------------------------------------------

def test_strategy_evaluator_is_instantiable():
    ev = StrategyEvaluator()
    assert ev is not None


# ---------------------------------------------------------------------------
# evaluate() returns a dict
# ---------------------------------------------------------------------------

def test_evaluate_returns_dict():
    ev = StrategyEvaluator()
    result = ev.evaluate(AlwaysLongStrategy, CANDLES_RISING)
    assert isinstance(result, dict), (
        f"evaluate() must return a dict, got {type(result)}"
    )


# ---------------------------------------------------------------------------
# Required keys are present
# ---------------------------------------------------------------------------

def test_evaluate_result_has_final_equity_key():
    ev = StrategyEvaluator()
    result = ev.evaluate(AlwaysLongStrategy, CANDLES_RISING)
    assert "final_equity" in result


def test_evaluate_result_has_sharpe_ratio_key():
    ev = StrategyEvaluator()
    result = ev.evaluate(AlwaysLongStrategy, CANDLES_RISING)
    assert "sharpe_ratio" in result


def test_evaluate_result_has_calmar_ratio_key():
    ev = StrategyEvaluator()
    result = ev.evaluate(AlwaysLongStrategy, CANDLES_RISING)
    assert "calmar_ratio" in result


def test_evaluate_result_has_fitness_score_key():
    ev = StrategyEvaluator()
    result = ev.evaluate(AlwaysLongStrategy, CANDLES_RISING)
    assert "fitness_score" in result


# ---------------------------------------------------------------------------
# final_equity correctness
# AlwaysLongStrategy on CANDLES_RISING:
#   BUY @ 100 → shares = 1000/100 = 10
#   HOLD @ 110, HOLD @ 120
#   exit at last close → 10 * 120 = 1200.0
# ---------------------------------------------------------------------------

def test_evaluate_final_equity_always_long_rising():
    ev = StrategyEvaluator()
    result = ev.evaluate(AlwaysLongStrategy, CANDLES_RISING)
    assert result["final_equity"] == 1200.0


# ---------------------------------------------------------------------------
# fitness_score definition:
#   fitness_score = sharpe_ratio - (abs(max_drawdown_pct) / 100)
# ---------------------------------------------------------------------------

def test_fitness_score_formula_rising():
    ev = StrategyEvaluator()
    result = ev.evaluate(AlwaysLongStrategy, CANDLES_RISING)
    sharpe = result["sharpe_ratio"]
    # monotonic rising → no drawdown → max_drawdown_pct = 0.0
    expected_fitness = sharpe - 0.0
    assert result["fitness_score"] == expected_fitness


def test_fitness_score_formula_with_drawdown():
    """
    AlwaysLongStrategy on CANDLES_DRAWDOWN:
      equity_curve = [1000, 1200, 900, 1300]
      max_drawdown_pct = (900 - 1200) / 1200 * 100 = -25.0
      fitness_score = sharpe_ratio - (abs(-25.0) / 100)
                    = sharpe_ratio - 0.25
    """
    ev = StrategyEvaluator()
    result = ev.evaluate(AlwaysLongStrategy, CANDLES_DRAWDOWN)
    sharpe = result["sharpe_ratio"]
    # max_drawdown_pct = -25.0, so abs/100 = 0.25
    expected_fitness = sharpe - 0.25
    assert abs(result["fitness_score"] - expected_fitness) < 1e-9


def test_fitness_score_is_float():
    ev = StrategyEvaluator()
    result = ev.evaluate(AlwaysLongStrategy, CANDLES_RISING)
    assert isinstance(result["fitness_score"], float)


# ---------------------------------------------------------------------------
# Input candles must NOT be mutated
# ---------------------------------------------------------------------------

def test_evaluate_does_not_mutate_candles():
    candles_copy = [dict(c) for c in CANDLES_RISING]
    original_closes = [c["close"] for c in candles_copy]

    ev = StrategyEvaluator()
    ev.evaluate(AlwaysLongStrategy, candles_copy)

    for i, c in enumerate(candles_copy):
        assert c["close"] == original_closes[i], (
            f"Candle {i} close was mutated: expected {original_closes[i]}, got {c['close']}"
        )


def test_evaluate_does_not_mutate_candle_keys():
    candles_copy = [dict(c) for c in CANDLES_RISING]
    original_keys_per_candle = [set(c.keys()) for c in candles_copy]

    ev = StrategyEvaluator()
    ev.evaluate(AlwaysLongStrategy, candles_copy)

    for i, c in enumerate(candles_copy):
        assert set(c.keys()) == original_keys_per_candle[i], (
            f"Candle {i} keys were mutated"
        )


# ---------------------------------------------------------------------------
# Determinism — same inputs must yield same outputs
# ---------------------------------------------------------------------------

def test_evaluate_is_deterministic():
    ev = StrategyEvaluator()
    result1 = ev.evaluate(AlwaysLongStrategy, CANDLES_RISING)
    result2 = ev.evaluate(AlwaysLongStrategy, CANDLES_RISING)
    assert result1["final_equity"] == result2["final_equity"]
    assert result1["sharpe_ratio"] == result2["sharpe_ratio"]
    assert result1["fitness_score"] == result2["fitness_score"]


# ---------------------------------------------------------------------------
# evaluate() accepts a class (not an instance) and instantiates it
# ---------------------------------------------------------------------------

def test_evaluate_accepts_class_not_instance():
    ev = StrategyEvaluator()
    # Passing the class itself, not AlwaysLongStrategy()
    result = ev.evaluate(AlwaysLongStrategy, CANDLES_RISING)
    assert "final_equity" in result


# ---------------------------------------------------------------------------
# sharpe_ratio and calmar_ratio values are consistent with Backtester output
# (regression: evaluator must delegate correctly, not recompute differently)
#
# AlwaysLongStrategy on CANDLES_DRAWDOWN:
#   equity_curve  = [1000, 1200, 900, 1300]
#   return_pct    = 30.0
#   max_drawdown  = -25.0
#   calmar_ratio  = 30.0 / 25.0 = 1.2
# ---------------------------------------------------------------------------

def test_evaluate_calmar_ratio_with_drawdown():
    ev = StrategyEvaluator()
    result = ev.evaluate(AlwaysLongStrategy, CANDLES_DRAWDOWN)
    # final_equity = 10 shares * 130 = 1300, return_pct = 30.0, drawdown = -25.0
    assert result["final_equity"] == 1300.0
    assert abs(result["calmar_ratio"] - 1.2) < 1e-9


def test_evaluate_sharpe_ratio_zero_for_flat_market():
    ev = StrategyEvaluator()
    result = ev.evaluate(AlwaysLongStrategy, CANDLES_FLAT)
    # HOLD after BUY @ 100, price stays 100 → zero volatility → sharpe = 0.0
    assert result["sharpe_ratio"] == 0.0
