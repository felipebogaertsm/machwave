import numpy as np

import machwave.models.grain as grain
import machwave.models.nozzle_losses as nozzle_losses
import machwave.models.propellants as propellants
import machwave.models.thrust_chamber as thrust_chamber

from . import base as motor_base


class SolidMotor(
    motor_base.Motor[
        propellants.SolidPropellant, thrust_chamber.SolidMotorThrustChamber
    ]
):
    """Solid rocket motor with a propellant grain and thrust chamber."""

    def __init__(
        self,
        grain: grain.Grain,
        propellant: propellants.SolidPropellant,
        thrust_chamber: thrust_chamber.SolidMotorThrustChamber,
        combustion_efficiency: float = 0.95,
        nozzle_loss_model: nozzle_losses.NozzleLossModel | None = None,
    ) -> None:
        """
        Initialize a solid rocket motor.

        Args:
            grain: Grain geometry configuration.
            propellant: Solid propellant properties.
            thrust_chamber: Thrust chamber model.
            combustion_efficiency: Ratio of the actual flame temperature to the ideal
                adiabatic flame temperature (0, 1].
            nozzle_loss_model: Nozzle loss model. Defaults to the Solid
                Performance Program 1975 solid set.
        """
        super().__init__(
            propellant,
            thrust_chamber,
            combustion_efficiency,
            nozzle_loss_model=nozzle_loss_model
            or nozzle_losses.presets.spp1975_solid_loss_model(),
        )

        self.grain = grain
        self.propellant: propellants.SolidPropellant = propellant

    def get_free_chamber_volume(self, propellant_volume: float) -> float:
        """
        Return the chamber volume without any propellant.

        Args:
            propellant_volume: Propellant volume [m^3].

        Returns:
            Free chamber volume [m^3].
        """
        return (
            self.thrust_chamber.combustion_chamber.internal_volume - propellant_volume
        )

    @property
    def initial_propellant_mass(self) -> float:
        """Return the initial propellant mass [kg]."""
        return self.grain.get_propellant_mass(
            web_distance=0, ideal_density=self.propellant.ideal_density
        )

    def get_launch_mass(self) -> float:
        """Return the launch mass (dry mass + initial propellant) [kg]."""
        return self.thrust_chamber.dry_mass + self.initial_propellant_mass

    def get_dry_mass(self) -> float:
        """Return the dry mass [kg]."""
        return self.thrust_chamber.dry_mass

    def get_center_of_gravity(
        self, web_distance: float = 0.0
    ) -> np.typing.NDArray[np.float64]:
        """
        Return the solid motor center of gravity.

        Combines the propellant grain (wet mass) and the thrust chamber dry
        mass via a mass-weighted average. Dry mass center of gravity is
        considered constant.

        Args:
            web_distance: Web distance traveled [m]. Defaults to ignition state.

        Returns:
            Center of gravity as `(x, y, z)` [m].

        Raises:
            ValueError: If the thrust chamber dry mass center of gravity is not
                defined or if the total mass is not strictly positive.
        """
        grain_cog_port = self.grain.get_center_of_gravity(web_distance=web_distance)
        propellant_mass = self.grain.get_propellant_mass(
            web_distance=web_distance, ideal_density=self.propellant.ideal_density
        )

        dry_mass = self.thrust_chamber.dry_mass
        dry_mass_cog = self.thrust_chamber.center_of_gravity_coordinate
        nozzle_exit_to_port = self.thrust_chamber.nozzle_exit_to_grain_port_distance

        # Transform grain CoG from port origin to nozzle exit origin
        grain_cog = grain_cog_port.copy()
        grain_cog[0] = nozzle_exit_to_port + grain_cog_port[0]

        if dry_mass_cog is None:
            raise ValueError("Dry mass center of gravity coordinate is not defined.")

        total_mass = propellant_mass + dry_mass
        if total_mass <= 0:
            raise ValueError("Total mass must be greater than zero to calculate CoG.")

        weighted_cog = (
            grain_cog * propellant_mass + dry_mass_cog * dry_mass
        ) / total_mass

        return weighted_cog.astype(np.float64)
