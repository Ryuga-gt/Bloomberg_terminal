"""
execution.broker_interface
==========================

Abstract base class for all broker implementations.

Any concrete broker (paper, live, simulated) must subclass
:class:`BrokerInterface` and implement :meth:`execute_order`.

Usage
-----
    class MyBroker(BrokerInterface):
        def execute_order(self, order: Order) -> Fill:
            ...
"""

from execution.order import Order, Fill


class BrokerInterface:
    """
    Abstract broker interface.

    Subclasses must override :meth:`execute_order`.
    """

    def execute_order(self, order: Order) -> Fill:
        """
        Execute *order* and return a :class:`Fill`.

        Parameters
        ----------
        order : Order
            The order to execute.

        Returns
        -------
        Fill
            Execution result.

        Raises
        ------
        NotImplementedError
            Always — subclasses must override this method.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement execute_order()"
        )
