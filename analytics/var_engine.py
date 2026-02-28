"""
analytics.var_engine
=====================

Value at Risk (VaR) engine.

Supports two methods:

historical_var(confidence)
    Sort returns ascending and take the (1 - confidence) percentile.
    E.g. for confidence=0.95, take the 5th percentile of the return
    distribution.  Returns a negative number (loss).

parametric_var(confidence)
    Assumes normally distributed returns.
    VaR = mu + z * sigma
    where z is the inverse standard normal CDF at (1 - confidence).
    Implemented via a rational approximation (no scipy/numpy).

Both methods return a float representing the loss threshold (negative
means a loss).

Validation
----------
* ``returns`` must have length >= 2 → ``ValueError``
* ``confidence`` must be in (0, 1) → ``ValueError``

All computations are pure Python, deterministic, and non-mutating.
"""

import math


# ---------------------------------------------------------------------------
# Rational approximation of the inverse standard normal CDF
# (Abramowitz & Stegun 26.2.17, maximum error 4.5e-4)
# ---------------------------------------------------------------------------

def _inv_norm(p: float) -> float:
    """
    Approximate inverse of the standard normal CDF at probability *p*.

    Parameters
    ----------
    p : float
        Probability in (0, 1).

    Returns
    -------
    float
        z such that Phi(z) ≈ p.
    """
    # Coefficients
    c0, c1, c2 = 2.515517, 0.802853, 0.010328
    d1, d2, d3 = 1.432788, 0.189269, 0.001308

    if p <= 0.0 or p >= 1.0:
        raise ValueError(f"p must be in (0, 1), got {p!r}")

    if p < 0.5:
        t = math.sqrt(-2.0 * math.log(p))
        sign = -1.0
    else:
        t = math.sqrt(-2.0 * math.log(1.0 - p))
        sign = 1.0

    numerator   = c0 + c1 * t + c2 * t * t
    denominator = 1.0 + d1 * t + d2 * t * t + d3 * t * t * t
    z = sign * (t - numerator / denominator)
    return z


class ValueAtRisk:
    """
    Value at Risk engine.

    Parameters
    ----------
    returns : list[float]
        Simple period returns.  Length >= 2.

    Raises
    ------
    ValueError
        If ``returns`` has fewer than 2 elements.
    """

    def __init__(self, returns: list) -> None:
        if len(returns) < 2:
            raise ValueError(
                f"returns must have at least 2 elements, got {len(returns)}"
            )
        self._returns = list(returns)  # defensive copy

    # ------------------------------------------------------------------

    def historical_var(self, confidence: float) -> float:
        """
        Historical (empirical) VaR at *confidence* level.

        Parameters
        ----------
        confidence : float
            Confidence level, e.g. 0.95 for 95% VaR.  Must be in (0, 1).

        Returns
        -------
        float
            The return at the (1 - confidence) percentile.  Negative
            values indicate a loss.

        Raises
        ------
        ValueError
            If ``confidence`` is not in (0, 1).
        """
        if not (0 < confidence < 1):
            raise ValueError(
                f"confidence must be in (0, 1), got {confidence!r}"
            )

        sorted_returns = sorted(self._returns)
        n = len(sorted_returns)
        # Index of the (1 - confidence) percentile
        idx = int(math.floor((1.0 - confidence) * n))
        idx = max(0, min(idx, n - 1))
        return sorted_returns[idx]

    def parametric_var(self, confidence: float) -> float:
        """
        Parametric (normal distribution) VaR at *confidence* level.

        VaR = mu + z * sigma
        where z = inverse normal CDF at (1 - confidence).

        Parameters
        ----------
        confidence : float
            Confidence level, e.g. 0.95 for 95% VaR.  Must be in (0, 1).

        Returns
        -------
        float
            Parametric VaR.  Negative values indicate a loss.

        Raises
        ------
        ValueError
            If ``confidence`` is not in (0, 1).
        """
        if not (0 < confidence < 1):
            raise ValueError(
                f"confidence must be in (0, 1), got {confidence!r}"
            )

        n = len(self._returns)
        mu = sum(self._returns) / n
        variance = sum((r - mu) ** 2 for r in self._returns) / (n - 1)
        sigma = math.sqrt(variance)

        z = _inv_norm(1.0 - confidence)
        return mu + z * sigma
