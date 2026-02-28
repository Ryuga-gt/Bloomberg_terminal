"""
research.stability_engine
=========================

Analyses a trading strategy across multiple market regimes (time windows)
and produces a single stability score that summarises cross-regime consistency.
"""

from app.backtester.engine import Backtester
from research.regime_splitter import split_into_time_windows


def analyze_strategy(
    strategy_class,
    candles: list[dict],
    window_size: int,
    initial_cash: float = 1000,
) -> dict:
    """
    Run *strategy_class* across every time window and compute stability metrics.

    Parameters
    ----------
    strategy_class :
        A class (not an instance) whose constructor takes no arguments and
        whose instances expose a ``generate(candles) -> list[str]`` method.
    candles : list[dict]
        Full chronological OHLCV history.
    window_size : int
        Number of candles per regime window (forwarded to
        ``split_into_time_windows``; raises ``ValueError`` when invalid).
    initial_cash : float, optional
        Starting cash for each per-window ``Backtester`` instance.  Default 1000.

    Returns
    -------
    dict with keys:
        regime_metrics  : list[dict]  – raw Backtester output for each window
        mean_sharpe     : float       – arithmetic mean of per-window Sharpe ratios
        sharpe_variance : float       – Bessel-corrected sample variance of Sharpe ratios
        worst_drawdown  : float       – minimum (most negative) per-window max_drawdown_pct
        stability_score : float       – mean_sharpe - sharpe_variance - abs(worst_drawdown)/100

    Raises
    ------
    ValueError
        Propagated from ``split_into_time_windows`` for invalid inputs.
    """
    # ------------------------------------------------------------------ #
    # Step 1 — split into regime windows                                   #
    # ------------------------------------------------------------------ #
    windows = split_into_time_windows(candles, window_size)

    # ------------------------------------------------------------------ #
    # Step 2 — run strategy on each window, collect per-window metrics     #
    # ------------------------------------------------------------------ #
    regime_metrics: list[dict] = []
    for window in windows:
        bt = Backtester(initial_cash)
        result = bt.run(window, strategy=strategy_class())
        regime_metrics.append(result)

    # ------------------------------------------------------------------ #
    # Step 3 — aggregate metrics                                           #
    # ------------------------------------------------------------------ #
    sharpes   = [m["sharpe_ratio"]    for m in regime_metrics]
    drawdowns = [m["max_drawdown_pct"] for m in regime_metrics]

    n = len(sharpes)
    mean_sharpe = sum(sharpes) / n

    # Bessel-corrected sample variance: divide by (n - 1)
    sharpe_variance = sum((s - mean_sharpe) ** 2 for s in sharpes) / (n - 1)

    worst_drawdown = min(drawdowns)

    # ------------------------------------------------------------------ #
    # Step 4 — stability score                                             #
    # ------------------------------------------------------------------ #
    stability_score = mean_sharpe - sharpe_variance - abs(worst_drawdown) / 100

    return {
        "regime_metrics":  regime_metrics,
        "mean_sharpe":     mean_sharpe,
        "sharpe_variance": sharpe_variance,
        "worst_drawdown":  worst_drawdown,
        "stability_score": stability_score,
    }
