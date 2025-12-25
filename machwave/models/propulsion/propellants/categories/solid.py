"""Solid propellant category."""

from machwave.services.cea import create_cea_service, generate_card_string

from ..components import ComponentRole, PropellantComponent
from ..properties import ThermochemicalProperties
from .base import MixtureType, Propellant, PropellantValidationError

MASS_FRACTION_SUM_TOLERANCE = 1e-6


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


class SolidPropellant(Propellant):
    """Solid propellant with burn rate model."""

    def __init__(
        self,
        name: str,
        components: list[PropellantComponent] | None = None,
        mass_fractions: list[float] | None = None,
        combustion_efficiency: float = 0.95,
        properties: ThermochemicalProperties | None = None,
        burn_rate_map: list[dict[str, float | int]] | None = None,
    ):
        """Initialize solid propellant. If components are not provided,
        properties must be defined and vice-versa.

        Args:
            name: Propellant name.
            components: Chemical components (optional).
            combustion_efficiency: Efficiency factor (0-1).
            properties: Pre-defined thermochemical properties (optional).
            burn_rate: St. Robert's law coefficients by pressure range.
        """
        super().__init__(
            name=name,
            mixture_type=MixtureType.SOLID,
            components=components,
            combustion_efficiency=combustion_efficiency,
        )
        self._properties = properties
        self.burn_rate_map = burn_rate_map if burn_rate_map is not None else []
        self.mass_fractions = mass_fractions if mass_fractions is not None else []

    @property
    def properties(self) -> ThermochemicalProperties | None:
        """Expose pre-defined thermochemical properties when present."""
        return self._properties

    def _validate_components(self):
        """Validate solid propellant has oxidizer and fuel.

        Raises:
            PropellantValidationError: If validation fails.
        """
        # Allow empty components if properties are pre-defined (for formulations)
        if not self.components:
            if self._properties is None:
                raise PropellantValidationError(
                    f"Solid propellant '{self.name}' has no components or pre-defined "
                    "properties"
                )
            return

        if not self.mass_fractions:
            raise PropellantValidationError(
                f"Solid propellant '{self.name}' requires mass_fractions for its "
                "components"
            )
        if len(self.mass_fractions) != len(self.components):
            raise PropellantValidationError(
                f"Solid propellant '{self.name}' mass_fractions length must match "
                "components length"
            )
        if any(mf < 0 for mf in self.mass_fractions):
            raise PropellantValidationError(
                f"Solid propellant '{self.name}' mass_fractions must be non-negative"
            )
        mf_sum = sum(self.mass_fractions)
        if abs(mf_sum - 1.0) > MASS_FRACTION_SUM_TOLERANCE:
            raise PropellantValidationError(
                f"Solid propellant '{self.name}' mass_fractions must sum to 1.0 (got "
                f"{mf_sum:.6f})"
            )

        has_oxidizer = any(c.role == ComponentRole.OXIDIZER for c in self.components)
        has_fuel = any(c.role == ComponentRole.FUEL for c in self.components)

        if not has_oxidizer:
            raise PropellantValidationError(
                f"Solid propellant '{self.name}' requires at least one oxidizer "
                "component"
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
            self._validate_components()
            # Convert components to CEA format
            components_data = [
                comp.to_cea_dict(weight_percent=mf * 100.0)
                for comp, mf in zip(self.components, self.mass_fractions)
            ]
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
        if self._properties is not None:
            return self._properties
        return super().evaluate(chamber_pressure, expansion_ratio)

    @property
    def ideal_density(self) -> float:
        """Calculate ideal propellant density [kg/m³] for solid mixtures.

        Uses harmonic mean based on solid mixture mass fractions.
        """
        self._validate_components()
        reciprocal_sum = sum(
            mf / comp.density for comp, mf in zip(self.components, self.mass_fractions)
        )
        return 1.0 / reciprocal_sum

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
        if not self.burn_rate_map:
            raise PropellantValidationError(
                f"Burn rate model not defined for propellant '{self.name}'"
            )

        for item in self.burn_rate_map:
            if item["min"] <= chamber_pressure <= item["max"]:
                a = item["a"]
                n = item["n"]
                # Convert pressure from Pa to MPa, apply St. Robert's law,
                # then convert from mm/s to m/s
                return (a * (chamber_pressure * 1e-6) ** n) * 1e-3

        raise BurnRateOutOfBoundsError(chamber_pressure)
