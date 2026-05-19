from abc import ABC, abstractmethod

from machwave.models.feed_systems.tanks import Tank


class FeedSystem(ABC):
    """
    Abstract base class for a bipropellant feed system in a liquid rocket engine (LRE).

    This class is responsible for determining oxidizer and fuel mass flows as a function of tank/pressurant states,
    pumps (if any), and current chamber conditions. Subclasses must implement the abstract methods to specify the
    actual flow calculations.

    The mass-flow methods accept `discharge_coefficient` and `injector_area` as keyword-only arguments with
    `None` defaults. Pressure-fed cycles require both to evaluate the injector orifice equation. Cycles that
    schedule mass flow from pump curves or other internal logic can ignore them.
    """

    def __init__(self, fuel_tank: Tank, oxidizer_tank: Tank):
        """Initialize the FeedSystem with associated tank objects.

        Args:
            fuel_tank: Instance representing the fuel tank.
            oxidizer_tank: Instance representing the oxidizer tank.
        """
        self.fuel_tank = fuel_tank
        self.oxidizer_tank = oxidizer_tank

    def get_propellant_mass(self) -> float:
        """Compute and return the initial propellant mass in the system [kg]."""
        return self.fuel_tank.fluid_mass + self.oxidizer_tank.fluid_mass

    @abstractmethod
    def get_mass_flow_ox(
        self,
        chamber_pressure: float,
        *,
        discharge_coefficient: float | None = None,
        injector_area: float | None = None,
    ) -> float:
        """Compute and return the current oxidizer mass flow rate [kg/s].

        Args:
            chamber_pressure: Chamber pressure [Pa].
            discharge_coefficient: Oxidizer injector discharge coefficient (dimensionless).
            injector_area: Effective flow area for the oxidizer injector [m^2].

        Returns:
            Oxidizer mass flow rate [kg/s].
        """
        pass

    @abstractmethod
    def get_mass_flow_fuel(
        self,
        chamber_pressure: float,
        *,
        discharge_coefficient: float | None = None,
        injector_area: float | None = None,
    ) -> float:
        """Compute and return the current fuel mass flow rate [kg/s].

        Args:
            chamber_pressure: Chamber pressure [Pa].
            discharge_coefficient: Fuel injector discharge coefficient (dimensionless).
            injector_area: Effective flow area for the fuel injector [m^2].

        Returns:
            Fuel mass flow rate [kg/s].
        """
        pass

    @abstractmethod
    def get_oxidizer_tank_pressure(self) -> float:
        """Compute and return the current oxidizer tank pressure [Pa]."""
        pass

    @abstractmethod
    def get_fuel_tank_pressure(self) -> float:
        """Compute and return the current fuel tank pressure [Pa]."""
        pass
