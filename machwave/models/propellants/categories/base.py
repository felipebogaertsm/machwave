"""Base propellant class with shared functionality."""

import abc
import enum
import functools

from machwave.services import cea as cea_service

from ..components import PropellantComponent
from ..properties import ThermochemicalProperties


class PropellantValidationError(Exception):
    """Raised when propellant validation fails."""

    def __init__(self, message: str):
        """
        Args:
            message: Description of the validation error.
        """
        super().__init__(f"Propellant validation error: {message}")


class MixtureType(enum.StrEnum):
    """Type of propellant mixture."""

    SOLID = "solid"
    BILIQUID = "biliquid"


class Propellant(abc.ABC):
    """Base class for propellant formulations."""

    mixture_type: MixtureType

    def __init__(
        self,
        name: str,
        components: list[PropellantComponent] | None = None,
        combustion_efficiency: float = 0.95,
    ):
        """Initialize propellant.

        Args:
            name: Propellant name.
            components: Chemical components. If None, defaults to empty list.
            combustion_efficiency: Efficiency factor (0-1).
        """
        self.name = name
        self.components = list(components) if components is not None else []
        self.combustion_efficiency = combustion_efficiency

    @functools.cached_property
    def thermochemical_service(self) -> cea_service.RocketCEAService:
        """Get thermochemical service, cached."""
        return self._get_thermochemical_service()

    @abc.abstractmethod
    def _validate_components(self):
        """Validate components meet propellant type requirements.

        Raises:
            PropellantValidationError: If validation fails.
        """
        pass

    @abc.abstractmethod
    def _get_thermochemical_service(self) -> cea_service.RocketCEAService:
        """Create thermochemical service for this propellant.

        Implemented for every subclass of propellant category, based on how the CEA
        object is constructed (from components, from properties, others).

        Returns:
            RocketCEAService instance.

        Raises:
            PropellantValidationError: If service creation fails.
        """
        pass

    def evaluate(
        self,
        chamber_pressure: float,
        expansion_ratio: float = 8.0,
        mixture_ratio: float | None = None,
    ) -> ThermochemicalProperties:
        """Evaluate thermochemical properties at given conditions.

        Args:
            chamber_pressure: Chamber pressure [Pa].
            expansion_ratio: Nozzle area ratio (Ae/At).
            mixture_ratio: Ratio of the propellant mixture.

        Returns:
            ThermochemicalProperties.

        Raises:
            ValueError: If evaluation fails.
        """
        self._validate_components()
        service = self.thermochemical_service

        adiabatic_flame_temperature = service.get_adiabatic_flame_temperature(
            chamber_pressure=chamber_pressure, mixture_ratio=mixture_ratio
        )

        molecular_weight_chamber, k_chamber = service.get_chamber_properties(
            chamber_pressure=chamber_pressure,
            expansion_ratio=expansion_ratio,
            mixture_ratio=mixture_ratio,
        )

        molecular_weight_exhaust, k_exhaust = service.get_exhaust_properties(
            chamber_pressure=chamber_pressure,
            expansion_ratio=expansion_ratio,
            mixture_ratio=mixture_ratio,
        )

        i_sp_frozen, i_sp_shifting = service.get_specific_impulse(
            chamber_pressure=chamber_pressure,
            expansion_ratio=expansion_ratio,
            mixture_ratio=mixture_ratio,
        )
        qsi_chamber, qsi_exhaust = service.get_condensed_phase_fractions(
            chamber_pressure=chamber_pressure,
            expansion_ratio=expansion_ratio,
            mixture_ratio=mixture_ratio,
        )

        properties = ThermochemicalProperties(
            k_chamber=k_chamber,
            k_exhaust=k_exhaust,
            adiabatic_flame_temperature=adiabatic_flame_temperature,
            molecular_weight_chamber=molecular_weight_chamber,
            molecular_weight_exhaust=molecular_weight_exhaust,
            i_sp_frozen=i_sp_frozen,
            i_sp_shifting=i_sp_shifting,
            qsi_chamber=qsi_chamber,
            qsi_exhaust=qsi_exhaust,
        )
        return properties
