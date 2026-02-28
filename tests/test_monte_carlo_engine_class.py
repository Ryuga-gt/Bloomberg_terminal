"""
RED tests for research.monte_carlo_engine.MonteCarloEngine

Class contract:
    class MonteCarloEngine:
        __init__(self, initial_cash=1000, seed=None)

        analyze(
            self,
            returns_series=None,
            trades=None,
            mode="returns",      # "returns" | "trades" | "execution"
            simulations=1000,
            slippage_std=0.0,
            shock_std=0.0,
        ) -> dict

Output dict (identical structure for all modes):
    simulations_results  : list[dict]
    mean_sharpe          : float
    sharpe_variance      : float   (Bessel-corrected; 0.0 when simulations==1)
    mean_return_pct      : float
    probability_of_loss  : float
    worst_drawdown       : float

Each entry in simulations_results:
    final_equity      : float
    return_pct        : float
    sharpe_ratio      : float
    max_drawdown_pct  : float

Mode "returns":
    Bootstrap-sample returns_series with replacement (len(returns_series) draws).
    Identical math to Phase A monte_carlo_analysis().

Mode "trades":
    Shuffle trades WITHOUT replacement each simulation.
    Reconstruct equity from shuffled order.
    Same Sharpe/drawdown math.

Mode "execution":
    Bootstrap returns_series (same as "returns").
    For each sampled return r:
        if shock_std != 0:   r = r * gauss(1.0, shock_std)
        if slippage_std != 0: r = r - gauss(0.0, slippage_std)
    When both stds are 0.0, no gauss calls → result identical to "returns" mode.

Raises ValueError for:
    returns_series length < 2 (for returns/execution modes)
    trades length < 2           (for trades mode)
    simulations < 1
    initial_cash <= 0
    slippage_std < 0
    shock_std < 0
    unknown mode string
"""

import math
import random
import pytest

from research.monte_carlo_engine import MonteCarloEngine


# ---------------------------------------------------------------------------
# Reference implementation — mirrors the exact algorithm
# ---------------------------------------------------------------------------

def _run_sim_returns(returns_series, initial_cash, rng):
    n = len(returns_series)
    sample = rng.choices(returns_series, k=n)
    return _metrics_from_sample(sample, initial_cash)


def _run_sim_trades(trades, initial_cash, rng):
    sample = list(trades)
    rng.shuffle(sample)
    return _metrics_from_sample(sample, initial_cash)


def _run_sim_execution(returns_series, initial_cash, rng, slippage_std, shock_std):
    n = len(returns_series)
    sample = rng.choices(returns_series, k=n)
    modified = []
    for r in sample:
        if shock_std != 0.0:
            r = r * rng.gauss(1.0, shock_std)
        if slippage_std != 0.0:
            r = r - rng.gauss(0.0, slippage_std)
        modified.append(r)
    return _metrics_from_sample(modified, initial_cash)


def _metrics_from_sample(sample, initial_cash):
    eq = initial_cash
    curve = [eq]
    for r in sample:
        eq = eq * (1 + r)
        curve.append(eq)
    final_equity = curve[-1]
    return_pct   = (final_equity - initial_cash) / initial_cash * 100

    ret_series = [0.0] + list(sample)
    m = len(ret_series)
    mean_r = sum(ret_series) / m
    var_r  = sum((x - mean_r) ** 2 for x in ret_series) / (m - 1)
    std_r  = math.sqrt(var_r)
    sharpe = mean_r / std_r if std_r != 0.0 else 0.0

    peak = curve[0]
    mdd  = 0.0
    for v in curve:
        if v > peak:
            peak = v
        dd = (v - peak) / peak * 100
        if dd < mdd:
            mdd = dd
    return {"final_equity": final_equity, "return_pct": return_pct,
            "sharpe_ratio": sharpe, "max_drawdown_pct": mdd}


