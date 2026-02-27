"""
execution.strategy_registry
============================

Dynamic strategy class registry.

Usage
-----
    registry = StrategyRegistry()
    registry.register("my_strategy", MyStrategyClass)
    cls = registry.get("my_strategy")
    names = registry.list_strategies()
    registry.unregister("my_strategy")

Rules
-----
* Names must be unique — registering a duplicate raises ``ValueError``.
* ``get()`` on an unknown name raises ``KeyError``.
* Stored classes are never mutated.
* Insertion order is preserved (``dict`` in Python 3.7+).
* No global state — each ``StrategyRegistry`` instance is independent.
"""


class StrategyRegistry:
    """
    Instance-based registry that maps string names to strategy classes.

    Parameters
    ----------
    None — instantiate with no arguments.

    Examples
    --------
    >>> registry = StrategyRegistry()
    >>> registry.register("trend", TrendFollowingStrategy)
    >>> cls = registry.get("trend")
    >>> registry.list_strategies()
    ['trend']
    >>> registry.unregister("trend")
    >>> registry.list_strategies()
    []
    """

    def __init__(self) -> None:
        # Ordered dict: name -> strategy_class
        self._registry: dict = {}

    # ------------------------------------------------------------------
    def register(self, name: str, strategy_class: type) -> None:
        """
        Register a strategy class under *name*.

        Parameters
        ----------
        name : str
            Unique identifier for the strategy.
        strategy_class : type
            The strategy class to register (not an instance).

        Raises
        ------
        ValueError
            If *name* is already registered.
        """
        if name in self._registry:
            raise ValueError(
                f"Strategy '{name}' is already registered. "
                "Unregister it first or choose a different name."
            )
        self._registry[name] = strategy_class

    # ------------------------------------------------------------------
    def unregister(self, name: str) -> None:
        """
        Remove the strategy registered under *name*.

        Parameters
        ----------
        name : str
            Name of the strategy to remove.

        Raises
        ------
        KeyError
            If *name* is not registered.
        """
        if name not in self._registry:
            raise KeyError(f"Strategy '{name}' is not registered.")
        del self._registry[name]

    # ------------------------------------------------------------------
    def get(self, name: str) -> type:
        """
        Retrieve the strategy class registered under *name*.

        Parameters
        ----------
        name : str
            Name of the strategy to look up.

        Returns
        -------
        type
            The registered strategy class.

        Raises
        ------
        KeyError
            If *name* is not registered.
        """
        if name not in self._registry:
            raise KeyError(f"Strategy '{name}' is not registered.")
        return self._registry[name]

    # ------------------------------------------------------------------
    def list_strategies(self) -> list:
        """
        Return a list of all registered strategy names in insertion order.

        Returns
        -------
        list[str]
        """
        return list(self._registry.keys())
