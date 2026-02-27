"""
Tests for execution.rebalance_policy.RebalancePolicy

Contract
--------
RebalancePolicy(interval: int)
    interval must be > 0 → ValueError otherwise

    should_rebalance(step: int) -> bool
        Returns True when step % interval == 0
        Stateless, deterministic, no mutation
"""

import pytest

from execution.rebalance_policy import RebalancePolicy


# ===========================================================================
# Part 1 — Validation
# ===========================================================================

def test_interval_zero_raises():
    with pytest.raises(ValueError):
        RebalancePolicy(interval=0)


def test_interval_negative_raises():
    with pytest.raises(ValueError):
        RebalancePolicy(interval=-1)


def test_interval_negative_large_raises():
    with pytest.raises(ValueError):
        RebalancePolicy(interval=-100)


def test_interval_one_is_valid():
    p = RebalancePolicy(interval=1)
    assert p.interval == 1


def test_interval_stored():
    p = RebalancePolicy(interval=5)
    assert p.interval == 5


# ===========================================================================
# Part 2 — interval=5 triggers at 0, 5, 10, 15
# ===========================================================================

def test_interval5_triggers_at_step_0():
    p = RebalancePolicy(interval=5)
    assert p.should_rebalance(0) is True


def test_interval5_triggers_at_step_5():
    p = RebalancePolicy(interval=5)
    assert p.should_rebalance(5) is True


def test_interval5_triggers_at_step_10():
    p = RebalancePolicy(interval=5)
    assert p.should_rebalance(10) is True


def test_interval5_triggers_at_step_15():
    p = RebalancePolicy(interval=5)
    assert p.should_rebalance(15) is True


def test_interval5_does_not_trigger_at_step_1():
    p = RebalancePolicy(interval=5)
    assert p.should_rebalance(1) is False


def test_interval5_does_not_trigger_at_step_2():
    p = RebalancePolicy(interval=5)
    assert p.should_rebalance(2) is False


def test_interval5_does_not_trigger_at_step_3():
    p = RebalancePolicy(interval=5)
    assert p.should_rebalance(3) is False


def test_interval5_does_not_trigger_at_step_4():
    p = RebalancePolicy(interval=5)
    assert p.should_rebalance(4) is False


def test_interval5_does_not_trigger_at_step_6():
    p = RebalancePolicy(interval=5)
    assert p.should_rebalance(6) is False


def test_interval5_does_not_trigger_at_step_9():
    p = RebalancePolicy(interval=5)
    assert p.should_rebalance(9) is False


# ===========================================================================
# Part 3 — interval=1 triggers every step
# ===========================================================================

def test_interval1_triggers_every_step():
    p = RebalancePolicy(interval=1)
    for step in range(20):
        assert p.should_rebalance(step) is True


# ===========================================================================
# Part 4 — Large interval triggers only at multiples
# ===========================================================================

def test_interval100_triggers_at_0():
    p = RebalancePolicy(interval=100)
    assert p.should_rebalance(0) is True


def test_interval100_triggers_at_100():
    p = RebalancePolicy(interval=100)
    assert p.should_rebalance(100) is True


def test_interval100_does_not_trigger_at_50():
    p = RebalancePolicy(interval=100)
    assert p.should_rebalance(50) is False


def test_interval100_does_not_trigger_at_99():
    p = RebalancePolicy(interval=100)
    assert p.should_rebalance(99) is False


# ===========================================================================
# Part 5 — Deterministic
# ===========================================================================

def test_deterministic_same_step_same_result():
    p = RebalancePolicy(interval=5)
    r1 = p.should_rebalance(10)
    r2 = p.should_rebalance(10)
    assert r1 == r2


def test_deterministic_no_state_between_calls():
    """Calling should_rebalance multiple times must not change future results."""
    p = RebalancePolicy(interval=5)
    for _ in range(100):
        p.should_rebalance(3)  # never triggers
    assert p.should_rebalance(5) is True


# ===========================================================================
# Part 6 — No mutation
# ===========================================================================

def test_should_rebalance_does_not_mutate_step():
    """step is an int (immutable), but we verify the policy doesn't store it."""
    p = RebalancePolicy(interval=5)
    step = 10
    p.should_rebalance(step)
    assert step == 10  # trivially true, but documents intent