def _ref_analyze(mode, simulations, initial_cash=1000, seed=None,
                 returns_series=None, trades=None,
                 slippage_std=0.0, shock_std=0.0):
    rng = random.Random(seed)
    sim_results = []
    for _ in range(simulations):
        if mode == "returns":
            s = _run_sim_returns(returns_series, initial_cash, rng)
        elif mode == "trades":
            s = _run_sim_trades(trades, initial_cash, rng)
        else:  # execution
            s = _run_sim_execution(returns_series, initial_cash, rng,
                                   slippage_std, shock_std)
        sim_results.append(s)

    n = len(sim_results)
    sharpes   = [s["sharpe_ratio"]     for s in sim_results]
    returns_p = [s["return_pct"]       for s in sim_results]
    drawdowns = [s["max_drawdown_pct"] for s in sim_results]
    mean_sharpe     = sum(sharpes) / n
    sharpe_variance = (sum((x - mean_sharpe)**2 for x in sharpes) / (n - 1)
                       if n > 1 else 0.0)
    mean_return_pct     = sum(returns_p) / n
    probability_of_loss = sum(1 for r in returns_p if r < 0) / n
    worst_drawdown      = min(drawdowns)
    return {"simulations_results": sim_results, "mean_sharpe": mean_sharpe,
            "sharpe_variance": sharpe_variance, "mean_return_pct": mean_return_pct,
            "probability_of_loss": probability_of_loss, "worst_drawdown": worst_drawdown}


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

RETURNS_3  = [0.1, 0.2, -0.05]
TRADES_3   = [0.1, -0.05, 0.2]
TRADES_4   = [0.3, -0.2, 0.1, -0.05]
SEED_42    = 42
SEED_0     = 0


# ===========================================================================
# PART 1 — Instantiation
# ===========================================================================

def test_engine_is_instantiable():
    eng = MonteCarloEngine()
    assert eng is not None


def test_engine_instantiable_with_cash_and_seed():
    eng = MonteCarloEngine(initial_cash=500, seed=7)
    assert eng is not None


def test_analyze_is_callable():
    eng = MonteCarloEngine(initial_cash=1000, seed=SEED_42)
    result = eng.analyze(returns_series=RETURNS_3, mode="returns", simulations=3)
    assert isinstance(result, dict)


# ===========================================================================
# PART 2 — Phase A compatibility: mode="returns" matches monte_carlo_analysis()
# ===========================================================================

def test_returns_mode_matches_phase_a_function():
    """MonteCarloEngine.analyze(mode='returns') must produce identical output
    to the legacy monte_carlo_analysis() for the same seed and inputs."""
    from research.monte_carlo_engine import monte_carlo_analysis
    eng = MonteCarloEngine(initial_cash=1000, seed=SEED_42)
    result_class  = eng.analyze(returns_series=RETURNS_3, mode="returns", simulations=3)
    result_func   = monte_carlo_analysis(RETURNS_3, 3, initial_cash=1000, seed=SEED_42)
    assert result_class["mean_sharpe"]         == result_func["mean_sharpe"]
    assert result_class["sharpe_variance"]     == result_func["sharpe_variance"]
    assert result_class["mean_return_pct"]     == result_func["mean_return_pct"]
    assert result_class["probability_of_loss"] == result_func["probability_of_loss"]
    assert result_class["worst_drawdown"]      == result_func["worst_drawdown"]


def test_returns_mode_per_sim_matches_phase_a():
    from research.monte_carlo_engine import monte_carlo_analysis
    eng = MonteCarloEngine(initial_cash=1000, seed=SEED_42)
    rc  = eng.analyze(returns_series=RETURNS_3, mode="returns", simulations=3)
    rf  = monte_carlo_analysis(RETURNS_3, 3, initial_cash=1000, seed=SEED_42)
    for sc, sf in zip(rc["simulations_results"], rf["simulations_results"]):
        assert sc["final_equity"]     == sf["final_equity"]
        assert sc["return_pct"]       == sf["return_pct"]
        assert sc["sharpe_ratio"]     == sf["sharpe_ratio"]
        assert sc["max_drawdown_pct"] == sf["max_drawdown_pct"]


