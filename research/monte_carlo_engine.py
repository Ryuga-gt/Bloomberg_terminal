"""
research.monte_carlo_engine
===========================

Return-level Monte Carlo engine.

Provides:
    - ``MonteCarloEngine``  — class-based interface supporting three modes.
    - ``monte_carlo_analysis`` — Phase A function (preserved for backward
      compatibility; delegates to MonteCarloEngine internally).
"""

import math
import random


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _metrics_from_sample(sample: list[float], initial_cash: float) -> dict:
    """
    Compound equity curve and compute per-simulation metrics from
    an already-prepared list of per-period returns.

    Parameters
    ----------
    sample : list[float]
        Ordered sequence of per-period returns for this simulation.
    initial_cash : float
        Starting portfolio value.

    Returns
    -------
    dict with keys: final_equity, return_pct, sharpe_ratio, max_drawdown_pct
    """
    # Compound equity curve
    eq = initial_cash
    curve = [eq]
    for r in sample:
        eq = eq * (1 + r)
        curve.append(eq)

    final_equity = curve[-1]
    return_pct   = (final_equity - initial_cash) / initial_cash * 100

    # Sharpe ratio — ret_series = [0.0] + sample, Bessel-corrected std
    ret_series = [0.0] + list(sample)
    m          = len(ret_series)
    mean_r     = sum(ret_series) / m
    var_r      = sum((x - mean_r) ** 2 for x in ret_series) / (m - 1)
    std_r      = math.sqrt(var_r)
    sharpe     = mean_r / std_r if std_r != 0.0 else 0.0

    # Max drawdown — running peak-to-trough as % of peak
    peak = curve[0]
    mdd  = 0.0
    for v in curve:
        if v > peak:
            peak = v
        dd = (v - peak) / peak * 100
        if dd < mdd:
            mdd = dd

    return {
        "final_equity":     final_equity,
        "return_pct":       return_pct,
        "sharpe_ratio":     sharpe,
        "max_drawdown_pct": mdd,
    }


def _aggregate(sim_results: list[dict]) -> dict:
    """Compute distribution-level statistics from per-simulation results."""
    n = len(sim_results)
    sharpes   = [s["sharpe_ratio"]     for s in sim_results]
    returns_p = [s["return_pct"]       for s in sim_results]
    drawdowns = [s["max_drawdown_pct"] for s in sim_results]

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
# MonteCarloEngine
# ---------------------------------------------------------------------------

