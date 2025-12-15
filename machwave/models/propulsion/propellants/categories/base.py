"""Base propellant type classes."""

import abc

from ..properties import ThermochemicalProperties


class Propellant(abc.ABC):
    """Base class for propellants.

    Each propellant type represents a specific composition and can dynamically
    calculate thermochemical properties by calling evaluate(), which populates
    and returns a properties object.

    Attributes:
        combustion_efficiency: Scaling factor (0 to 1) applied to ideal combustion temperature.
        cea_obj: RocketCEA object for thermochemical calculations (populated by evaluate).
        properties: Calculated propellant properties (populated by evaluate).
    """

    def __init__(self, combustion_efficiency: float):
        self.combustion_efficiency = combustion_efficiency
        self.properties = None

    @abc.abstractmethod
    def evaluate(
        self, chamber_pressure: float, expansion_ratio: float = 8.0
    ) -> "ThermochemicalProperties":
        """Calculate propellant properties given chamber conditions.

        Args:
            chamber_pressure: Chamber pressure [Pa].
            expansion_ratio: Nozzle area expansion ratio (Ae/At).

        Returns:
            ThermochemicalProperties: Calculated properties.
        """
        ...


class BurnRateOutOfBoundsError(Exception):
    """Exception raised when chamber pressure is outside valid burn rate range.

    Attributes:
        value: The chamber pressure that caused the error [Pa].
        message: The error message.
    """

    def __init__(self, value: float) -> None:
        self.value = value
        self.message = f"Chamber pressure out of bounds: {value * 1e-6:.2f} MPa"
        super().__init__(self.message)
