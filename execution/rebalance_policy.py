"""
execution.rebalance_policy
==========================

Time-based rebalance policy for the portfolio lifecycle manager.

Usage
-----
    policy = RebalancePolicy(interval=5)
    for step in range(20):
        if policy.should_rebalance(step):
            ...  # rebalance at steps 0, 5, 10, 15

Design
------
* Stateless — ``should_rebalance`` depends only on ``step`` and
  ``interval``.
* Deterministic.
* No mutation of any input.

Validation
----------
* ``interval`` must be > 0 → ``ValueError``
"""


class RebalancePolicy:
    """
    Trigger rebalancing every *interval* candles.

    Parameters
    ----------
    interval : int
        Number of candles between rebalances.  Must be > 0.
        A rebalance is triggered when ``step % interval == 0``.

    Raises
    ------
    ValueError
        If ``interval`` is not > 0.
    """

    def __init__(self, interval: int) -> None:
        if interval <= 0:
            raise ValueError(
                f"interval must be > 0, got {interval!r}"
            )
        self._interval = int(interval)

    # ------------------------------------------------------------------

    @property
    def interval(self) -> int:
        return self._interval

    # ------------------------------------------------------------------

    def should_rebalance(self, step: int) -> bool:
        """
        Return ``True`` if a rebalance should occur at *step*.

        Parameters
        ----------
        step : int
            Current candle index (0-based).

        Returns
        -------
        bool
            ``True`` when ``step % interval == 0``.
        """
        return step % self._interval == 0