def test_returns_mode_required_keys():
    eng = MonteCarloEngine(seed=SEED_42)
    result = eng.analyze(returns_series=RETURNS_3, mode="returns", simulations=3)
    for key in ("simulations_results", "mean_sharpe", "sharpe_variance",
                "mean_return_pct", "probability_of_loss", "worst_drawdown"):
        assert key in result


def test_returns_mode_sim_count():
    eng = MonteCarloEngine(seed=SEED_42)
    result = eng.analyze(returns_series=RETURNS_3, mode="returns", simulations=5)
    assert len(result["simulations_results"]) == 5


def test_returns_mode_default_simulations_1000():
    """Default simulations=1000 must produce 1000 results."""
    eng = MonteCarloEngine(seed=1)
    result = eng.analyze(returns_series=RETURNS_3, mode="returns")
    assert len(result["simulations_results"]) == 1000


def test_returns_mode_deterministic():
    eng1 = MonteCarloEngine(initial_cash=1000, seed=SEED_42)
    eng2 = MonteCarloEngine(initial_cash=1000, seed=SEED_42)
    r1 = eng1.analyze(returns_series=RETURNS_3, mode="returns", simulations=5)
    r2 = eng2.analyze(returns_series=RETURNS_3, mode="returns", simulations=5)
    assert r1["mean_sharpe"]     == r2["mean_sharpe"]
    assert r1["mean_return_pct"] == r2["mean_return_pct"]


def test_returns_mode_matches_reference():
    ref = _ref_analyze("returns", 3, seed=SEED_42, returns_series=RETURNS_3)
    eng = MonteCarloEngine(seed=SEED_42)
    result = eng.analyze(returns_series=RETURNS_3, mode="returns", simulations=3)
    assert result["mean_sharpe"]         == pytest.approx(ref["mean_sharpe"],         rel=1e-9)
    assert result["sharpe_variance"]     == pytest.approx(ref["sharpe_variance"],     rel=1e-9)
    assert result["mean_return_pct"]     == pytest.approx(ref["mean_return_pct"],     rel=1e-9)
    assert result["probability_of_loss"] == pytest.approx(ref["probability_of_loss"], rel=1e-9)
    assert result["worst_drawdown"]      == pytest.approx(ref["worst_drawdown"],      rel=1e-9)


# ===========================================================================
# PART 3 — Mode "trades": shuffle without replacement
# ===========================================================================

def test_trades_mode_returns_dict():
    eng = MonteCarloEngine(seed=SEED_42)
    result = eng.analyze(trades=TRADES_3, mode="trades", simulations=3)
    assert isinstance(result, dict)


def test_trades_mode_required_keys():
    eng = MonteCarloEngine(seed=SEED_42)
    result = eng.analyze(trades=TRADES_3, mode="trades", simulations=3)
    for key in ("simulations_results", "mean_sharpe", "sharpe_variance",
                "mean_return_pct", "probability_of_loss", "worst_drawdown"):
        assert key in result


def test_trades_mode_sim_count():
    eng = MonteCarloEngine(seed=SEED_42)
    result = eng.analyze(trades=TRADES_3, mode="trades", simulations=4)
    assert len(result["simulations_results"]) == 4


def test_trades_mode_deterministic():
    eng1 = MonteCarloEngine(seed=SEED_42)
    eng2 = MonteCarloEngine(seed=SEED_42)
    r1 = eng1.analyze(trades=TRADES_3, mode="trades", simulations=5)
    r2 = eng2.analyze(trades=TRADES_3, mode="trades", simulations=5)
    assert r1["mean_sharpe"]     == r2["mean_sharpe"]
    assert r1["mean_return_pct"] == r2["mean_return_pct"]
    for s1, s2 in zip(r1["simulations_results"], r2["simulations_results"]):
        assert s1["final_equity"]     == s2["final_equity"]
        assert s1["max_drawdown_pct"] == s2["max_drawdown_pct"]


