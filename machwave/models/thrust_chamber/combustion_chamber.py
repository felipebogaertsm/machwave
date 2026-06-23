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
        """
        Create a new CombustionChamber instance.

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

        self._validate()

    def _validate(self) -> None:
        """
        Validate the combustion chamber geometry.

        Raises:
            ValueError: If any field is outside its valid physical range.
        """
        if self.casing_inner_diameter <= 0.0:
            raise ValueError(
                "casing_inner_diameter must be strictly positive, got "
                f"{self.casing_inner_diameter}"
            )
        if self.casing_outer_diameter <= self.casing_inner_diameter:
            raise ValueError(
                f"casing_outer_diameter ({self.casing_outer_diameter}) must be larger "
                f"than casing_inner_diameter ({self.casing_inner_diameter})"
            )
        if self.internal_length <= 0.0:
            raise ValueError(
                f"internal_length must be strictly positive, got {self.internal_length}"
            )
        if self.thermal_liner_thickness < 0.0:
            raise ValueError(
                "thermal_liner_thickness must be non-negative, got "
                f"{self.thermal_liner_thickness}"
            )
        if self.thermal_liner_thickness >= 0.5 * self.casing_inner_diameter:
            raise ValueError(
                f"thermal_liner_thickness ({self.thermal_liner_thickness}) leaves no "
                f"open bore for casing_inner_diameter ({self.casing_inner_diameter})"
            )

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
