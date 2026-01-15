import numpy as np

from machwave.core.flow.isentropic import get_ideal_thrust_coefficient
from machwave.models.propulsion.feed_systems.base import FeedSystem
from machwave.models.propulsion.propellants import BiliquidPropellant
from machwave.models.propulsion.thrust_chamber import LiquidEngineThrustChamber

from .base import Motor


class LiquidEngine(Motor[BiliquidPropellant, LiquidEngineThrustChamber]):
    def __init__(
        self,
        propellant: BiliquidPropellant,
        thrust_chamber: LiquidEngineThrustChamber,
        feed_system: FeedSystem,
        oxidizer_tank_cog: float | None = None,
        fuel_tank_cog: float | None = None,
        other_losses: float = 12.0,
    ) -> None:
        """
        Initialize a liquid rocket engine.

        Args:
            propellant: Bi-liquid propellant properties (oxidizer + fuel).
            thrust_chamber: Thrust chamber assembly (nozzle + combustion chamber + injector).
            feed_system: Propellant feed system (tanks, lines, pumps/pressurization).
            oxidizer_tank_cog: Axial position of the oxidizer tank center (where propellant CoG is),
                measured from the nozzle exit, in meters. If None, uses a default estimate.
            fuel_tank_cog: Axial position of the fuel tank center (where propellant CoG is),
                measured from the nozzle exit, in meters. If None, uses a default estimate.
            other_losses: Additional engine losses not accounted for by specific
                loss mechanisms, in percent. Defaults to 12%.
        """
        super().__init__(propellant, thrust_chamber, other_losses)
        self.feed_system = feed_system
        self.oxidizer_tank_cog = oxidizer_tank_cog
        self.fuel_tank_cog = fuel_tank_cog

    @property
    def initial_propellant_mass(self) -> float:
        """
        Returns the initial propellant mass in kg.
        """
        return self.feed_system.get_propellant_mass()

    def get_launch_mass(self) -> float:
        return self.thrust_chamber.dry_mass + self.initial_propellant_mass

    def get_dry_mass(self) -> float:
        return self.thrust_chamber.dry_mass

    def get_center_of_gravity(
        self, propellant_fraction: float = 0.0
    ) -> np.typing.NDArray[np.float64]:
        """
        Calculate the center of gravity of the liquid engine including structural
        dry mass, oxidizer, and fuel.

        The calculation uses a mass-weighted average of:
        1. Structural dry mass (thrust chamber, tanks structure, feed lines, etc.)
        2. Oxidizer mass (from oxidizer tank)
        3. Fuel mass (from fuel tank)

        Args:
            propellant_fraction: Fraction of propellant consumed (0.0 = full, 1.0 = empty).

        Returns:
            Center of gravity in 3D space [x, y, z], in meters.
            Origin is at the nozzle exit on the chamber axis.
            Positive x-direction points forward (toward bulkhead/away from nozzle exit).

        Raises:
            ValueError: If thrust_chamber.center_of_gravity_coordinate, oxidizer_tank_cog,
                or fuel_tank_cog is not defined.
        """
        # Get current propellant masses
        initial_ox_mass = self.feed_system.oxidizer_tank.initial_fluid_mass
        initial_fuel_mass = self.feed_system.fuel_tank.initial_fluid_mass

        ox_mass = initial_ox_mass * (1.0 - propellant_fraction)
        fuel_mass = initial_fuel_mass * (1.0 - propellant_fraction)

        # Structural dry mass (thrust chamber, tank structure, feed lines, etc.)
        dry_mass = self.thrust_chamber.dry_mass

        if self.thrust_chamber.center_of_gravity_coordinate is None:
            raise ValueError(
                "Thrust chamber center of gravity coordinate is not defined."
            )

        dry_cog = self.thrust_chamber.center_of_gravity_coordinate

        # Oxidizer tank CoG
        if self.oxidizer_tank_cog is None:
            raise ValueError("Oxidizer tank center of gravity is not defined.")

        ox_cog = np.array([self.oxidizer_tank_cog, 0.0, 0.0], dtype=np.float64)

        # Fuel tank CoG
        if self.fuel_tank_cog is None:
            raise ValueError("Fuel tank center of gravity is not defined.")

        fuel_cog = np.array([self.fuel_tank_cog, 0.0, 0.0], dtype=np.float64)

        # Calculate total mass and weighted CoG
        total_mass = dry_mass + ox_mass + fuel_mass

        if total_mass <= 0:
            # Fallback if calculation fails
            return dry_cog

        weighted_cog = (
            dry_cog * dry_mass + ox_cog * ox_mass + fuel_cog * fuel_mass
        ) / total_mass

        return weighted_cog.astype(np.float64)

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
            chamber_pressure (float): Chamber pressure in Pa.
            exit_pressure (float): Exit pressure in Pa.
            external_pressure (float): External pressure in Pa.
            expansion_ratio (float): Expansion ratio, adimensional.
            k_ex (float): Two-phase isentropic coefficient, adimensional.
            n_cf (float): Thrust coefficient correction factor, adimensional.

        Returns:
            Instantaneous thrust coefficient.
        """
        cf_ideal = get_ideal_thrust_coefficient(
            chamber_pressure=chamber_pressure,
            exit_pressure=exit_pressure,
            external_pressure=external_pressure,
            expansion_ratio=expansion_ratio,
            k_ex=k_ex,
        )
        n_cf = self.get_thrust_coefficient_correction_factor()
        return cf_ideal * n_cf
