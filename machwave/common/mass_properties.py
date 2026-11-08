import dataclasses
import math


def _as_3d_vector(
    name: str, value: tuple[float, float, float]
) -> tuple[float, float, float]:
    """Coerce value to a length-three float tuple, raising if it is not."""
    try:
        components = tuple(float(component) for component in value)
    except TypeError as error:
        raise ValueError(f"{name} must be a length-three sequence") from error
    if len(components) != 3:
        raise ValueError(f"{name} must have three components, got {len(components)}")
    return (components[0], components[1], components[2])


@dataclasses.dataclass(frozen=True, kw_only=True)
class DryMassProperties:
    """
    Properties common to devices that contain dry mass.

    Attributes:
        dry_mass: Dry mass scalar [kg].
        center_of_gravity_coordinate: Dry mass center of gravity position measured from
            the nozzle exit `(x, y, z)` [m]. Positive x points toward the bulkhead.
        moment_of_inertia: Dry mass principal moments of inertia `(I_11, I_22, I_33)`
            [kg-m^2], evaluated at the dry mass center of gravity. Assumes the thrust
            chamber is aligned with the x-axis.
    """

    dry_mass: float
    center_of_gravity_coordinate: tuple[float, float, float]
    moment_of_inertia: tuple[float, float, float]

    def __post_init__(self) -> None:
        """
        Validate and normalize the dry mass properties.

        Raises:
            ValueError: If the dry mass is non-positive or non-finite, either triple is
                malformed, or a moment of inertia is negative or non-finite.
        """
        if not math.isfinite(self.dry_mass) or self.dry_mass <= 0.0:
            raise ValueError(
                f"dry_mass must be a positive finite number, got {self.dry_mass}"
            )

        cog = _as_3d_vector(
            "center_of_gravity_coordinate", self.center_of_gravity_coordinate
        )
        moment_of_inertia = _as_3d_vector("moment_of_inertia", self.moment_of_inertia)

        if any(not math.isfinite(c) or c < 0.0 for c in moment_of_inertia):
            raise ValueError(
                "moment_of_inertia components must be non-negative finite numbers, got "
                f"{moment_of_inertia}"
            )

        object.__setattr__(self, "center_of_gravity_coordinate", cog)
        object.__setattr__(self, "moment_of_inertia", moment_of_inertia)
