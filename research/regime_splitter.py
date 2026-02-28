"""
research.regime_splitter
========================

Splits a list of candle dicts into sequential, non-overlapping time windows
for regime-based strategy analysis.
"""

import copy


def split_into_time_windows(
    candles: list[dict], window_size: int
) -> list[list[dict]]:
    """
    Split *candles* into sequential, non-overlapping windows of *window_size*.

    Parameters
    ----------
    candles : list[dict]
        Ordered (chronological) list of OHLCV candle dicts.
    window_size : int
        Number of candles per window.  Must be >= 2.

    Returns
    -------
    list[list[dict]]
        Windows in chronological order.  Each window is a deep-copied slice
        of *candles* so that neither the original list nor any candle dict
        is mutated.  The final (remainder) window is included only when it
        contains at least 2 candles; a trailing window of length 1 is
        silently discarded.

    Raises
    ------
    ValueError
        * If ``window_size < 2``
        * If ``len(candles) < window_size`` (not enough data for even one full window)
    """
    if window_size < 2:
        raise ValueError(
            f"window_size must be >= 2, got {window_size}"
        )
    if len(candles) < window_size:
        raise ValueError(
            f"Not enough candles: need at least {window_size}, got {len(candles)}"
        )

    windows: list[list[dict]] = []
    n = len(candles)
    start = 0

    while start < n:
        end = start + window_size
        slice_ = candles[start:end]

        # Only include this slice if it has at least 2 candles
        if len(slice_) >= 2:
            # Deep-copy each candle so callers cannot mutate the originals
            windows.append([copy.copy(c) for c in slice_])

        start = end

    return windows
