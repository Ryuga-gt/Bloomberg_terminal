"""
RED tests for research.monte_carlo_engine.monte_carlo_analysis

Contract:
    monte_carlo_analysis(
        returns_series,
        simulations,
        initial_cash=1000,
        seed=None,
    ) -> dict

Simulation logic (per simulation):
    1. Bootstrap-sample len(returns_series) returns WITH REPLACEMENT
       using Python's random.choices.
    2. Reconstruct equity curve via compound growth:
         equity[0]   = initial_cash
         equity[i]   = equity[i-1] * (1 + sample[i-1])   for i >= 1
    3. Compute per-simulation metrics:
         final_equity    = equity[-1]
         return_pct      = (final_equity - initial_cash) / initial_cash * 100
         sharpe_ratio    = mean(ret_series) / sample_std(ret_series)
                           where ret_series = [0.0] + list(sample)
                           and sample_std uses Bessel correction (n-1)
                           0.0 when std == 0
         max_drawdown_pct = running peak-to-trough, as pct of peak, minimum value

Aggregation:
    mean_sharpe         = mean of per-sim sharpe_ratio
    sharpe_variance     = Bessel-corrected variance of per-sim sharpe_ratio
                          0.0 when simulations == 1
    mean_return_pct     = mean of per-sim return_pct
    probability_of_loss = fraction of sims where return_pct < 0
    worst_drawdown      = min of per-sim max_drawdown_pct

Return dict must include:
    simulations_results     list of per-sim dicts
    mean_sharpe
    sharpe_variance
    mean_return_pct
    probability_of_loss
    worst_drawdown

Raises ValueError for:
    len(returns_series) < 2
    simulations < 1
    initial_cash <= 0
    mutation of returns_series is forbidden
"""

import math
import random
import pytest

from research.monte_carlo_engine import monte_carlo_analysis


# ---------------------------------------------------------------------------
# Reference helpers — re-implement spec to derive exact expected values
# ---------------------------------------------------------------------------

def _sim_once(returns_series: list[float], initial_cash: float,
              rng: random.Random) -> dict:
    n = len(returns_series)
    sample = rng.choices(returns_series, k=n)

    # Compound equity curve
    eq = initial_cash
    curve = [eq]
    for r in sample:
        eq = eq * (1 + r)
        curve.append(eq)
    final_equity = curve[-1]
    return_pct   = (final_equity - initial_cash) / initial_cash * 100

    # Sharpe from [0.0] + sample
    ret_series = [0.0] + list(sample)
    m = len(ret_series)
    mean_r = sum(ret_series) / m
    var_r  = sum((x - mean_r) ** 2 for x in ret_series) / (m - 1)
    std_r  = math.sqrt(var_r)
    sharpe = mean_r / std_r if std_r != 0.0 else 0.0

    # Max drawdown
    peak = curve[0]
    mdd  = 0.0
    for v in curve:
        if v > peak:
            peak = v
        dd = (v - peak) / peak * 100
        if dd < mdd:
            mdd = dd

    return {
        "final_equity":    final_equity,
        "return_pct":      return_pct,
        "sharpe_ratio":    sharpe,
        "max_drawdown_pct": mdd,
    }


def _ref_monte_carlo(returns_series, simulations, initial_cash=1000, seed=None):
    rng = random.Random(seed)
    sim_results = [
        _sim_once(returns_series, initial_cash, rng)
        for _ in range(simulations)
    ]
    sharpes   = [s["sharpe_ratio"]     for s in sim_results]
    returns_p = [s["return_pct"]       for s in sim_results]
    drawdowns = [s["max_drawdown_pct"] for s in sim_results]

    n = len(sim_results)
    mean_sharpe     = sum(sharpes) / n
    sharpe_variance = (
        sum((x - mean_sharpe) ** 2 for x in sharpes) / (n - 1)
        if n > 1 else 0.0
    )
    mean_return_pct     = sum(returns_p) / n
    probability_of_loss = sum(1 for r in returns_p if r < 0) / n
    worst_drawdown      = min(drawdowns)

    return {
        "simulations_results": sim_results,
        "mean_sharpe":         mean_sharpe,
        "sharpe_variance":     sharpe_variance,
        "mean_return_pct":     mean_return_pct,
        "probability_of_loss": probability_of_loss,
        "worst_drawdown":      worst_drawdown,
    }


