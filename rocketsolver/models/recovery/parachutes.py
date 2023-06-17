"""
Parachutes are implemented using Strategy design pattern. The Parachute base 
class can be implemented in different ways by inheriting from it and then 
changing its methods depending on the particular parachute geometry. 
"""

from abc import ABC, abstractmethod

from rocketsolver.services.math.geometric import get_circle_area


class Parachute(ABC):
    def __init__(self) -> None:
        pass

    @property
    @abstractmethod
    def drag_coefficient(self):
        pass

    @property
    @abstractmethod
    def area(self):
        pass


class HemisphericalParachute(Parachute):
    def __init__(self, diameter) -> None:
        super().__init__()
        self.diameter = diameter

    @property
    def drag_coefficient(self) -> float:
        return 0.71

    @property
    def area(self) -> float:
        return get_circle_area(self.diameter)