def test_trades_mode_matches_reference():
    ref = _ref_analyze("trades", 3, seed=SEED_42, trades=TRADES_3)
    eng = MonteCarloEngine(seed=SEED_42)
    result = eng.analyze(trades=TRADES_3, mode="trades", simulations=3)
    assert result["mean_sharpe"]     == pytest.approx(ref["mean_sharpe"],     rel=1e-9)
    assert result["mean_return_pct"] == pytest.approx(ref["mean_return_pct"], rel=1e-9)
    assert result["worst_drawdown"]  == pytest.approx(ref["worst_drawdown"],  rel=1e-9)


def test_trades_mode_per_sim_matches_reference():
    ref = _ref_analyze("trades", 3, seed=SEED_42, trades=TRADES_3)
    eng = MonteCarloEngine(seed=SEED_42)
    result = eng.analyze(trades=TRADES_3, mode="trades", simulations=3)
    for sc, sr in zip(result["simulations_results"], ref["simulations_results"]):
        assert sc["final_equity"]     == pytest.approx(sr["final_equity"],     rel=1e-9)
        assert sc["return_pct"]       == pytest.approx(sr["return_pct"],       rel=1e-9)
        assert sc["sharpe_ratio"]     == pytest.approx(sr["sharpe_ratio"],     rel=1e-9)
        assert sc["max_drawdown_pct"] == pytest.approx(sr["max_drawdown_pct"], rel=1e-9)


def test_trades_mode_same_final_equity_all_sims():
    """
    Multiplication is commutative: all shuffles of the same trades produce
    the same final_equity regardless of order.
    """
    eng = MonteCarloEngine(seed=SEED_42)
    result = eng.analyze(trades=TRADES_3, mode="trades", simulations=6)
    finals = [s["final_equity"] for s in result["simulations_results"]]
    assert all(abs(f - finals[0]) < 1e-9 for f in finals)


def test_trades_mode_drawdown_varies_across_sims():
    """
    Order DOES affect drawdown. Using 4 trades with a negative return
    that, depending on position, creates different drawdowns.
    seed=7, trades=[0.3,-0.2,0.1,-0.05]: shuffles produce different mdd.
    """
    ref = _ref_analyze("trades", 4, seed=7, trades=TRADES_4)
    eng = MonteCarloEngine(seed=7)
    result = eng.analyze(trades=TRADES_4, mode="trades", simulations=4)
    drawdowns = [s["max_drawdown_pct"] for s in result["simulations_results"]]
    # Not all drawdowns should be identical (order matters for path shape)
    assert not all(d == drawdowns[0] for d in drawdowns)


def test_trades_does_not_mutate_input():
    trades = list(TRADES_3)
    orig   = list(trades)
    eng = MonteCarloEngine(seed=SEED_42)
    eng.analyze(trades=trades, mode="trades", simulations=5)
    assert trades == orig


def test_trades_mode_bessel_variance():
    eng = MonteCarloEngine(seed=7)
    result = eng.analyze(trades=TRADES_4, mode="trades", simulations=4)
    sharpes = [s["sharpe_ratio"] for s in result["simulations_results"]]
    n = len(sharpes)
    mean = sum(sharpes) / n
    expected = sum((x - mean)**2 for x in sharpes) / (n - 1)
    assert result["sharpe_variance"] == pytest.approx(expected, rel=1e-9)


# ===========================================================================
# PART 4 — Mode "execution": bootstrap + shock + slippage
# ===========================================================================

def test_execution_mode_returns_dict():
    eng = MonteCarloEngine(seed=SEED_0)
    result = eng.analyze(returns_series=RETURNS_3, mode="execution",
                         simulations=2, slippage_std=0.01, shock_std=0.05)
    assert isinstance(result, dict)


def test_execution_mode_required_keys():
    eng = MonteCarloEngine(seed=SEED_0)
    result = eng.analyze(returns_series=RETURNS_3, mode="execution",
                         simulations=2, slippage_std=0.01, shock_std=0.05)
    for key in ("simulations_results", "mean_sharpe", "sharpe_variance",
                "mean_return_pct", "probability_of_loss", "worst_drawdown"):
        assert key in result


