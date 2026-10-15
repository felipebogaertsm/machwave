import dataclasses

import numpy as np


@dataclasses.dataclass(kw_only=True)
class CombustionChamber:
    """
    Represents a cylindrical combustion chamber.

    The chamber internal volume is the open bore of diameter `inner_diameter` over
    `internal_length`. Inhibitors belong to the grain, so an inhibitor sleeve between
    the grain and the thermal insulation is not part of the chamber: its annulus is
    counted as free chamber volume.

    Attributes:
        inner_diameter: Diameter of the open bore inside the thermal insulation
            (liner) [m]. The insulation thickness is already subtracted; inhibitor
            thickness is not.
        internal_length: Distance from combustion chamber inlet to nozzle inlet [m].
    """

    inner_diameter: float
    internal_length: float

    def __post_init__(self) -> None:
        """
        Validate the combustion chamber geometry.

        Raises:
            ValueError: If any field is outside its valid physical range.
        """
        if self.inner_diameter <= 0.0:
            raise ValueError(
                f"inner_diameter must be strictly positive, got {self.inner_diameter}"
            )
        if self.internal_length <= 0.0:
            raise ValueError(
                f"internal_length must be strictly positive, got {self.internal_length}"
            )

    @property
    def internal_volume(self) -> float:
        """Internal volume of the combustion chamber [m^3]."""
        radius = 0.5 * self.inner_diameter
        return np.pi * radius * radius * self.internal_length
