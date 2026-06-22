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

    @property
    def outlet_diameter(self) -> float:
        """Return the nozzle exit diameter [m]."""
        return self.throat_diameter * np.sqrt(self.expansion_ratio)

    def get_throat_area(self) -> float:
        """Return the nozzle throat area [m^2]."""
        return geometric.get_circle_area(self.throat_diameter)
