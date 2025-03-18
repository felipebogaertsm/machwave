from abc import ABC, abstractmethod

import numpy as np

from machwave.models.propulsion.grain import Grain
from machwave.models.propulsion.propellants import Propellant
from machwave.models.propulsion.propellants.solid import SolidPropellant
from machwave.models.propulsion.structure import MotorStructure
from machwave.services.isentropic_flow import (
    get_thrust_coefficients,
    get_thrust_from_cf,
)


class Motor(ABC):
    """
    Abstract rocket motor/engine class. Can be used to model any chemical
    rocket propulsion system, such as Solid, Hybrid and Liquid.
    """

    def __init__(
        self,
        propellant: Propellant,
        structure: MotorStructure,
    ) -> None:
        """
        Instantiates object attributes common to any motor/engine (Solid,
        Hybrid or Liquid).

        Args:
            propellant: Object representing the propellant used in the motor.
            structure: Object representing the structure of the motor.
        """
        self.propellant = propellant
        self.structure = structure

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
            self.structure.nozzle.get_throat_area(),
        )


class SolidMotor(Motor):
    def __init__(
        self,
        grain: Grain,
        propellant: SolidPropellant,
        structure: MotorStructure,
    ) -> None:
        self.grain = grain
        super().__init__(propellant, structure)

        self.propellant: SolidPropellant = propellant
        self.cf_ideal = None  # ideal thrust coefficient
        self.cf_real = None  # real thrust coefficient

    def get_free_chamber_volume(self, propellant_volume: float) -> float:
        """
        Calculates the chamber volume without any propellant.

        Args:
            propellant_volume: Propellant volume, in m^3

        Returns:
            Free chamber volume, in m^3
        """
        return self.structure.chamber.empty_volume - propellant_volume

    @property
    def initial_propellant_mass(self) -> float:
        """
        Returns:
            Initial propellant mass, in kg
        """
        return (
            self.grain.get_propellant_volume(web_distance=0) * self.propellant.density
        )

    def get_thrust_coefficient_correction_factor(
        self, n_kin: float, n_bl: float, n_tp: float
    ) -> float:
        """
        Args:
            n_kin: Kinematic correction factor, adimensional
            n_bl: Boundary layer correction factor, adimensional
            n_tp: Two-phase correction factor, adimensional

        Returns:
            float: Thrust coefficient correction factor, adimensional
        """
        return (
            (100 - (n_kin + n_bl + n_tp))
            * self.structure.nozzle.get_divergent_correction_factor()
            / 100
            * self.propellant.combustion_efficiency
        )

    def get_thrust_coefficient(
        self,
        chamber_pressure: float,
        exit_pressure: float,
        external_pressure: float,
        expansion_ratio: float,
        k_2ph_ex: float,
        n_cf: float,
    ) -> float:
        """
        Args:
            chamber_pressure: Chamber pressure, in Pa
            exit_pressure: Exit pressure, in Pa
            external_pressure: External pressure, in Pa
            expansion_ratio: Expansion ratio, adimensional
            k_2ph_ex: Two-phase isentropic coefficient, adimensional
            n_cf: Thrust coefficient correction factor, adimensional

        Returns:
            Instanteneous thrust coefficient, adimensional
        """
        self.cf_ideal, self.cf_real = get_thrust_coefficients(
            chamber_pressure,
            exit_pressure,
            external_pressure,
            expansion_ratio,
            k_2ph_ex,
            n_cf,
        )
        return self.cf_real

    def get_launch_mass(self) -> float:
        return self.structure.dry_mass + self.initial_propellant_mass

    def get_dry_mass(self) -> float:
        return self.structure.dry_mass

    def get_center_of_gravity(self) -> np.typing.NDArray[np.float64]:
        """
        Constant CG throughout the operation. Half the chamber length.

        TODO: implement grain CG calculation.
        """
        return np.array([self.structure.chamber.length / 2, 0.0, 0.0], dtype=np.float64)
