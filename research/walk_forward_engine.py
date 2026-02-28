"""
research.walk_forward_engine
============================

Walk-forward analysis: repeatedly fits a strategy on a training window
and evaluates it on the immediately following out-of-sample test window,
sliding both windows forward by ``step_size`` candles each iteration.
"""

import copy

from app.backtester.engine import Backtester


def walk_forward_analysis(
    strategy_class,
    candles: list[dict],
    train_size: int,
    test_size: int,
    step_size: int,
    initial_cash: float = 1000,
) -> dict:
    """
    Run a walk-forward analysis over *candles*.

    Parameters
    ----------
    strategy_class :
        A class (not an instance) with a no-argument constructor whose
        instances expose ``generate(candles) -> list[str]``.
    candles : list[dict]
        Full chronological OHLCV history.  Not mutated.
    train_size : int
        Number of candles in each training slice.  Must be >= 2.
    test_size : int
        Number of candles in each test slice.  Must be >= 2.
    step_size : int
        Number of candles to advance the window origin per iteration.
        Must be >= 1.
    initial_cash : float, optional
        Starting cash for every ``Backtester`` instance.  Default 1000.

    Returns
    -------
    dict with keys:
        windows              : list[dict]  – per-window metrics (see below)
        mean_train_sharpe    : float
        mean_test_sharpe     : float
        test_sharpe_variance : float  – Bessel-corrected sample variance
        performance_decay    : float  – mean_test_sharpe - mean_train_sharpe

    Each entry in *windows* contains:
        train_sharpe, test_sharpe,
        train_drawdown, test_drawdown,
        train_return, test_return

    Raises
    ------
    ValueError
        * ``train_size < 2``
        * ``test_size  < 2``
        * ``step_size  < 1``
        * Dataset too small to produce even one complete train+test window.
    """
    # ------------------------------------------------------------------ #
    # Parameter validation                                                 #
    # ------------------------------------------------------------------ #
    if train_size < 2:
        raise ValueError(f"train_size must be >= 2, got {train_size}")
    if test_size < 2:
        raise ValueError(f"test_size must be >= 2, got {test_size}")
    if step_size < 1:
        raise ValueError(f"step_size must be >= 1, got {step_size}")

    # ------------------------------------------------------------------ #
    # Check that at least one complete window fits in the dataset          #
    # ------------------------------------------------------------------ #
    if len(candles) < train_size + test_size:
        raise ValueError(
            f"Dataset too small: need at least {train_size + test_size} candles "
            f"for one window, got {len(candles)}"
        )

    # ------------------------------------------------------------------ #
    # Sliding-window loop                                                  #
    # ------------------------------------------------------------------ #
    windows_out: list[dict] = []
    pos = 0

    while True:
        train_slice = candles[pos: pos + train_size]
        test_slice  = candles[pos + train_size: pos + train_size + test_size]

        # Stop when the test window is incomplete
        if len(test_slice) < test_size:
            break

        # Run strategy on train slice
        bt_train = Backtester(initial_cash)
        r_train  = bt_train.run(
            [copy.copy(c) for c in train_slice],
            strategy=strategy_class(),
        )

        # Run strategy on test slice
        bt_test = Backtester(initial_cash)
        r_test  = bt_test.run(
            [copy.copy(c) for c in test_slice],
            strategy=strategy_class(),
        )

        windows_out.append({
            "train_sharpe":   r_train["sharpe_ratio"],
            "test_sharpe":    r_test["sharpe_ratio"],
            "train_drawdown": r_train["max_drawdown_pct"],
            "test_drawdown":  r_test["max_drawdown_pct"],
            "train_return":   r_train["return_pct"],
            "test_return":    r_test["return_pct"],
        })

        pos += step_size

    # ------------------------------------------------------------------ #
    # Aggregate metrics                                                    #
    # ------------------------------------------------------------------ #
    n = len(windows_out)
    train_sharpes = [w["train_sharpe"] for w in windows_out]
    test_sharpes  = [w["test_sharpe"]  for w in windows_out]

    mean_train_sharpe = sum(train_sharpes) / n
    mean_test_sharpe  = sum(test_sharpes)  / n

    # Bessel-corrected sample variance: divide by (n - 1).
    # With only one window the variance is undefined; return 0.0.
    test_sharpe_variance = (
        sum((s - mean_test_sharpe) ** 2 for s in test_sharpes) / (n - 1)
        if n > 1 else 0.0
    )

    performance_decay = mean_test_sharpe - mean_train_sharpe

    return {
        "windows":              windows_out,
        "mean_train_sharpe":    mean_train_sharpe,
        "mean_test_sharpe":     mean_test_sharpe,
        "test_sharpe_variance": test_sharpe_variance,
        "performance_decay":    performance_decay,
    }