def test_execution_mode_sim_count():
    eng = MonteCarloEngine(seed=SEED_0)
    result = eng.analyze(returns_series=RETURNS_3, mode="execution",
                         simulations=5, slippage_std=0.01, shock_std=0.05)
    assert len(result["simulations_results"]) == 5


def test_execution_mode_deterministic():
    eng1 = MonteCarloEngine(seed=SEED_0)
    eng2 = MonteCarloEngine(seed=SEED_0)
    r1 = eng1.analyze(returns_series=RETURNS_3, mode="execution",
                      simulations=3, slippage_std=0.01, shock_std=0.05)
    r2 = eng2.analyze(returns_series=RETURNS_3, mode="execution",
                      simulations=3, slippage_std=0.01, shock_std=0.05)
    assert r1["mean_sharpe"]     == r2["mean_sharpe"]
    assert r1["mean_return_pct"] == r2["mean_return_pct"]
    for s1, s2 in zip(r1["simulations_results"], r2["simulations_results"]):
        assert s1["final_equity"] == s2["final_equity"]


def test_execution_mode_matches_reference():
    ref = _ref_analyze("execution", 2, seed=SEED_0, returns_series=RETURNS_3,
                       slippage_std=0.01, shock_std=0.05)
    eng = MonteCarloEngine(seed=SEED_0)
    result = eng.analyze(returns_series=RETURNS_3, mode="execution",
                         simulations=2, slippage_std=0.01, shock_std=0.05)
    assert result["mean_sharpe"]         == pytest.approx(ref["mean_sharpe"],         rel=1e-9)
    assert result["mean_return_pct"]     == pytest.approx(ref["mean_return_pct"],     rel=1e-9)
    assert result["probability_of_loss"] == pytest.approx(ref["probability_of_loss"], rel=1e-9)
    assert result["worst_drawdown"]      == pytest.approx(ref["worst_drawdown"],      rel=1e-9)


def test_execution_mode_per_sim_matches_reference():
    ref = _ref_analyze("execution", 2, seed=SEED_0, returns_series=RETURNS_3,
                       slippage_std=0.01, shock_std=0.05)
    eng = MonteCarloEngine(seed=SEED_0)
    result = eng.analyze(returns_series=RETURNS_3, mode="execution",
                         simulations=2, slippage_std=0.01, shock_std=0.05)
    for sc, sr in zip(result["simulations_results"], ref["simulations_results"]):
        assert sc["final_equity"]     == pytest.approx(sr["final_equity"],     rel=1e-9)
        assert sc["return_pct"]       == pytest.approx(sr["return_pct"],       rel=1e-9)
        assert sc["sharpe_ratio"]     == pytest.approx(sr["sharpe_ratio"],     rel=1e-9)
        assert sc["max_drawdown_pct"] == pytest.approx(sr["max_drawdown_pct"], rel=1e-9)


def test_execution_zero_std_matches_returns_mode():
    """
    When slippage_std=0 and shock_std=0, no gauss calls are made.
    execution mode must produce identical results to returns mode.
    """
    eng_ret = MonteCarloEngine(seed=SEED_42)
    eng_exe = MonteCarloEngine(seed=SEED_42)
    r_ret = eng_ret.analyze(returns_series=RETURNS_3, mode="returns",   simulations=5)
    r_exe = eng_exe.analyze(returns_series=RETURNS_3, mode="execution",
                            simulations=5, slippage_std=0.0, shock_std=0.0)
    assert r_ret["mean_sharpe"]         == r_exe["mean_sharpe"]
    assert r_ret["mean_return_pct"]     == r_exe["mean_return_pct"]
    assert r_ret["probability_of_loss"] == r_exe["probability_of_loss"]
    assert r_ret["worst_drawdown"]      == r_exe["worst_drawdown"]


