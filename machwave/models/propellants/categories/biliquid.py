"""Liquid propellant categories (biliquid)."""

from machwave.services.cea import create_cea_service

from ..components import ComponentRole, PropellantComponent
from ..properties import ThermochemicalProperties
from .base import MixtureType, Propellant, PropellantValidationError


class BiliquidPropellant(Propellant):
    """Biliquid propellant with separate oxidizer and fuel."""

    mixture_type = MixtureType.BILIQUID

    def __init__(
        self,
        name: str,
        components: list[PropellantComponent] | None = None,
        combustion_efficiency: float = 0.95,
        properties: ThermochemicalProperties | None = None,
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
        """
        Create RocketCEA service for biliquid propellant.

        Returns:
            RocketCEAService instance.
        """
        fuel = self._get_fuel()
        oxidizer = self._get_oxidizer()

        return create_cea_service(
            oxidizer_name=oxidizer.name,
            fuel_name=fuel.name,
            oxidizer_to_fuel_ratio=self.oxidizer_to_fuel_ratio,
        )
