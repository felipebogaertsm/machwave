from abc import ABC, abstractmethod


class SimulationParameters(ABC):
    """
    Abstract class that stores simulation parameters and should be subclassed
    for specific simulations.

    Examples of simulation parameters:
    - time step for a time-based iterative simulation
    - initial elevation in the case of a rocket launch
    - igniter pressure in the case of an internal ballistic simulation
    """

    pass


class Simulation(ABC):
    """
    Abstract class that represents a simulation. Subclasses of Simulation
    implement specific simulation logic.

    NOTE: Instances of this class should not store any simulation state.
    Storing and analyzing simulation data should be done only by the State
    class.

    Attributes:
        params (SimulationParameters): Object containing simulation parameters.

    """

    def __init__(self, params: SimulationParameters) -> None:
        """
        Initializes the Simulation instance with the provided parameters.

        Args:
            params (SimulationParameters): Object containing simulation
                parameters.

        """
        self.params = params

    @abstractmethod
    def run(self) -> tuple:
        """
        Runs the simulation. This method should be implemented by subclasses.
        It typically contains a loop that iterates over time or distance.

        Returns:
            list[State]: A list of State instances representing the
            states performed during the simulation.

        """
        pass

    @abstractmethod
    def print_results(self, *args, **kwargs):
        """
        Prints the results of the simulation by calling the print_results
        method on the State instances of the simulation.

        Args:
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        """
        pass