def test_execution_nonzero_std_increases_sharpe_variance():
    """
    Adding noise (non-zero std) should not produce the same variance
    as zero-noise for a sufficiently large simulation count.
    """
    eng_base  = MonteCarloEngine(seed=SEED_42)
    eng_noisy = MonteCarloEngine(seed=SEED_42)
    r_base  = eng_base.analyze(returns_series=RETURNS_3,  mode="returns",   simulations=200)
    r_noisy = eng_noisy.analyze(returns_series=RETURNS_3, mode="execution",
                                simulations=200, slippage_std=0.05, shock_std=0.10)
    # Noisy execution should produce a different (usually higher) sharpe variance
    assert r_noisy["sharpe_variance"] != r_base["sharpe_variance"]


def test_execution_mode_does_not_mutate_returns():
    returns = list(RETURNS_3)
    orig    = list(returns)
    eng = MonteCarloEngine(seed=SEED_0)
    eng.analyze(returns_series=returns, mode="execution",
                simulations=3, slippage_std=0.01, shock_std=0.05)
    assert returns == orig


# ===========================================================================
# PART 5 — initial_cash parameter honored by engine
# ===========================================================================

def test_initial_cash_scales_final_equity_returns_mode():
    eng1k = MonteCarloEngine(initial_cash=1000, seed=SEED_42)
    eng2k = MonteCarloEngine(initial_cash=2000, seed=SEED_42)
    r1 = eng1k.analyze(returns_series=RETURNS_3, mode="returns", simulations=3)
    r2 = eng2k.analyze(returns_series=RETURNS_3, mode="returns", simulations=3)
    for s1, s2 in zip(r1["simulations_results"], r2["simulations_results"]):
        assert s2["final_equity"] == pytest.approx(s1["final_equity"] * 2, rel=1e-9)
        assert s2["return_pct"]   == pytest.approx(s1["return_pct"],        rel=1e-9)


def test_initial_cash_scales_final_equity_trades_mode():
    eng1k = MonteCarloEngine(initial_cash=1000, seed=SEED_42)
    eng2k = MonteCarloEngine(initial_cash=2000, seed=SEED_42)
    r1 = eng1k.analyze(trades=TRADES_3, mode="trades", simulations=3)
    r2 = eng2k.analyze(trades=TRADES_3, mode="trades", simulations=3)
    for s1, s2 in zip(r1["simulations_results"], r2["simulations_results"]):
        assert s2["final_equity"] == pytest.approx(s1["final_equity"] * 2, rel=1e-9)


# ===========================================================================
# PART 6 — No mutation of inputs
# ===========================================================================

def test_returns_mode_does_not_mutate_returns_series():
    returns = list(RETURNS_3)
    orig    = list(returns)
    eng = MonteCarloEngine(seed=SEED_42)
    eng.analyze(returns_series=returns, mode="returns", simulations=5)
    assert returns == orig


def test_trades_mode_does_not_mutate_trades():
    trades = list(TRADES_3)
    orig   = list(trades)
    eng = MonteCarloEngine(seed=SEED_42)
    eng.analyze(trades=trades, mode="trades", simulations=5)
    assert trades == orig


# ===========================================================================
# PART 7 — ValueError for invalid parameters
# ===========================================================================

def test_raises_for_initial_cash_zero():
    with pytest.raises(ValueError):
        MonteCarloEngine(initial_cash=0)


def test_raises_for_initial_cash_negative():
    with pytest.raises(ValueError):
        MonteCarloEngine(initial_cash=-500)


def test_raises_for_simulations_zero():
    eng = MonteCarloEngine(seed=SEED_42)
    with pytest.raises(ValueError):
        eng.analyze(returns_series=RETURNS_3, mode="returns", simulations=0)


def test_raises_for_simulations_negative():
    eng = MonteCarloEngine(seed=SEED_42)
    with pytest.raises(ValueError):
        eng.analyze(returns_series=RETURNS_3, mode="returns", simulations=-1)


def test_raises_for_returns_series_too_short():
    eng = MonteCarloEngine(seed=SEED_42)
    with pytest.raises(ValueError):
        eng.analyze(returns_series=[0.1], mode="returns", simulations=3)


