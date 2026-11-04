from .. import components as propellant_components
from . import base as propellant_base


class BiliquidPropellant(propellant_base.Propellant):
    """Biliquid propellant with separate oxidizer and fuel."""

    mixture_type = propellant_base.MixtureType.BILIQUID

    def __init__(
        self,
        name: str,
        components: list[propellant_components.PropellantComponent] | None = None,
        oxidizer_to_fuel_ratio: float | None = None,
    ):
        """
        Initialize biliquid propellant.

        Args:
            name: Propellant name.
            components: Chemical components (should be exactly 2: oxidizer and fuel).
            oxidizer_to_fuel_ratio: Oxidizer-to-fuel mass ratio for this
                formulation. Used as the default mixture_ratio at the
                thermochemical service layer; callers can override per-call
                via ``evaluate(mixture_ratio=...)``.

        Raises:
            PropellantValidationError: If components do not include exactly
                one oxidizer and one fuel.
        """
        super().__init__(
            name=name,
            components=components,
        )

        self.oxidizer_to_fuel_ratio = oxidizer_to_fuel_ratio
        self._validate_components()

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

        Raises:
            ValueError: If creating the CEA object for the oxidizer and fuel
                fails.
            MissingOptionalDependencyError: If the `cea` extra is not installed.
        """
        import machwave.services.cea as cea_service

        fuel = self._get_fuel()
        oxidizer = self._get_oxidizer()
        oxidizer_name, oxidizer_card = self._get_reactant(oxidizer, "oxid")
        fuel_name, fuel_card = self._get_reactant(fuel, "fuel")

        return cea_service.create_cea_service(
            oxidizer_name=oxidizer_name,
            oxidizer_card_string=oxidizer_card,
            fuel_name=fuel_name,
            fuel_card_string=fuel_card,
            oxidizer_to_fuel_ratio=self.oxidizer_to_fuel_ratio,
            has_condensed_phase=self.has_condensed_phase,
        )

    @staticmethod
    def _get_reactant(
        component: propellant_components.PropellantComponent, reactant_type: str
    ) -> tuple[str, str | None]:
        """
        Get the RocketCEA name and, for a custom component, its card string.

        Args:
            component: Oxidizer or fuel component.
            reactant_type: CEA reactant keyword, "oxid" or "fuel".

        Returns:
            Name to register or look up, and the card string, or None to use
            RocketCEA's built-in card for that name.
        """
        import machwave.services.cea as cea_service

        if not component.custom_card:
            return component.name, None

        card = cea_service.generate_card_string(
            [component.to_cea_dict(weight_percent=100.0)],
            reactant_type=reactant_type,
        )
        return cea_service.normalize_custom_propellant_name(component.name), card
