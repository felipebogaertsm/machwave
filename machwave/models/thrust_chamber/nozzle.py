import numpy as np

import machwave.core.geometric as geometric

DEFAULT_SEPARATION_PRESSURE_RATIO = 0.4  # typically between 0.3 and 0.4


class Nozzle:
    """Converging-diverging nozzle geometry."""

    def __init__(
        self,
        inlet_diameter: float,
        throat_diameter: float,
        divergent_angle: float,
        convergent_angle: float,
        expansion_ratio: float,
        discharge_coefficient: float = 1.0,
        separation_pressure_ratio: float = DEFAULT_SEPARATION_PRESSURE_RATIO,
    ) -> None:
        """
        Initialize a nozzle.

        Args:
            inlet_diameter: Inlet diameter [m].
            throat_diameter: Throat diameter [m].
            divergent_angle: Divergent half-angle [deg].
            convergent_angle: Convergent half-angle [deg].
            expansion_ratio: Area ratio of exit to throat.
            discharge_coefficient: Throat discharge coefficient.
            separation_pressure_ratio: Pressure ratio at which the overexpanded flow
                separates from the nozzle wall (Summerfield criterion).
        """
        self.inlet_diameter = inlet_diameter
        self.throat_diameter = throat_diameter
        self.divergent_angle = divergent_angle
        self.convergent_angle = convergent_angle
        self.expansion_ratio = expansion_ratio
        self.discharge_coefficient = discharge_coefficient
        self.separation_pressure_ratio = separation_pressure_ratio

        self._validate()

    def _validate(self) -> None:
        """
        Validate the nozzle geometry.

        Raises:
            ValueError: If any field is outside its valid physical range.
        """
        if self.inlet_diameter <= 0.0:
            raise ValueError(
                f"inlet_diameter must be strictly positive, got {self.inlet_diameter}"
            )
        if self.throat_diameter <= 0.0:
            raise ValueError(
                f"throat_diameter must be strictly positive, got {self.throat_diameter}"
            )
        if self.throat_diameter >= self.inlet_diameter:
            raise ValueError(
                f"throat_diameter ({self.throat_diameter}) must be smaller than "
                f"inlet_diameter ({self.inlet_diameter})"
            )
        if self.expansion_ratio <= 1.0:
            raise ValueError(
                f"expansion_ratio must be greater than 1, got {self.expansion_ratio}"
            )
        if not 0.0 < self.discharge_coefficient <= 1.0:
            raise ValueError(
                "discharge_coefficient must be in (0, 1], got "
                f"{self.discharge_coefficient}"
            )
        if not 0.0 < self.separation_pressure_ratio < 1.0:
            raise ValueError(
                "separation_pressure_ratio must be in (0, 1), got "
                f"{self.separation_pressure_ratio}"
            )
        if not 0.0 < self.divergent_angle < 90.0:
            raise ValueError(
                f"divergent_angle must be in (0, 90) deg, got {self.divergent_angle}"
            )
        if not 0.0 < self.convergent_angle < 90.0:
            raise ValueError(
                f"convergent_angle must be in (0, 90) deg, got {self.convergent_angle}"
            )

    @property
    def outlet_diameter(self) -> float:
        """Return the nozzle exit diameter [m]."""
        return self.throat_diameter * np.sqrt(self.expansion_ratio)

    def get_throat_area(self) -> float:
        """Return the nozzle throat area [m^2]."""
        return geometric.get_circle_area(self.throat_diameter)
