import numpy as np

from machwave.core.geometric import get_circle_area


class Nozzle:
    def __init__(
        self,
        inlet_diameter,
        throat_diameter,
        divergent_angle,
        convergent_angle,
        expansion_ratio,
        c_1: float = 0.00506,
        c_2: float = 0.0,
    ) -> None:
        self.inlet_diameter = inlet_diameter
        self.throat_diameter = throat_diameter
        self.divergent_angle = divergent_angle
        self.convergent_angle = convergent_angle
        self.expansion_ratio = expansion_ratio

        # Boundary layer loss correction coefficients (ref. a015140).
        # Used in the boundary layer percentage loss calculation to account
        # for viscous and heat transfer effects in the nozzle walls.
        # Ordinary nozzle:                 c_1 = 0.003650, c_2 = 0.000937
        # Thick-walled solid steel nozzle: c_1 = 0.005060, c_2 = 0.000000
        self.c_1 = c_1
        self.c_2 = c_2

    @property
    def outlet_diameter(self):
        return self.throat_diameter * np.sqrt(self.expansion_ratio)

    def get_throat_area(self):
        return get_circle_area(self.throat_diameter)
