from abc import abstractmethod
from .. import Operation


class BallisticOperation(Operation):
    @property
    @abstractmethod
    def apogee(self) -> float:
        pass

    @property
    @abstractmethod
    def apogee_time(self) -> float:
        pass

    @property
    @abstractmethod
    def max_velocity(self) -> float:
        pass

    @property
    @abstractmethod
    def max_velocity_time(self) -> float:
        pass
