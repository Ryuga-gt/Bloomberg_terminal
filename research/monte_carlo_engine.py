"""
research.monte_carlo_engine
===========================

Return-level Monte Carlo engine.

Bootstraps a returns series to produce many synthetic equity paths, then
aggregates per-path statistics into a distribution-level risk summary.
"""

import math
import random


def monte_carlo_analysis(
    returns_series: list[float],
    simulations: int,
    initial_cash: float = 1000,
    seed=None,
) -> dict:
    """
    Run a bootstrapped Monte Carlo analysis over *returns_series*.

    Parameters
    ----------
    returns_series : list[float]
        Historical per-period returns (e.g. ``[0.01, -0.02, 0.03, ...]``).
        Not mutated.  Must contain at least 2 elements.
    simulations : int
        Number of bootstrap paths to generate.  Must be >= 1.
    initial_cash : float, optional
        Starting portfolio value for every simulated path.  Default 1000.
        Must be > 0.
    seed : int or None, optional
        Seed for the internal ``random.Random`` instance.  Pass an integer
        for fully deterministic output; ``None`` (default) uses the global
        random state.

    Returns
    -------
    dict with keys:
        simulations_results : list[dict]
            Per-simulation metrics (see below).
        mean_sharpe         : float
        sharpe_variance     : float  — Bessel-corrected; 0.0 when simulations==1
        mean_return_pct     : float
        probability_of_loss : float  — fraction of paths where return_pct < 0
        worst_drawdown      : float  — minimum max_drawdown_pct across all paths

    Each entry in *simulations_results* contains:
        final_equity      : float
        return_pct        : float
        sharpe_ratio      : float
        max_drawdown_pct  : float

    Simulation logic per path
    -------------------------
    1. Bootstrap-sample ``len(returns_series)`` returns **with replacement**
       using ``random.choices``.
    2. Reconstruct equity curve via compound growth:
           equity[0] = initial_cash
           equity[i] = equity[i-1] * (1 + sample[i-1])
    3. ``final_equity``    = equity[-1]
    4. ``return_pct``      = (final_equity - initial_cash) / initial_cash * 100
    5. ``sharpe_ratio``    = mean(ret_series) / sample_std(ret_series)
                             where ret_series = [0.0] + list(sample)
                             and sample_std uses Bessel correction (n-1).
                             Returns 0.0 when std_dev == 0.
    6. ``max_drawdown_pct`` = running peak-to-trough minimum, as % of peak.

    Raises
    ------
    ValueError
        * ``len(returns_series) < 2``
        * ``simulations < 1``
        * ``initial_cash <= 0``
    """
    # ------------------------------------------------------------------ #
    # Validation                                                           #
    # ------------------------------------------------------------------ #
    if len(returns_series) < 2:
        raise ValueError(
            f"returns_series must have at least 2 elements, got {len(returns_series)}"
        )
    if simulations < 1:
        raise ValueError(f"simulations must be >= 1, got {simulations}")
    if initial_cash <= 0:
        raise ValueError(f"initial_cash must be > 0, got {initial_cash}")

    # ------------------------------------------------------------------ #
    # RNG — isolated instance so callers' global state is unaffected       #
    # ------------------------------------------------------------------ #
    rng = random.Random(seed)
    n_returns = len(returns_series)

    # ------------------------------------------------------------------ #
    # Per-simulation bootstrap                                             #
    # ------------------------------------------------------------------ #
    sim_results: list[dict] = []

    for _ in range(simulations):
        sample = rng.choices(returns_series, k=n_returns)

        # --- Compound equity curve ---
        eq = initial_cash
        curve = [eq]
        for r in sample:
            eq = eq * (1 + r)
            curve.append(eq)

        final_equity = curve[-1]
        return_pct   = (final_equity - initial_cash) / initial_cash * 100

        # --- Sharpe ratio ---
        ret_series = [0.0] + list(sample)
        m          = len(ret_series)
        mean_r     = sum(ret_series) / m
        var_r      = sum((x - mean_r) ** 2 for x in ret_series) / (m - 1)
        std_r      = math.sqrt(var_r)
        sharpe     = mean_r / std_r if std_r != 0.0 else 0.0

        # --- Max drawdown ---
        peak = curve[0]
        mdd  = 0.0
        for v in curve:
            if v > peak:
                peak = v
            dd = (v - peak) / peak * 100
            if dd < mdd:
                mdd = dd

        sim_results.append({
            "final_equity":     final_equity,
            "return_pct":       return_pct,
            "sharpe_ratio":     sharpe,
            "max_drawdown_pct": mdd,
        })

    # ------------------------------------------------------------------ #
    # Aggregation                                                          #
    # ------------------------------------------------------------------ #
    n = len(sim_results)
    sharpes   = [s["sharpe_ratio"]     for s in sim_results]
    returns_p = [s["return_pct"]       for s in sim_results]
    drawdowns = [s["max_drawdown_pct"] for s in sim_results]

    mean_sharpe = sum(sharpes) / n

    # Bessel-corrected variance; undefined (0.0) for a single simulation
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
