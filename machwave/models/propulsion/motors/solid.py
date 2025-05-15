import numpy as np

from machwave.models.propulsion.grain import Grain
from machwave.models.propulsion.propellants.solid import SolidPropellant
from machwave.models.propulsion.thrust_chamber import SolidMotorThrustChamber
from machwave.services.flow.isentropic import get_thrust_coefficients

from .base import Motor


class SolidMotor(Motor[SolidPropellant, SolidMotorThrustChamber]):
    def __init__(
        self,
        grain: Grain,
        propellant: SolidPropellant,
        thrust_chamber: SolidMotorThrustChamber,
    ) -> None:
        self.grain = grain
        super().__init__(propellant, thrust_chamber)

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
        return (
            self.thrust_chamber.combustion_chamber.internal_volume - propellant_volume
        )

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
            * self.thrust_chamber.nozzle.get_divergent_correction_factor()
            / 100
            * self.propellant.combustion_efficiency
        )

    def get_thrust_coefficient(
        self,
        chamber_pressure: float,
        exit_pressure: float,
        external_pressure: float,
        expansion_ratio: float,
        k_ex: float,
        n_cf: float,
    ) -> float:
        """
        Args:
            chamber_pressure: Chamber pressure, in Pa
            exit_pressure: Exit pressure, in Pa
            external_pressure: External pressure, in Pa
            expansion_ratio: Expansion ratio, adimensional
            k_ex: Two-phase isentropic coefficient, adimensional
            n_cf: Thrust coefficient correction factor, adimensional

        Returns:
            Instanteneous thrust coefficient, adimensional
        """
        self.cf_ideal, self.cf_real = get_thrust_coefficients(
            chamber_pressure,
            exit_pressure,
            external_pressure,
            expansion_ratio,
            k_ex,
            n_cf,
        )
        return self.cf_real

    def get_launch_mass(self) -> float:
        return self.thrust_chamber.dry_mass + self.initial_propellant_mass

    def get_dry_mass(self) -> float:
        return self.thrust_chamber.dry_mass

    def get_center_of_gravity(self) -> np.typing.NDArray[np.float64]:
        """
        Constant CG throughout the operation. Half the chamber length.

        TODO: implement grain CG calculation.
        """
        return np.array(
            [self.thrust_chamber.combustion_chamber.internal_length / 2, 0.0, 0.0],
            dtype=np.float64,
        )
