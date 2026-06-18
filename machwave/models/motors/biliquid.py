import numpy as np

import machwave.models.feed_systems.base as feed_system_base
import machwave.models.losses as losses
import machwave.models.propellants as propellants
import machwave.models.thrust_chamber as thrust_chamber_models

from . import base as motor_base


class BiliquidEngine(
    motor_base.Motor[
        propellants.BiliquidPropellant,
        thrust_chamber_models.BiliquidEngineThrustChamber,
    ]
):
    """Biliquid rocket engine with a bipropellant feed system."""

    def __init__(
        self,
        propellant: propellants.BiliquidPropellant,
        thrust_chamber: thrust_chamber_models.BiliquidEngineThrustChamber,
        feed_system: feed_system_base.FeedSystem,
        oxidizer_tank_cog: float | None = None,
        fuel_tank_cog: float | None = None,
        combustion_efficiency: float = 0.95,
        nozzle_loss_model: losses.NozzleLossModel | None = None,
    ) -> None:
        """
        Initialize a biliquid rocket engine.

        Args:
            propellant: Biliquid propellant properties (oxidizer + fuel).
            thrust_chamber: Thrust chamber assembly (nozzle, combustion chamber,
                injector).
            feed_system: Propellant feed system (tanks, lines, pumps or
                pressurization).
            oxidizer_tank_cog: Axial position of the oxidizer propellant center
                of gravity, measured from the nozzle exit [m]. If None, uses a
                default estimate.
            fuel_tank_cog: Axial position of the fuel propellant center of
                gravity, measured from the nozzle exit [m]. If None, uses a
                default estimate.
            combustion_efficiency: Ratio of the actual flame temperature to the ideal
                adiabatic flame temperature (0, 1].
            nozzle_loss_model: Nozzle loss model. Defaults to the Solid
                Performance Program 1975 biliquid set.
        """
        super().__init__(
            propellant,
            thrust_chamber,
            combustion_efficiency,
            nozzle_loss_model=nozzle_loss_model or losses.spp1975_biliquid_loss_model(),
        )
        self.feed_system = feed_system
        self.oxidizer_tank_cog = oxidizer_tank_cog
        self.fuel_tank_cog = fuel_tank_cog

    @property
    def initial_propellant_mass(self) -> float:
        """Return the initial propellant mass [kg]."""
        return self.feed_system.get_initial_propellant_mass()

    def get_launch_mass(self) -> float:
        """Return the launch mass (dry mass + initial propellant) [kg]."""
        return self.thrust_chamber.dry_mass + self.initial_propellant_mass

    def get_dry_mass(self) -> float:
        """Return the dry mass [kg]."""
        return self.thrust_chamber.dry_mass

    def get_center_of_gravity(
        self, propellant_fraction: float = 0.0
    ) -> np.typing.NDArray[np.float64]:
        """
        Return the engine center of gravity.

        Combines structural dry mass, oxidizer, and fuel via a mass-weighted
        average. Origin is at the nozzle exit on the chamber axis with
        positive x pointing forward (toward bulkhead).

        Args:
            propellant_fraction: Fraction of propellant consumed (0.0 = full,
                1.0 = empty).

        Returns:
            Center of gravity as `(x, y, z)` [m].

        Raises:
            ValueError: If `thrust_chamber.center_of_gravity_coordinate`,
                `oxidizer_tank_cog`, or `fuel_tank_cog` is not defined.
        """
        initial_ox_mass = self.feed_system.oxidizer_tank.initial_fluid_mass
        initial_fuel_mass = self.feed_system.fuel_tank.initial_fluid_mass

        ox_mass = initial_ox_mass * (1.0 - propellant_fraction)
        fuel_mass = initial_fuel_mass * (1.0 - propellant_fraction)

        dry_mass = self.thrust_chamber.dry_mass

        if self.thrust_chamber.center_of_gravity_coordinate is None:
            raise ValueError(
                "Thrust chamber center of gravity coordinate is not defined."
            )

        dry_cog = self.thrust_chamber.center_of_gravity_coordinate

        if self.oxidizer_tank_cog is None:
            raise ValueError("Oxidizer tank center of gravity is not defined.")

        ox_cog = np.array([self.oxidizer_tank_cog, 0.0, 0.0], dtype=np.float64)

        if self.fuel_tank_cog is None:
            raise ValueError("Fuel tank center of gravity is not defined.")

        fuel_cog = np.array([self.fuel_tank_cog, 0.0, 0.0], dtype=np.float64)

        total_mass = dry_mass + ox_mass + fuel_mass

        if total_mass <= 0:
            return dry_cog

        weighted_cog = (
            dry_cog * dry_mass + ox_cog * ox_mass + fuel_cog * fuel_mass
        ) / total_mass

        return weighted_cog.astype(np.float64)
