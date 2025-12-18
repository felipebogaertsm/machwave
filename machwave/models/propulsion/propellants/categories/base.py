"""Base propellant class with shared functionality."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum

from machwave.services.cea import RocketCEAService

from ..components import PropellantComponent
from ..properties import ThermochemicalProperties


class PropellantValidationError(Exception):
    """Raised when propellant validation fails."""

    pass


class MixtureType(str, Enum):
    """Type of propellant mixture."""

    SOLID = "solid"
    BILIQUID = "biliquid"


@dataclass
class Propellant(ABC):
    """Base class for propellant formulations.

    Attributes:
        name: Propellant name.
        components: Chemical components.
        combustion_efficiency: Efficiency factor (0-1).
        mixture_type: Mixture type (solid, biliquid).
    """

    name: str
    components: list[PropellantComponent] = field(default_factory=list)
    combustion_efficiency: float = 0.95
    mixture_type: MixtureType = field(init=False)
    _thermochemical_service: RocketCEAService | None = field(
        init=False, repr=False, default=None
    )

    @property
    def thermochemical_service(self) -> RocketCEAService:
        """Get thermochemical service, creating it lazily if needed."""
        if self._thermochemical_service is None:
            self._thermochemical_service = self._get_thermochemical_service()
        return self._thermochemical_service

    @abstractmethod
    def _validate_components(self):
        """Validate components meet propellant type requirements.

        Raises:
            PropellantValidationError: If validation fails.
        """
        pass

    @abstractmethod
    def _get_thermochemical_service(self) -> RocketCEAService:
        """Create thermochemical service for this propellant.

        Returns:
            RocketCEAService instance.

        Raises:
            PropellantValidationError: If service creation fails.
        """
        pass

    @property
    def ideal_density(self) -> float:
        """Ideal propellant density (no porosity) [kg/m³].

        Computed as harmonic mean: 1 / sum(mass_fraction_i / density_i).
        For real density with porosity, use real_density(porosity) method.

        Raises:
            PropellantValidationError: If components missing or invalid.
        """
        if not self.components:
            raise PropellantValidationError(
                f"Cannot compute density without components for propellant '{self.name}'"
            )

        # Check all components have density defined
        for comp in self.components:
            if comp.density is None or comp.density <= 0:
                raise PropellantValidationError(
                    f"Component '{comp.name}' has invalid density: {comp.density}"
                )

        # Harmonic mean: 1 / sum(mass_fraction_i / density_i)
        reciprocal_sum: float = sum(
            comp.mass_fraction / comp.density  # type: ignore[operator]
            for comp in self.components
        )
        return 1.0 / reciprocal_sum

    def evaluate(
        self, chamber_pressure: float, expansion_ratio: float = 8.0
    ) -> ThermochemicalProperties:
        """Evaluate thermochemical properties at given conditions.

        Args:
            chamber_pressure: Chamber pressure [Pa].
            expansion_ratio: Nozzle area ratio (Ae/At).

        Returns:
            ThermochemicalProperties.

        Raises:
            ValueError: If evaluation fails.
        """
        self._validate_components()
        service = self.thermochemical_service

        adiabatic_flame_temperature = service.get_adiabatic_flame_temperature(
            chamber_pressure=chamber_pressure
        )

        molecular_weight_chamber, gamma_chamber = service.get_chamber_properties(
            chamber_pressure=chamber_pressure, expansion_ratio=expansion_ratio
        )

        molecular_weight_exhaust, gamma_exhaust = service.get_exhaust_properties(
            chamber_pressure=chamber_pressure, expansion_ratio=expansion_ratio
        )

        i_sp_frozen, i_sp_shifting = service.get_specific_impulse(
            chamber_pressure=chamber_pressure, expansion_ratio=expansion_ratio
        )
        qsi_chamber, qsi_exhaust = service.get_condensed_phase_fractions(
            chamber_pressure=chamber_pressure, expansion_ratio=expansion_ratio
        )

        properties = ThermochemicalProperties(
            gamma_chamber=gamma_chamber,
            gamma_exhaust=gamma_exhaust,
            adiabatic_flame_temperature=adiabatic_flame_temperature,
            molecular_weight_chamber=molecular_weight_chamber,
            molecular_weight_exhaust=molecular_weight_exhaust,
            i_sp_frozen=i_sp_frozen,
            i_sp_shifting=i_sp_shifting,
            qsi_chamber=qsi_chamber,
            qsi_exhaust=qsi_exhaust,
        )
        return properties
