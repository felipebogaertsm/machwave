from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import numpy as np

from machwave.models.propulsion.propellants import Propellant
from machwave.models.propulsion.thrust_chamber import ThrustChamber
from machwave.services.flow.isentropic import get_thrust_from_cf

P = TypeVar("P", bound=Propellant)
T = TypeVar("T", bound=ThrustChamber)


class Motor(Generic[P, T], ABC):
    """
    Abstract rocket motor/engine class. Can be used to model any chemical
    rocket propulsion system, such as Solid, Hybrid and Liquid.
    """

    def __init__(
        self,
        propellant: P,
        thrust_chamber: T,
    ) -> None:
        """
        Instantiates object attributes common to any motor/engine (Solid,
        Hybrid or Liquid).

        Args:
            propellant: Object representing the propellant used in the motor.
            thrust_chamber: Object representing the thrust chamber of the motor.
        """
        self.propellant = propellant
        self.thrust_chamber = thrust_chamber

    @abstractmethod
    def get_launch_mass(self) -> float:
        """
        Calculates the total mass of the motor before launch.

        Returns:
            Total mass of the motor before launch, in kg
        """
        pass

    @abstractmethod
    def get_dry_mass(self) -> float:
        """
        Calculates the dry mass of the rocket at any time.

        Returns:
            Dry mass of the rocket, in kg
        """
        pass

    @abstractmethod
    def get_center_of_gravity(self) -> np.typing.NDArray[np.float64]:
        """
        Calculate the center of gravity of the propulsion system.

        The coordinate system is defined such that the origin (0, 0, 0) corresponds
        to the nozzle exit area on the combustion chamber axis.

        Returns:
            A 1D array of shape (3,) representing the [x, y, z] coordinates of the center of gravity, in meters.
        """
        pass

    @abstractmethod
    def get_thrust_coefficient_correction_factor(self, *args, **kwargs) -> float:
        """
        Calculates the thrust coefficient correction factor. This factor is
        adimensional and should be applied to the ideal thrust coefficient to
        get the real thrust coefficient.

        Returns:
            Thrust coefficient correction factor
        """
        pass

    @abstractmethod
    def get_thrust_coefficient(self, *args, **kwargs) -> float:
        """
        Calculates the thrust coefficient at a particular instant.

        Returns:
            Thrust coefficient
        """
        pass

    @property
    @abstractmethod
    def initial_propellant_mass(self) -> float:
        """
        Returns:
            Initial propellant mass, in kg
        """
        pass

    def get_thrust(self, cf: float, chamber_pressure: float) -> float:
        """
        Calculates the thrust based on instantaneous thrust coefficient and
        chamber pressure.

        Utilized nozzle throat area from the structure and nozzle classes.

        Args:
            cf: Instantaneous thrust coefficient, adimensional
            chamber_pressure: Instantaneous chamber pressure, in Pa

        Returns:
            Instantaneous thrust, in Newtons
        """
        return get_thrust_from_cf(
            cf,
            chamber_pressure,
            self.thrust_chamber.nozzle.get_throat_area(),
        )