# ---------------------------------------------------------------------------
# Primary fixture
# returns_series = [0.1, 0.2, -0.05], simulations=3, seed=42
#
# seed=42 RNG sequence (random.choices, k=3 each call):
#   sim 0: [0.2, 0.1, 0.1]
#   sim 1: [0.1, -0.05, -0.05]
#   sim 2: [-0.05, 0.1, 0.2]
# ---------------------------------------------------------------------------

RETURNS_3   = [0.1, 0.2, -0.05]
SEED_42     = 42
SIMS_3      = 3
CASH_1000   = 1000.0


# ===========================================================================
# PART 1 — Return type and top-level keys
# ===========================================================================

def test_returns_dict():
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    assert isinstance(result, dict)


def test_result_has_simulations_results_key():
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    assert "simulations_results" in result


def test_result_has_mean_sharpe_key():
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    assert "mean_sharpe" in result


def test_result_has_sharpe_variance_key():
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    assert "sharpe_variance" in result


def test_result_has_mean_return_pct_key():
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    assert "mean_return_pct" in result


def test_result_has_probability_of_loss_key():
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    assert "probability_of_loss" in result


def test_result_has_worst_drawdown_key():
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    assert "worst_drawdown" in result


# ===========================================================================
# PART 2 — simulations_results structure
# ===========================================================================

def test_simulations_results_is_list():
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    assert isinstance(result["simulations_results"], list)


def test_simulations_results_length_equals_simulations():
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    assert len(result["simulations_results"]) == SIMS_3


def test_each_sim_result_has_final_equity():
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    for s in result["simulations_results"]:
        assert "final_equity" in s


def test_each_sim_result_has_return_pct():
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    for s in result["simulations_results"]:
        assert "return_pct" in s


def test_each_sim_result_has_sharpe_ratio():
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    for s in result["simulations_results"]:
        assert "sharpe_ratio" in s


def test_each_sim_result_has_max_drawdown_pct():
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    for s in result["simulations_results"]:
        assert "max_drawdown_pct" in s


# ===========================================================================
# PART 3 — Exact per-simulation compound math
#
# seed=42, returns=[0.1, 0.2, -0.05]:
#   sim 0 sample=[0.2, 0.1, 0.1]:
#     equity: 1000 → 1200 → 1320 → 1452
#     final_equity = 1452.0,  return_pct = 45.2
#     ret_series   = [0.0, 0.2, 0.1, 0.1]
#     mean_r=(0+0.2+0.1+0.1)/4=0.1, var=(4 terms, bessel)/3
#     sharpe = mean_r/std_r
#   sim 1 sample=[0.1, -0.05, -0.05]:
#     equity: 1000 → 1100 → 1045 → 992.75
#     return_pct = -0.725  (LOSS)
#   sim 2 sample=[-0.05, 0.1, 0.2]:
#     equity: 1000 → 950 → 1045 → 1254
# ===========================================================================

def test_sim0_final_equity():
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    ref    = _ref_monte_carlo(RETURNS_3, SIMS_3, seed=SEED_42)
    assert result["simulations_results"][0]["final_equity"] == pytest.approx(
        ref["simulations_results"][0]["final_equity"], rel=1e-9)


def test_sim0_return_pct():
    # sample=[0.2,0.1,0.1]: 1000*1.2*1.1*1.1 = 1452, return=45.2%
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    assert result["simulations_results"][0]["return_pct"] == pytest.approx(45.2, rel=1e-9)


def test_sim0_max_drawdown_monotonic():
    # 1000→1200→1320→1452: monotonically rising → drawdown=0.0
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    assert result["simulations_results"][0]["max_drawdown_pct"] == 0.0


def test_sim1_return_pct_negative():
    # sample=[0.1,-0.05,-0.05]: return_pct = -0.725
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    assert result["simulations_results"][1]["return_pct"] == pytest.approx(-0.725, rel=1e-9)


def test_sim1_max_drawdown():
    # equity: 1000→1100→1045→992.75
    # peak after step1=1100, trough=992.75 → dd=(992.75-1100)/1100*100=-9.75
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    assert result["simulations_results"][1]["max_drawdown_pct"] == pytest.approx(-9.75, rel=1e-9)


