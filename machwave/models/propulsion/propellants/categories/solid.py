"""Solid propellant category."""

from dataclasses import dataclass, field

from machwave.services.cea import create_cea_service, generate_card_string

from ..components import ComponentRole
from ..properties import ThermochemicalProperties
from .base import MixtureType, Propellant, PropellantValidationError


class BurnRateOutOfBoundsError(Exception):
    """Raised when chamber pressure is outside burn rate model valid range."""

    def __init__(self, chamber_pressure: float):
        """
        Args:
            chamber_pressure: Chamber pressure that is out of bounds [Pa].
        """
        super().__init__(
            f"Chamber pressure {chamber_pressure:.2e} Pa is outside the valid range "
            f"for this burn rate model."
        )


@dataclass
class SolidPropellant(Propellant):
    """Solid propellant with burn rate model.

    Attributes:
        properties: Pre-defined thermochemical properties (optional).
        burn_rate: St. Robert's law coefficients by pressure range.
    """

    mixture_type: MixtureType = MixtureType.SOLID
    properties: ThermochemicalProperties | None = None
    burn_rate: list[dict[str, float | int]] = field(default_factory=list)

    def _validate_components(self):
        """Validate solid propellant has oxidizer and fuel.

        Raises:
            PropellantValidationError: If validation fails.
        """
        # Allow empty components if properties are pre-defined (for formulations)
        if not self.components:
            if self.properties is None:
                raise PropellantValidationError(
                    f"Solid propellant '{self.name}' has no components or pre-defined properties"
                )
            return

        has_oxidizer = any(c.role == ComponentRole.OXIDIZER for c in self.components)
        has_fuel = any(c.role == ComponentRole.FUEL for c in self.components)

        if not has_oxidizer:
            raise PropellantValidationError(
                f"Solid propellant '{self.name}' requires at least one oxidizer component"
            )
        if not has_fuel:
            raise PropellantValidationError(
                f"Solid propellant '{self.name}' requires at least one fuel component"
            )

    def _get_thermochemical_service(self):
        """Create RocketCEA service from components.

        Returns:
            RocketCEAService instance.
        """
        if self.components:
            # Convert components to CEA format
            components_data = [comp.to_cea_dict() for comp in self.components]
            card_string = generate_card_string(components_data)
            return create_cea_service(
                propellant_name=self.name.replace(" ", "_").upper(),
                card_string=card_string,
            )
        else:
            raise PropellantValidationError(
                f"Cannot create thermochemical service without components for "
                f"propellant '{self.name}'"
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

    def get_burn_rate(self, chamber_pressure: float) -> float:
        """Calculate instantaneous burn rate for solid propellants.

        Uses St. Robert's law: r = a * P^n, where r is burn rate [m/s],
        P is chamber pressure [MPa], and a, n are empirical coefficients.

        Args:
            chamber_pressure: Chamber pressure [Pa].

        Returns:
            float: Burn rate [m/s].

        Raises:
            BurnRateOutOfBoundsError: If pressure is outside valid range.
            ValueError: If burn_rate model is not defined.
        """
        if not self.burn_rate:
            raise PropellantValidationError(
                f"Burn rate model not defined for propellant '{self.name}'"
            )

        for item in self.burn_rate:
            if item["min"] <= chamber_pressure <= item["max"]:
                a = item["a"]
                n = item["n"]
                # Convert pressure from Pa to MPa, apply St. Robert's law,
                # then convert from mm/s to m/s
                return (a * (chamber_pressure * 1e-6) ** n) * 1e-3

        raise BurnRateOutOfBoundsError(chamber_pressure)

    def real_density(self, porosity: float = 0.0) -> float:
        """Get real propellant density accounting for porosity.

        Args:
            porosity: Porosity fraction (0.0 to 1.0). Default is 0.0 (no porosity).

        Returns:
            float: Real density [kg/m³] = ideal_density * (1 - porosity).

        Raises:
            ValueError: If porosity is outside valid range [0, 1).
        """
        if not (0.0 <= porosity < 1.0):
            raise ValueError(f"Porosity must be in range [0, 1), got {porosity}")
        return self.ideal_density * (1.0 - porosity)