class MonteCarloEngine:
    """
    Class-based Monte Carlo engine supporting three simulation modes.

    Parameters
    ----------
    initial_cash : float, optional
        Starting portfolio value for every simulated path.  Default 1000.
        Must be > 0.
    seed : int or None, optional
        Seed for the internal RNG.  ``None`` draws from the global state.
    """

    def __init__(self, initial_cash: float = 1000, seed=None) -> None:
        if initial_cash <= 0:
            raise ValueError(f"initial_cash must be > 0, got {initial_cash}")
        self._initial_cash = initial_cash
        self._seed         = seed

    # ------------------------------------------------------------------
    def analyze(
        self,
        returns_series: list[float] | None = None,
        trades: list[float] | None = None,
        mode: str = "returns",
        simulations: int = 1000,
        slippage_std: float = 0.0,
        shock_std: float = 0.0,
    ) -> dict:
        """
        Run *simulations* Monte Carlo paths.

        Parameters
        ----------
        returns_series : list[float], optional
            Required for modes ``"returns"`` and ``"execution"``.
        trades : list[float], optional
            Required for mode ``"trades"``.
        mode : str
            ``"returns"``   — bootstrap with replacement from *returns_series*.
            ``"trades"``    — shuffle *trades* without replacement per sim.
            ``"execution"`` — bootstrap from *returns_series*, then apply
                              multiplicative shock and additive slippage noise.
        simulations : int
            Number of paths.  Must be >= 1.
        slippage_std : float
            Std-dev of additive slippage noise (execution mode only).
            0.0 → no slippage applied.  Must be >= 0.
        shock_std : float
            Std-dev of multiplicative shock (execution mode only).
            0.0 → no shock applied.  Must be >= 0.

        Returns
        -------
        dict — see module docstring for key definitions.

        Raises
        ------
        ValueError
            On invalid arguments or missing required inputs for the mode.
        """
        # ---------------------------------------------------------------- #
        # Parameter validation                                              #
        # ---------------------------------------------------------------- #
        if simulations < 1:
            raise ValueError(f"simulations must be >= 1, got {simulations}")
        if mode not in ("returns", "trades", "execution"):
            raise ValueError(
                f"mode must be 'returns', 'trades', or 'execution', got {mode!r}"
            )
        if slippage_std < 0:
            raise ValueError(f"slippage_std must be >= 0, got {slippage_std}")
        if shock_std < 0:
            raise ValueError(f"shock_std must be >= 0, got {shock_std}")

        if mode in ("returns", "execution"):
            if returns_series is None or len(returns_series) < 2:
                raise ValueError(
                    "returns_series must have at least 2 elements for "
                    f"mode={mode!r}, got "
                    f"{len(returns_series) if returns_series is not None else 0}"
                )
        if mode == "trades":
            if trades is None or len(trades) < 2:
                raise ValueError(
                    "trades must have at least 2 elements for mode='trades', got "
                    f"{len(trades) if trades is not None else 0}"
                )

        # ---------------------------------------------------------------- #
        # Isolated RNG                                                      #
        # ---------------------------------------------------------------- #
        rng = random.Random(self._seed)

        # ---------------------------------------------------------------- #
        # Simulation loop                                                   #
        # ---------------------------------------------------------------- #
        sim_results: list[dict] = []

        if mode == "returns":
            n = len(returns_series)
            for _ in range(simulations):
                sample = rng.choices(returns_series, k=n)
                sim_results.append(_metrics_from_sample(sample, self._initial_cash))

        elif mode == "trades":
            for _ in range(simulations):
                sample = list(trades)       # copy — never mutate the original
                rng.shuffle(sample)
                sim_results.append(_metrics_from_sample(sample, self._initial_cash))

        else:  # execution
            n = len(returns_series)
            for _ in range(simulations):
                # Step 1 — bootstrap sample (same RNG calls as returns mode)
                sample = rng.choices(returns_series, k=n)

                # Step 2 — apply noise only when std > 0
                # Skipping gauss calls when std == 0 keeps the RNG state
                # identical to returns mode, ensuring zero-std execution
                # reproduces the returns-mode baseline exactly.
                modified = []
                for r in sample:
                    if shock_std != 0.0:
                        r = r * rng.gauss(1.0, shock_std)
                    if slippage_std != 0.0:
                        r = r - rng.gauss(0.0, slippage_std)
                    modified.append(r)

                sim_results.append(_metrics_from_sample(modified, self._initial_cash))

        return _aggregate(sim_results)


# ---------------------------------------------------------------------------
# Phase A backward-compatible function (delegates to MonteCarloEngine)
# ---------------------------------------------------------------------------

def monte_carlo_analysis(
    returns_series: list[float],
    simulations: int,
    initial_cash: float = 1000,
    seed=None,
) -> dict:
    """
    Phase A entry point — bootstrapped Monte Carlo over *returns_series*.

    Preserved for backward compatibility.  Internally delegates to
    ``MonteCarloEngine.analyze(mode='returns')``.

    Parameters / returns / raises: identical to the original Phase A contract.
    """
    # Validation that Phase A tests depend on (engine validates too, but
    # we must surface the same errors for the same reasons)
    if len(returns_series) < 2:
        raise ValueError(
            f"returns_series must have at least 2 elements, got {len(returns_series)}"
        )
    if simulations < 1:
        raise ValueError(f"simulations must be >= 1, got {simulations}")
    if initial_cash <= 0:
        raise ValueError(f"initial_cash must be > 0, got {initial_cash}")

    engine = MonteCarloEngine(initial_cash=initial_cash, seed=seed)
    return engine.analyze(
        returns_series=returns_series,
        mode="returns",
        simulations=simulations,
    )