def test_sim1_sharpe_zero_mean():
    # ret_series=[0.0,0.1,-0.05,-0.05], mean=0.0 → sharpe=0.0
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    assert result["simulations_results"][1]["sharpe_ratio"] == 0.0


def test_sim2_final_equity():
    # sample=[-0.05,0.1,0.2]: 1000*0.95*1.1*1.2 = 1254
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    assert result["simulations_results"][2]["final_equity"] == pytest.approx(1254.0, rel=1e-9)


def test_sim2_max_drawdown():
    # equity: 1000→950→1045→1254; peak=1000 then 950→dd=-5.0%, then rises
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    assert result["simulations_results"][2]["max_drawdown_pct"] == pytest.approx(-5.0, rel=1e-9)


# ===========================================================================
# PART 4 — Exact Sharpe calculation
#
# sim 0: ret_series = [0.0, 0.2, 0.1, 0.1]
#   mean = (0+0.2+0.1+0.1)/4 = 0.1
#   var  = ((0-0.1)^2+(0.2-0.1)^2+(0.1-0.1)^2+(0.1-0.1)^2)/(4-1)
#        = (0.01+0.01+0+0)/3 = 0.02/3 = 0.006666...
#   std  = sqrt(0.00666...) = 0.081649...
#   sharpe = 0.1 / 0.081649... = 1.224744...
# ===========================================================================

def test_sim0_sharpe_exact():
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    ref    = _ref_monte_carlo(RETURNS_3, SIMS_3, seed=SEED_42)
    assert result["simulations_results"][0]["sharpe_ratio"] == pytest.approx(
        ref["simulations_results"][0]["sharpe_ratio"], rel=1e-9)


def test_sim0_sharpe_manual():
    # Manual: ret_series=[0.0,0.2,0.1,0.1]
    # mean=0.1, var=0.02/3, std=sqrt(0.02/3), sharpe=0.1/sqrt(0.02/3)=sqrt(3)/2*sqrt(2)=sqrt(6)/2
    # = 1.2247448713915890...
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    expected = math.sqrt(6) / 2  # exact closed form
    assert result["simulations_results"][0]["sharpe_ratio"] == pytest.approx(expected, rel=1e-9)


def test_sim2_sharpe_exact():
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    ref    = _ref_monte_carlo(RETURNS_3, SIMS_3, seed=SEED_42)
    assert result["simulations_results"][2]["sharpe_ratio"] == pytest.approx(
        ref["simulations_results"][2]["sharpe_ratio"], rel=1e-9)


# ===========================================================================
# PART 5 — Aggregate metric correctness
# ===========================================================================

def test_correct_mean_sharpe():
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    ref    = _ref_monte_carlo(RETURNS_3, SIMS_3, seed=SEED_42)
    assert result["mean_sharpe"] == pytest.approx(ref["mean_sharpe"], rel=1e-9)


def test_mean_sharpe_is_average_of_sim_sharpes():
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    sharpes  = [s["sharpe_ratio"] for s in result["simulations_results"]]
    expected = sum(sharpes) / len(sharpes)
    assert result["mean_sharpe"] == pytest.approx(expected, rel=1e-9)


def test_correct_sharpe_variance():
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    ref    = _ref_monte_carlo(RETURNS_3, SIMS_3, seed=SEED_42)
    assert result["sharpe_variance"] == pytest.approx(ref["sharpe_variance"], rel=1e-9)


def test_sharpe_variance_uses_bessel_correction():
    """Variance must divide by (n-1), not n."""
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    sharpes = [s["sharpe_ratio"] for s in result["simulations_results"]]
    n = len(sharpes)
    mean = sum(sharpes) / n
    bessel_var = sum((x - mean) ** 2 for x in sharpes) / (n - 1)
    biased_var = sum((x - mean) ** 2 for x in sharpes) / n
    assert result["sharpe_variance"] == pytest.approx(bessel_var, rel=1e-9)
    if sharpes[0] != sharpes[-1]:   # non-trivial guard
        assert abs(result["sharpe_variance"] - biased_var) > 1e-12


