import numpy as np


class CombustionChamber:
    """Geometry model of a cylindrical combustion-chamber."""

    def __init__(
        self,
        casing_inner_diameter: float,
        casing_outer_diameter: float,
        internal_length: float,
        thermal_liner_thickness: float = 0.0,
    ) -> None:
        """Create a new CombustionChamber instance.

        Args:
            casing_inner_diameter: Internal diameter [m].
            casing_outer_diameter: Outer diameter [m].
            internal_length: Distance from combustion chamber inlet to
                nozzle inlet [m].
            thermal_liner_thickness: Thermal liner thickness [m].
                Defaults to 0.0.
        """
        self.casing_inner_diameter = casing_inner_diameter
        self.casing_outer_diameter = casing_outer_diameter
        self.internal_length = internal_length
        self.thermal_liner_thickness = thermal_liner_thickness

    @property
    def inner_diameter(self) -> float:
        """Inner diameter of the combustion chamber [m]."""
        return self.casing_inner_diameter - 2 * self.thermal_liner_thickness

    @property
    def outer_diameter(self) -> float:
        """Outer diameter of the combustion chamber [m]."""
        return self.casing_outer_diameter

    @property
    def inner_radius(self) -> float:
        """Inner radius of the combustion chamber [m]."""
        return 0.5 * self.inner_diameter

    @property
    def outer_radius(self) -> float:
        """Outer radius of the combustion chamber [m]."""
        return 0.5 * self.outer_diameter

    @property
    def internal_volume(self) -> float:
        """Internal volume of the combustion chamber [m^3]."""
        r = self.inner_radius
        return np.pi * r * r * self.internal_length
