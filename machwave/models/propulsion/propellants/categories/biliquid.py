"""Liquid propellant categories (biliquid)."""

from dataclasses import dataclass, field

from machwave.services.cea import create_cea_service

from ..components import ComponentRole, PropellantComponent
from ..properties import ThermochemicalProperties
from .base import MixtureType, Propellant, PropellantValidationError


@dataclass
class BiliquidPropellant(Propellant):
    """Biliquid propellant with separate oxidizer and fuel.

    Attributes:
        properties: Pre-defined thermochemical properties (optional).
        of_ratio: Oxidizer-to-fuel mass ratio.
        oxidizer_tank_density: Oxidizer density [kg/m³].
        fuel_tank_density: Fuel density [kg/m³].
    """

    mixture_type: MixtureType = MixtureType.BILIQUID
    properties: ThermochemicalProperties | None = None
    of_ratio: float | None = None
    oxidizer_tank_density: float = field(default=0.0, init=False)
    fuel_tank_density: float = field(default=0.0, init=False)

    def _validate_components(self):
        """Validate biliquid has exactly 2 components: oxidizer and fuel.

        Raises:
            PropellantValidationError: If validation fails.
        """
        if not self.components or len(self.components) != 2:
            raise PropellantValidationError(
                f"Biliquid propellant '{self.name}' requires exactly two components"
            )

        _ = self._get_fuel()  # check fuel
        _ = self._get_oxidizer()  # check oxidizer

    def _get_fuel(self) -> PropellantComponent:
        """Get the fuel component."""
        for c in self.components:
            if c.role == ComponentRole.FUEL:
                return c
        raise PropellantValidationError(
            f"Biliquid propellant '{self.name}' has no fuel component"
        )

    def _get_oxidizer(self) -> PropellantComponent:
        """Get the oxidizer component."""
        for c in self.components:
            if c.role == ComponentRole.OXIDIZER:
                return c
        raise PropellantValidationError(
            f"Biliquid propellant '{self.name}' has no oxidizer component"
        )

    def _get_thermochemical_service(self):
        """Create RocketCEA service for biliquid propellant.

        Returns:
            RocketCEAService instance.
        """
        fuel = self._get_fuel()
        oxidizer = self._get_oxidizer()

        return create_cea_service(
            oxidizer_name=oxidizer.name,
            fuel_name=fuel.name,
            oxidizer_to_fuel_ratio=self.of_ratio,
        )

    def evaluate(
        self, chamber_pressure: float, expansion_ratio: float = 8.0
    ) -> ThermochemicalProperties:
        """Evaluate thermochemical properties.

        If properties are pre-defined, returns them directly.
        Otherwise, evaluates using the thermochemical service via parent class.

        Args:
            chamber_pressure: Chamber pressure [Pa].
            expansion_ratio: Nozzle area expansion ratio (Ae/At).

        Returns:
            ThermochemicalProperties: Pre-defined or calculated properties.

        Raises:
            PropellantValidationError: If evaluation fails.
        """
        if self.properties is not None:
            return self.properties
        return super().evaluate(chamber_pressure, expansion_ratio)