def test_sharpe_variance_non_negative():
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    assert result["sharpe_variance"] >= 0.0


def test_correct_mean_return_pct():
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    ref    = _ref_monte_carlo(RETURNS_3, SIMS_3, seed=SEED_42)
    assert result["mean_return_pct"] == pytest.approx(ref["mean_return_pct"], rel=1e-9)


def test_mean_return_pct_is_average_of_sim_returns():
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    returns_p = [s["return_pct"] for s in result["simulations_results"]]
    expected  = sum(returns_p) / len(returns_p)
    assert result["mean_return_pct"] == pytest.approx(expected, rel=1e-9)


def test_correct_probability_of_loss():
    # sim1 return=-0.725 < 0, sims 0 and 2 > 0 → prob_loss = 1/3
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    assert result["probability_of_loss"] == pytest.approx(1 / 3, rel=1e-9)


def test_probability_of_loss_is_fraction():
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    p = result["probability_of_loss"]
    assert 0.0 <= p <= 1.0


def test_probability_of_loss_zero_for_all_positive():
    # returns_series all positive → every bootstrap sample will be positive
    returns_pos = [0.05, 0.10, 0.08]
    result = monte_carlo_analysis(returns_pos, simulations=10, seed=1)
    assert result["probability_of_loss"] == 0.0


def test_probability_of_loss_one_for_all_negative():
    # returns_series all negative → every bootstrap sample will be negative
    returns_neg = [-0.05, -0.10, -0.08]
    result = monte_carlo_analysis(returns_neg, simulations=10, seed=2)
    assert result["probability_of_loss"] == 1.0


def test_correct_worst_drawdown():
    # worst is sim1: -9.75
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    ref    = _ref_monte_carlo(RETURNS_3, SIMS_3, seed=SEED_42)
    assert result["worst_drawdown"] == pytest.approx(ref["worst_drawdown"], rel=1e-9)


def test_worst_drawdown_is_minimum_of_sim_drawdowns():
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    drawdowns = [s["max_drawdown_pct"] for s in result["simulations_results"]]
    assert result["worst_drawdown"] == min(drawdowns)


def test_worst_drawdown_equals_neg_9_75():
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    assert result["worst_drawdown"] == pytest.approx(-9.75, rel=1e-9)


# ===========================================================================
# PART 6 — Determinism with fixed seed
# ===========================================================================

def test_deterministic_with_seed():
    r1 = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    r2 = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    assert r1["mean_sharpe"]         == r2["mean_sharpe"]
    assert r1["sharpe_variance"]     == r2["sharpe_variance"]
    assert r1["mean_return_pct"]     == r2["mean_return_pct"]
    assert r1["probability_of_loss"] == r2["probability_of_loss"]
    assert r1["worst_drawdown"]      == r2["worst_drawdown"]


def test_deterministic_per_sim_with_seed():
    r1 = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    r2 = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    for s1, s2 in zip(r1["simulations_results"], r2["simulations_results"]):
        assert s1["final_equity"]     == s2["final_equity"]
        assert s1["sharpe_ratio"]     == s2["sharpe_ratio"]
        assert s1["max_drawdown_pct"] == s2["max_drawdown_pct"]


def test_different_seeds_produce_different_results():
    r1 = monte_carlo_analysis(RETURNS_3, simulations=10, seed=1)
    r2 = monte_carlo_analysis(RETURNS_3, simulations=10, seed=999)
    # Not guaranteed, but extremely unlikely to be equal with 10 sims and different seeds
    assert r1["mean_return_pct"] != r2["mean_return_pct"]


def test_seed_none_is_allowed():
    """seed=None must not raise; result is non-deterministic but structurally valid."""
    result = monte_carlo_analysis(RETURNS_3, simulations=5, seed=None)
    assert "mean_sharpe" in result
    assert len(result["simulations_results"]) == 5


# ===========================================================================
# PART 7 — Exact compound math with constant-return fixture
#
# returns_series = [0.1, 0.1]  (only one distinct value)
# Any bootstrap sample must be [0.1, 0.1]
# equity: 1000 → 1100 → 1210
# final_equity = 1210.0,  return_pct = 21.0
# ret_series   = [0.0, 0.1, 0.1]
# mean_r = 0.2/3
# var_r  = ((0-mean)^2 + (0.1-mean)^2 + (0.1-mean)^2) / 2
# sharpe = mean_r / sqrt(var_r)
# max_drawdown = 0.0 (monotonically rising)
# ===========================================================================

