import numpy as np

from machwave.core.geometric import get_circle_area


class Nozzle:
    """Converging-diverging nozzle geometry and loss coefficients."""

    def __init__(
        self,
        inlet_diameter: float,
        throat_diameter: float,
        divergent_angle: float,
        convergent_angle: float,
        expansion_ratio: float,
        c_1: float = 0.00506,
        c_2: float = 0.0,
        discharge_coefficient: float = 1.0,
    ) -> None:
        """
        Initialize a nozzle.

        Args:
            inlet_diameter: Inlet diameter [m].
            throat_diameter: Throat diameter [m].
            divergent_angle: Divergent half-angle [deg].
            convergent_angle: Convergent half-angle [deg].
            expansion_ratio: Area ratio of exit to throat.
            c_1: Boundary-layer loss coefficient (see notes below).
            c_2: Boundary-layer loss coefficient (see notes below).
            discharge_coefficient: Throat discharge coefficient.

        Notes:
            Boundary-layer loss correction coefficients (ref. a015140) are used
            in the boundary-layer percentage loss calculation to account for
            viscous and heat-transfer effects on the nozzle walls. Typical
            values:

            - Ordinary nozzle: `c_1 = 0.003650`, `c_2 = 0.000937`.
            - Thick-walled solid steel nozzle: `c_1 = 0.005060`, `c_2 = 0.0`.
        """
        self.inlet_diameter = inlet_diameter
        self.throat_diameter = throat_diameter
        self.divergent_angle = divergent_angle
        self.convergent_angle = convergent_angle
        self.expansion_ratio = expansion_ratio
        self.c_1 = c_1
        self.c_2 = c_2
        self.discharge_coefficient = discharge_coefficient

    @property
    def outlet_diameter(self) -> float:
        """Return the nozzle exit diameter [m]."""
        return self.throat_diameter * np.sqrt(self.expansion_ratio)

    def get_throat_area(self) -> float:
        """Return the nozzle throat area [m^2]."""
        return get_circle_area(self.throat_diameter)
