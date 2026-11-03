import dataclasses
import math
from collections.abc import Iterable

import numpy as np
import numpy.typing as npt

import machwave.core.mechanics as mechanics


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


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class AxisymmetricMassProperties:
    """
    Mass properties of a body symmetric about the x-axis.

    Attributes:
        mass: Mass [kg].
        axial_position: Center of gravity position along the x-axis, measured from the
            nozzle exit [m]. Undefined for a massless body.
        axial_moment_of_inertia: Moment of inertia about the x-axis [kg-m^2].
        transverse_moment_of_inertia: Moment of inertia about any transverse axis
            through the center of gravity [kg-m^2].
    """

    mass: float
    axial_position: float
    axial_moment_of_inertia: float
    transverse_moment_of_inertia: float

    @classmethod
    def from_cylinder(
        cls,
        *,
        mass: float,
        length: float,
        outer_radius: float,
        axial_position: float,
        inner_radius: float = 0.0,
    ) -> "AxisymmetricMassProperties":
        """
        Return the mass properties of a uniform cylinder lying along the x-axis.

        Args:
            mass: Cylinder mass [kg].
            length: Cylinder length [m].
            outer_radius: Outer radius [m].
            axial_position: Position of the cylinder center along the x-axis [m].
            inner_radius: Bore radius [m], zero for a solid cylinder.

        Returns:
            The mass properties of the cylinder.
        """
        axial_moment, transverse_moment = mechanics.get_cylinder_moments_of_inertia(
            mass=mass,
            length=length,
            outer_radius=outer_radius,
            inner_radius=inner_radius,
        )
        return cls(
            mass=mass,
            axial_position=axial_position,
            axial_moment_of_inertia=axial_moment,
            transverse_moment_of_inertia=transverse_moment,
        )

    @classmethod
    def combine(
        cls, bodies: Iterable["AxisymmetricMassProperties"]
    ) -> "AxisymmetricMassProperties":
        """
        Combine coaxial bodies into one with the parallel axis theorem.

        A massless body adds nothing, so its axial position may be undefined.

        Args:
            bodies: Bodies sharing the x-axis.

        Returns:
            The mass properties of the bodies taken together.
        """
        massive_bodies = [body for body in bodies if body.mass > 0.0]
        mass = sum(body.mass for body in massive_bodies)
        if mass <= 0.0:
            return cls(
                mass=0.0,
                axial_position=math.nan,
                axial_moment_of_inertia=0.0,
                transverse_moment_of_inertia=0.0,
            )

        axial_position = (
            sum(body.mass * body.axial_position for body in massive_bodies) / mass
        )
        return cls(
            mass=mass,
            axial_position=axial_position,
            axial_moment_of_inertia=sum(
                body.axial_moment_of_inertia for body in massive_bodies
            ),
            transverse_moment_of_inertia=sum(
                body.transverse_moment_of_inertia
                + body.mass * (body.axial_position - axial_position) ** 2
                for body in massive_bodies
            ),
        )

    @property
    def center_of_gravity(self) -> npt.NDArray[np.float64]:
        """Center of gravity `(x, y, z)` [m], NaN for a massless body."""
        if self.mass <= 0.0:
            return np.full(3, np.nan)
        return np.array([self.axial_position, 0.0, 0.0], dtype=np.float64)

    @property
    def moment_of_inertia(self) -> npt.NDArray[np.float64]:
        """3x3 inertia tensor about the center of gravity [kg-m^2], x-axis first."""
        axial = self.axial_moment_of_inertia
        transverse = self.transverse_moment_of_inertia
        return np.array(
            [[axial, 0.0, 0.0], [0.0, transverse, 0.0], [0.0, 0.0, transverse]],
            dtype=np.float64,
        )
