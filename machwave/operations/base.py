from abc import ABC, abstractmethod


class Operation(ABC):
    """
    The Operation class:
    - Stores simulation data
    - Iterates a simulation loop
    - Presents simulation data
    """

    @abstractmethod
    def __init__(self) -> None:
        """
        Initializes the operation, receiving arguments such as initial
        conditions or boundary conditions.
        """
        pass

    @abstractmethod
    def run_timestep(self, *args, **kwargs):
        """
        Runs on every iteration of a simulation loop, incrementing results
        and storing them in the Operation instance (self).
        """
        pass

    @abstractmethod
    def print_results(self, *args, **kwargs):
        """
        Prints some key values and metrics obtained from the operation.
        """
        pass