RETURNS_CONST = [0.1, 0.1]


def test_constant_returns_final_equity():
    result = monte_carlo_analysis(RETURNS_CONST, simulations=3, seed=0)
    for s in result["simulations_results"]:
        assert s["final_equity"] == pytest.approx(1210.0, rel=1e-9)


def test_constant_returns_return_pct():
    result = monte_carlo_analysis(RETURNS_CONST, simulations=3, seed=0)
    for s in result["simulations_results"]:
        assert s["return_pct"] == pytest.approx(21.0, rel=1e-9)


def test_constant_returns_no_drawdown():
    result = monte_carlo_analysis(RETURNS_CONST, simulations=3, seed=0)
    for s in result["simulations_results"]:
        assert s["max_drawdown_pct"] == 0.0


def test_constant_returns_sharpe_exact():
    # ret_series=[0.0, 0.1, 0.1]
    # mean=0.2/3, var=((0-mean)^2+(0.1-mean)^2+(0.1-mean)^2)/2
    ret_series = [0.0, 0.1, 0.1]
    mean_r = sum(ret_series) / 3
    var_r  = sum((x - mean_r) ** 2 for x in ret_series) / 2
    std_r  = math.sqrt(var_r)
    expected_sharpe = mean_r / std_r
    result = monte_carlo_analysis(RETURNS_CONST, simulations=1, seed=0)
    assert result["simulations_results"][0]["sharpe_ratio"] == pytest.approx(
        expected_sharpe, rel=1e-9)


def test_constant_returns_mean_return_pct():
    result = monte_carlo_analysis(RETURNS_CONST, simulations=5, seed=0)
    assert result["mean_return_pct"] == pytest.approx(21.0, rel=1e-9)


def test_constant_returns_zero_probability_of_loss():
    result = monte_carlo_analysis(RETURNS_CONST, simulations=5, seed=0)
    assert result["probability_of_loss"] == 0.0


def test_constant_returns_worst_drawdown_zero():
    result = monte_carlo_analysis(RETURNS_CONST, simulations=5, seed=0)
    assert result["worst_drawdown"] == 0.0


# ===========================================================================
# PART 8 — initial_cash parameter
# ===========================================================================

def test_initial_cash_default_is_1000():
    r_default = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    r_explicit = monte_carlo_analysis(RETURNS_3, SIMS_3, initial_cash=1000, seed=SEED_42)
    assert r_default["mean_return_pct"] == r_explicit["mean_return_pct"]


def test_initial_cash_scales_final_equity():
    """Doubling initial_cash doubles every final_equity; return_pct is unchanged."""
    r1000 = monte_carlo_analysis(RETURNS_3, SIMS_3, initial_cash=1000, seed=SEED_42)
    r2000 = monte_carlo_analysis(RETURNS_3, SIMS_3, initial_cash=2000, seed=SEED_42)
    for s1, s2 in zip(r1000["simulations_results"], r2000["simulations_results"]):
        assert s2["final_equity"] == pytest.approx(s1["final_equity"] * 2, rel=1e-9)
        assert s2["return_pct"]   == pytest.approx(s1["return_pct"],        rel=1e-9)


def test_initial_cash_does_not_affect_sharpe():
    """Sharpe is scale-invariant: same samples → same sharpe regardless of cash."""
    r1000 = monte_carlo_analysis(RETURNS_CONST, simulations=3, initial_cash=1000, seed=0)
    r500  = monte_carlo_analysis(RETURNS_CONST, simulations=3, initial_cash=500,  seed=0)
    for s1, s5 in zip(r1000["simulations_results"], r500["simulations_results"]):
        assert s1["sharpe_ratio"] == pytest.approx(s5["sharpe_ratio"], rel=1e-9)


# ===========================================================================
# PART 9 — simulations=1 edge case (sharpe_variance must be 0.0)
# ===========================================================================

