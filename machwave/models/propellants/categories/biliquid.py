"""Liquid propellant categories (biliquid)."""

import machwave.services.cea as cea_service

from .. import components as propellant_components
from .. import properties as propellant_properties
from . import base as propellant_base


class BiliquidPropellant(propellant_base.Propellant):
    """Biliquid propellant with separate oxidizer and fuel."""

    mixture_type = propellant_base.MixtureType.BILIQUID

    def __init__(
        self,
        name: str,
        components: list[propellant_components.PropellantComponent] | None = None,
        combustion_efficiency: float = 0.95,
        properties: propellant_properties.ThermochemicalProperties | None = None,
        oxidizer_to_fuel_ratio: float | None = None,
    ):
        """
        Initialize biliquid propellant.

        Args:
            name: Propellant name.
            components: Chemical components (should be exactly 2: oxidizer and fuel).
            combustion_efficiency: Efficiency factor (0-1).
            properties: Pre-defined thermochemical properties (optional).
            oxidizer_to_fuel_ratio: Oxidizer-to-fuel mass ratio for this
                formulation. Used as the default mixture_ratio at the
                thermochemical service layer; callers can override per-call
                via ``evaluate(mixture_ratio=...)``.
        """
        super().__init__(
            name=name,
            components=components,
            combustion_efficiency=combustion_efficiency,
        )
        self.properties = properties
        self.oxidizer_to_fuel_ratio = oxidizer_to_fuel_ratio
        self.oxidizer_tank_density: float = 0.0
        self.fuel_tank_density: float = 0.0

    def _validate_components(self):
        """
        Validate biliquid has exactly 2 components: oxidizer and fuel.

        Raises:
            PropellantValidationError: If validation fails.
        """
        if not self.components or len(self.components) != 2:
            raise propellant_base.PropellantValidationError(
                f"Biliquid propellant '{self.name}' requires exactly two components"
            )

        _ = self._get_fuel()  # check fuel
        _ = self._get_oxidizer()  # check oxidizer

    def _get_fuel(self) -> propellant_components.PropellantComponent:
        """Get the fuel component."""
        for c in self.components:
            if c.role == propellant_components.ComponentRole.FUEL:
                return c
        raise propellant_base.PropellantValidationError(
            f"Biliquid propellant '{self.name}' has no fuel component"
        )

    def _get_oxidizer(self) -> propellant_components.PropellantComponent:
        """Get the oxidizer component."""
        for c in self.components:
            if c.role == propellant_components.ComponentRole.OXIDIZER:
                return c
        raise propellant_base.PropellantValidationError(
            f"Biliquid propellant '{self.name}' has no oxidizer component"
        )

    def _get_thermochemical_service(self):
        """
        Create RocketCEA service for biliquid propellant.

        Returns:
            RocketCEAService instance.
        """
        fuel = self._get_fuel()
        oxidizer = self._get_oxidizer()

        return cea_service.create_cea_service(
            oxidizer_name=oxidizer.name,
            fuel_name=fuel.name,
            oxidizer_to_fuel_ratio=self.oxidizer_to_fuel_ratio,
        )
