import dataclasses

import numpy as np


@dataclasses.dataclass(kw_only=True)
class CombustionChamber:
    """
    Represents a cylindrical combustion chamber.

    Attributes:
        inner_diameter: Bore diameter inside the thermal insulation (liner) [m]. Do
            not subtract inhibitors, which belong to the grain.
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