def test_single_simulation_produces_one_result():
    result = monte_carlo_analysis(RETURNS_3, simulations=1, seed=SEED_42)
    assert len(result["simulations_results"]) == 1


def test_single_simulation_sharpe_variance_is_zero():
    """With n=1 Bessel variance is undefined → must return 0.0, not raise."""
    result = monte_carlo_analysis(RETURNS_3, simulations=1, seed=SEED_42)
    assert result["sharpe_variance"] == 0.0


def test_single_simulation_probability_of_loss_is_0_or_1():
    result = monte_carlo_analysis(RETURNS_3, simulations=1, seed=SEED_42)
    p = result["probability_of_loss"]
    assert p == 0.0 or p == 1.0


# ===========================================================================
# PART 10 — No mutation of input returns_series
# ===========================================================================

def test_does_not_mutate_returns_series_length():
    returns = [0.1, 0.2, -0.05]
    orig_len = len(returns)
    monte_carlo_analysis(returns, simulations=5, seed=0)
    assert len(returns) == orig_len


def test_does_not_mutate_returns_series_values():
    returns = [0.1, 0.2, -0.05]
    orig = list(returns)
    monte_carlo_analysis(returns, simulations=5, seed=0)
    assert returns == orig


# ===========================================================================
# PART 11 — ValueError for invalid inputs
# ===========================================================================

def test_raises_for_returns_series_length_one():
    with pytest.raises(ValueError):
        monte_carlo_analysis([0.1], simulations=5)


def test_raises_for_returns_series_empty():
    with pytest.raises(ValueError):
        monte_carlo_analysis([], simulations=5)


def test_raises_for_simulations_zero():
    with pytest.raises(ValueError):
        monte_carlo_analysis(RETURNS_3, simulations=0)


def test_raises_for_simulations_negative():
    with pytest.raises(ValueError):
        monte_carlo_analysis(RETURNS_3, simulations=-1)


def test_raises_for_initial_cash_zero():
    with pytest.raises(ValueError):
        monte_carlo_analysis(RETURNS_3, simulations=5, initial_cash=0)


def test_raises_for_initial_cash_negative():
    with pytest.raises(ValueError):
        monte_carlo_analysis(RETURNS_3, simulations=5, initial_cash=-100)


# ===========================================================================
# PART 12 — Cross-check full run against reference implementation
# ===========================================================================

def test_full_run_matches_reference():
    ref    = _ref_monte_carlo(RETURNS_3, SIMS_3, seed=SEED_42)
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    assert result["mean_sharpe"]         == pytest.approx(ref["mean_sharpe"],         rel=1e-9)
    assert result["sharpe_variance"]     == pytest.approx(ref["sharpe_variance"],     rel=1e-9)
    assert result["mean_return_pct"]     == pytest.approx(ref["mean_return_pct"],     rel=1e-9)
    assert result["probability_of_loss"] == pytest.approx(ref["probability_of_loss"], rel=1e-9)
    assert result["worst_drawdown"]      == pytest.approx(ref["worst_drawdown"],      rel=1e-9)


def test_per_sim_results_match_reference():
    ref    = _ref_monte_carlo(RETURNS_3, SIMS_3, seed=SEED_42)
    result = monte_carlo_analysis(RETURNS_3, SIMS_3, seed=SEED_42)
    for r, s in zip(ref["simulations_results"], result["simulations_results"]):
        assert s["final_equity"]     == pytest.approx(r["final_equity"],     rel=1e-9)
        assert s["return_pct"]       == pytest.approx(r["return_pct"],       rel=1e-9)
        assert s["sharpe_ratio"]     == pytest.approx(r["sharpe_ratio"],     rel=1e-9)
        assert s["max_drawdown_pct"] == pytest.approx(r["max_drawdown_pct"], rel=1e-9)


# ===========================================================================
# PART 13 — Large simulation count regression (structure only, not values)
# ===========================================================================

def test_large_simulation_count_structure():
    result = monte_carlo_analysis(RETURNS_3, simulations=100, seed=7)
    assert len(result["simulations_results"]) == 100
    assert 0.0 <= result["probability_of_loss"] <= 1.0
    assert result["sharpe_variance"] >= 0.0
    assert result["worst_drawdown"] <= 0.0
