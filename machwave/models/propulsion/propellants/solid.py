from .base import Propellant


class BurnRateOutOfBoundsError(Exception):
    """
    Exception raised when the chamber pressure is out of the burn rate range.

    This exception is raised when the chamber pressure provided is outside the
    valid burn rate range for a specific solid propellant.

    Attributes:
        value: The chamber pressure that caused the error.
        message: The error message.
    """

    def __init__(self, value: float) -> None:
        self.value = value
        self.message = f"Chamber pressure out of bounds: {value * 1e-6:.2f} MPa"
        super().__init__(self.message)


class SolidPropellant(Propellant):
    """
    Extends the Propellant abstract class to represent a solid propellant.

    Attributes:
        burn_rate: List of dictionaries describing burn rate behavior (St.
            Robert's law parameters) with keys: "min", "max", "a", and "n".
        qsi_chamber: Number of condensed-phase moles per 100 g in the chamber.
        qsi_exhaust: Number of condensed-phase moles per 100 g in the exhaust.
        porosity: Porosity of the solid propellant (0 to 1). Represents the
            volume fraction of voids in the propellant.
        solid_density: Solid propellant density [kg/m^3].
    """

    def __init__(
        self,
        burn_rate: list[dict[str, float | int]],
        porosity: float = 0.98,
        combustion_efficiency: float = 0.95,
    ):
        super().__init__(combustion_efficiency)
        self.porosity = porosity
        self.burn_rate = burn_rate

    def evaluate(self, *args, **kwargs) -> None:
        super().evaluate(*args, **kwargs)

        self.qsi_chamber = 0.0
        self.qsi_exhaust = 0.0
        self.solid_density = 0.0 * self.porosity

    def get_burn_rate(self, chamber_pressure: float) -> float:
        """
        Calculates the instantaneous burn rate of the solid propellant using
        St. Robert's law.

        Args:
            chamber_pressure (float): The instantaneous stagnation pressure
                [Pa].

        Returns:
            float: The instantaneous burn rate in meters per second.

        Raises:
            BurnRateOutOfBoundsError: If the chamber pressure is not within any
                burn rate range.
        """
        for item in self.burn_rate:
            if item["min"] <= chamber_pressure <= item["max"]:
                a = item["a"]
                n = item["n"]
                # Convert pressure from Pa to MPa, apply St. Robert's law,
                # then convert from mm/s to m/s
                return (a * (chamber_pressure * 1e-6) ** n) * 1e-3

        raise BurnRateOutOfBoundsError(chamber_pressure)
