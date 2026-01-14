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
        dry_mass_cog: float | None = None,
        other_losses: float = motor_base.DEFAULT_OTHER_MOTOR_LOSSES,
    ) -> None:
        """
        Initialize a solid rocket motor.

        Args:
            grain: Grain geometry configuration.
            propellant: Solid propellant properties.
            thrust_chamber: Thrust chamber model.
            dry_mass_cog: Axial position of the dry mass (hardware) center of gravity,
                measured from the nozzle throat, in meters. Positive values point toward
                the bulkhead. If None, will be estimated from chamber geometry.
            other_losses: Additional motor losses not accounted for by specific
                loss mechanisms (0-1), defaults to 0.12 (12%).
        """
        super().__init__(propellant, thrust_chamber, other_losses)

        self.grain = grain
        self.propellant: propellants.SolidPropellant = propellant
        self.dry_mass_cog = dry_mass_cog
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
        Calculates the thrust coefficient correction factor including all
        losses.

        Args:
            n_kin: Kinematic correction factor, adimensional, in percent
            n_bl: Boundary layer correction factor, adimensional, in percent
            n_tp: Two-phase correction factor, adimensional, in percent

        Returns:
            Thrust coefficient correction factor, adimensional
        """
        return (
            (100 - (n_kin + n_bl + n_tp + self.other_losses))
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

    def get_center_of_gravity(
        self, web_distance: float = 0.0
    ) -> np.typing.NDArray[np.float64]:
        """
        Calculates the center of gravity of the solid motor including
        propellant grain (wet mass) and dry mass.

        The calculation uses a mass-weighted average of:
        1. Propellant grain CoG;
        2. Thrust chamber dry mass CoG, considered constant.

        Args:
            web_distance: Web distance traveled [m].
                Defaults to 0.0 (ignition state).

        Returns:
            Center of gravity in 3D space (x, y, z) [m].
        """
        grain_cog_port = self.grain.get_center_of_gravity(web_distance=web_distance)
        propellant_mass = self.grain.get_propellant_mass(
            web_distance=web_distance, ideal_density=self.propellant.ideal_density
        )

        dry_mass = self.thrust_chamber.dry_mass
        nozzle_exit_to_port = self.thrust_chamber.nozzle_exit_to_grain_port_distance

        # Transform grain CoG from port origin to nozzle exit origin
        grain_cog = grain_cog_port.copy()
        grain_cog[0] = nozzle_exit_to_port + grain_cog_port[0]

        if self.dry_mass_cog is not None:
            # User-provided dry mass CoG (already in throat-origin coordinates)
            hardware_cog = np.array([self.dry_mass_cog, 0.0, 0.0], dtype=np.float64)
        else:
            # Estimate hardware CoG from chamber geometry
            # Assume it's at the geometric center of the combustion chamber
            chamber_length = self.thrust_chamber.combustion_chamber.internal_length
            grain_total_length = self.grain.total_length
            # Distance from port to chamber center
            chamber_center_from_port = grain_total_length - (
                chamber_length / 2 - (chamber_length - grain_total_length)
            )
            hardware_cog = np.array(
                [nozzle_exit_to_port + chamber_center_from_port, 0.0, 0.0],
                dtype=np.float64,
            )

        # Calculate total mass and weighted CoG
        total_mass = propellant_mass + dry_mass

        if total_mass <= 0:
            # Fallback to hardware CoG if calculation fails
            return hardware_cog

        weighted_cog = (
            grain_cog * propellant_mass + hardware_cog * dry_mass
        ) / total_mass

        return weighted_cog.astype(np.float64)