def test_raises_for_returns_series_empty():
    eng = MonteCarloEngine(seed=SEED_42)
    with pytest.raises(ValueError):
        eng.analyze(returns_series=[], mode="returns", simulations=3)


def test_raises_for_trades_too_short():
    eng = MonteCarloEngine(seed=SEED_42)
    with pytest.raises(ValueError):
        eng.analyze(trades=[0.1], mode="trades", simulations=3)


def test_raises_for_trades_empty():
    eng = MonteCarloEngine(seed=SEED_42)
    with pytest.raises(ValueError):
        eng.analyze(trades=[], mode="trades", simulations=3)


def test_raises_for_unknown_mode():
    eng = MonteCarloEngine(seed=SEED_42)
    with pytest.raises(ValueError):
        eng.analyze(returns_series=RETURNS_3, mode="invalid_mode", simulations=3)


def test_raises_for_negative_slippage_std():
    eng = MonteCarloEngine(seed=SEED_42)
    with pytest.raises(ValueError):
        eng.analyze(returns_series=RETURNS_3, mode="execution",
                    simulations=3, slippage_std=-0.01)


def test_raises_for_negative_shock_std():
    eng = MonteCarloEngine(seed=SEED_42)
    with pytest.raises(ValueError):
        eng.analyze(returns_series=RETURNS_3, mode="execution",
                    simulations=3, shock_std=-0.05)


def test_execution_mode_missing_returns_series_raises():
    eng = MonteCarloEngine(seed=SEED_42)
    with pytest.raises(ValueError):
        eng.analyze(mode="execution", simulations=3)


def test_trades_mode_missing_trades_raises():
    eng = MonteCarloEngine(seed=SEED_42)
    with pytest.raises(ValueError):
        eng.analyze(mode="trades", simulations=3)


def test_returns_mode_missing_returns_series_raises():
    eng = MonteCarloEngine(seed=SEED_42)
    with pytest.raises(ValueError):
        eng.analyze(mode="returns", simulations=3)


# ===========================================================================
# PART 8 — Aggregate math correctness (Bessel, prob_loss, worst_drawdown)
# ===========================================================================

def test_returns_mode_bessel_variance():
    eng = MonteCarloEngine(seed=SEED_42)
    result = eng.analyze(returns_series=RETURNS_3, mode="returns", simulations=3)
    sharpes = [s["sharpe_ratio"] for s in result["simulations_results"]]
    n = len(sharpes)
    mean = sum(sharpes) / n
    expected = sum((x - mean)**2 for x in sharpes) / (n - 1)
    assert result["sharpe_variance"] == pytest.approx(expected, rel=1e-9)


def test_single_sim_variance_is_zero():
    eng = MonteCarloEngine(seed=SEED_42)
    result = eng.analyze(returns_series=RETURNS_3, mode="returns", simulations=1)
    assert result["sharpe_variance"] == 0.0


def test_probability_of_loss_formula():
    eng = MonteCarloEngine(seed=SEED_42)
    result = eng.analyze(returns_series=RETURNS_3, mode="returns", simulations=3)
    returns_p = [s["return_pct"] for s in result["simulations_results"]]
    expected = sum(1 for r in returns_p if r < 0) / len(returns_p)
    assert result["probability_of_loss"] == pytest.approx(expected, rel=1e-9)


def test_worst_drawdown_is_minimum():
    eng = MonteCarloEngine(seed=SEED_42)
    result = eng.analyze(returns_series=RETURNS_3, mode="returns", simulations=3)
    drawdowns = [s["max_drawdown_pct"] for s in result["simulations_results"]]
    assert result["worst_drawdown"] == min(drawdowns)


def test_mean_return_pct_is_average():
    eng = MonteCarloEngine(seed=SEED_42)
    result = eng.analyze(returns_series=RETURNS_3, mode="returns", simulations=3)
    returns_p = [s["return_pct"] for s in result["simulations_results"]]
    expected = sum(returns_p) / len(returns_p)
    assert result["mean_return_pct"] == pytest.approx(expected, rel=1e-9)
