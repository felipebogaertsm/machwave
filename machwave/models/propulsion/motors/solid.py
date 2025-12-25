import numpy as np

import machwave.core.flow.isentropic as isentropic
import machwave.core.losses as losses
import machwave.models.propulsion.grain as grain
import machwave.models.propulsion.propellants as propellants
import machwave.models.propulsion.thrust_chamber as thrust_chamber

from . import base as motor_base


class SolidMotor(
    motor_base.Motor[
        propellants.SolidPropellant, thrust_chamber.SolidMotorThrustChamber
    ]
):
    def __init__(
        self,
        grain: grain.Grain,
        propellant: propellants.SolidPropellant,
        thrust_chamber: thrust_chamber.SolidMotorThrustChamber,
    ) -> None:
        self.grain = grain
        super().__init__(propellant, thrust_chamber)

        self.propellant: propellants.SolidPropellant = propellant
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
        return self.grain.get_propellant_mass(
            web_distance=0, ideal_density=self.propellant.ideal_density
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
            * losses.get_nozzle_divergent_percentage_loss(
                self.thrust_chamber.nozzle.throat_diameter
            )
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
        self.cf_ideal, self.cf_real = isentropic.get_thrust_coefficients(
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
