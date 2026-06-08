import machwave.services.cea as cea_service

from .. import components as propellant_components
from .. import properties as propellant_properties
from . import base as propellant_base

MASS_FRACTION_SUM_TOLERANCE = 1e-6


class BurnRateOutOfBoundsError(Exception):
    """Raised when chamber pressure is outside burn rate model valid range."""

    def __init__(self, chamber_pressure: float):
        """
        Build the error from the offending chamber pressure.

        Args:
            chamber_pressure: Chamber pressure that is out of bounds [Pa].
        """
        super().__init__(
            f"Chamber pressure {chamber_pressure:.2e} Pa is outside the valid range "
            f"for this burn rate model."
        )


class SolidPropellant(propellant_base.Propellant):
    """Solid propellant with burn rate model."""

    mixture_type = propellant_base.MixtureType.SOLID

    def __init__(
        self,
        name: str,
        components: list[propellant_components.PropellantComponent] | None = None,
        mass_fractions: list[float] | None = None,
        properties: propellant_properties.ThermochemicalProperties | None = None,
        burn_rate_map: list[dict[str, float | int]] | None = None,
    ):
        """
        Initialize a solid propellant.

        Args:
            name: Propellant name.
            components: Chemical components. Required; must contain at least
                one oxidizer and one fuel.
            mass_fractions: Mass fractions aligned with `components`. Must
                sum to 1.0.
            properties: Pre-defined thermochemical properties. Optional
                override used by `evaluate()` to skip CEA when provided.
            burn_rate_map: Saint Robert's law coefficients by pressure range.

        Raises:
            PropellantValidationError: If components, mass_fractions, or
                their relationship is invalid.
        """
        super().__init__(
            name=name,
            components=components,
        )

        self._properties = properties
        self.burn_rate_map = burn_rate_map or []
        self.mass_fractions = mass_fractions or []
        self._validate_components()

    @property
    def properties(self) -> propellant_properties.ThermochemicalProperties | None:
        """Expose pre-defined thermochemical properties when present."""
        return self._properties

    def _validate_components(self):
        """
        Validate solid propellant components and mass fractions.

        Raises:
            PropellantValidationError: If validation fails.
        """
        if not self.components:
            raise propellant_base.PropellantValidationError(
                f"Solid propellant '{self.name}' requires `components`"
            )

        if not self.mass_fractions:
            raise propellant_base.PropellantValidationError(
                f"Solid propellant '{self.name}' requires `mass_fractions` for its "
                "components"
            )
        if len(self.mass_fractions) != len(self.components):
            raise propellant_base.PropellantValidationError(
                f"Solid propellant '{self.name}' `mass_fractions` length must match "
                "components length"
            )
        if any(mf < 0 for mf in self.mass_fractions):
            raise propellant_base.PropellantValidationError(
                f"Solid propellant '{self.name}' `mass_fractions` must be non-negative"
            )
        mf_sum = sum(self.mass_fractions)
        if abs(mf_sum - 1.0) > MASS_FRACTION_SUM_TOLERANCE:
            raise propellant_base.PropellantValidationError(
                f"Solid propellant '{self.name}' `mass_fractions` must sum to 1.0 (got "
                f"{mf_sum:.6f})"
            )

        has_oxidizer = any(
            c.role == propellant_components.ComponentRole.OXIDIZER
            for c in self.components
        )
        has_fuel = any(
            c.role == propellant_components.ComponentRole.FUEL for c in self.components
        )

        if not has_oxidizer:
            raise propellant_base.PropellantValidationError(
                f"Solid propellant '{self.name}' requires at least one oxidizer "
                "component"
            )
        if not has_fuel:
            raise propellant_base.PropellantValidationError(
                f"Solid propellant '{self.name}' requires at least one fuel component"
            )

    def _get_thermochemical_service(self):
        """
        Create a RocketCEA service from this propellant's components.

        Returns:
            RocketCEAService instance.
        """
        components_data = [
            comp.to_cea_dict(weight_percent=mf * 100.0)
            for comp, mf in zip(self.components, self.mass_fractions)
        ]
        card_string = cea_service.generate_card_string(components_data)
        return cea_service.create_cea_service(
            propellant_name=cea_service.normalize_custom_propellant_name(self.name),
            card_string=card_string,
            has_condensed_phase=self.has_condensed_phase,
        )

    def evaluate(
        self,
        chamber_pressure: float,
        expansion_ratio: float = 8.0,
        mixture_ratio: float | None = None,
    ) -> propellant_properties.ThermochemicalProperties:
        """
        Evaluate thermochemical properties.

        If properties are pre-defined, returns them directly. Otherwise,
        evaluates using the thermochemical service via the parent class.

        Args:
            chamber_pressure: Chamber pressure [Pa].
            expansion_ratio: Nozzle area expansion ratio (Ae/At).
            mixture_ratio: Per-call mixture ratio override. Unused for solid
                formulations; accepted for parent-class compatibility.

        Returns:
            Pre-defined or calculated properties.

        Raises:
            PropellantValidationError: If evaluation fails.
        """
        if self._properties is not None:
            return self._properties
        return super().evaluate(chamber_pressure, expansion_ratio, mixture_ratio)

    @property
    def ideal_density(self) -> float:
        """
        Return the ideal propellant density [kg/m^3] for solid mixtures.

        Uses a harmonic mean based on solid mixture mass fractions.
        """
        reciprocal_sum = sum(
            mf / comp.density for comp, mf in zip(self.components, self.mass_fractions)
        )
        return 1.0 / reciprocal_sum

    def get_burn_rate(self, chamber_pressure: float) -> float:
        """
        Return the instantaneous burn rate of the solid propellant.

        Uses Saint Robert's law `r = a * P^n`, where `r` is burn rate [m/s],
        `P` is chamber pressure [MPa], and `a`, `n` are empirical coefficients
        drawn from `burn_rate_map`.

        Args:
            chamber_pressure: Chamber pressure [Pa].

        Returns:
            Burn rate [m/s].

        Raises:
            BurnRateOutOfBoundsError: If pressure is outside the valid range.
            PropellantValidationError: If the burn rate model is not defined.
        """
        if not self.burn_rate_map:
            raise propellant_base.PropellantValidationError(
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
