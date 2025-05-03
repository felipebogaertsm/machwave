from abc import abstractmethod

from machwave.operations import Operation


class BallisticOperation(Operation):
    @property
    @abstractmethod
    def apogee(self) -> float:
        """Get the apogee of the operation."""
        pass

    @property
    @abstractmethod
    def apogee_time(self) -> float:
        """Get the time of the apogee."""
        pass

    @property
    @abstractmethod
    def max_velocity(self) -> float:
        """Get the maximum velocity of the operation."""
        pass

    @property
    @abstractmethod
    def max_velocity_time(self) -> float:
        """Get the time of the maximum velocity."""
        pass
