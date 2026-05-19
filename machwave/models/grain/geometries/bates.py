import numpy as np

from machwave.core.geometric import (
    get_circle_area,
    get_cylinder_surface_area,
)
from machwave.models.grain import GrainGeometryError, GrainSegment2D
from machwave.models.grain.base import InhibitedSurfaces


class BatesSegment(GrainSegment2D):
    """BATES grain segment: cylindrical with circular central port."""

    INHIBITED_SURFACES = InhibitedSurfaces(
        outer_surface=True,
        inner_surface=False,
        upper_end=False,
        lower_end=False,
    )

    def __init__(
        self,
        outer_diameter: float,
        core_diameter: float,
        length: float,
        density_ratio: float = 1.0,
    ) -> None:
        """
        Initialize a BATES grain segment.

        Args:
            outer_diameter: Outer diameter [m].
            core_diameter: Core (port) diameter [m].
            length: Segment length [m].
            density_ratio: Ratio of real to ideal propellant density.
        """
        self.core_diameter = core_diameter

        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            inhibited_surfaces=self.INHIBITED_SURFACES,
            density_ratio=density_ratio,
        )

    def validate(self) -> None:
        """Validate BATES segment geometry."""
        super().validate()

        if not self.outer_diameter > self.core_diameter:
            raise GrainGeometryError(
                f"Outer diameter ({self.outer_diameter}) must be greater than "
                f"core diameter ({self.core_diameter})"
            )
        if not self.core_diameter > 0:
            raise GrainGeometryError(
                f"Core diameter must be positive, got {self.core_diameter}"
            )

    def get_core_diameter(self, web_distance: float) -> float:
        """Return the core diameter at a given web distance [m]."""
        return self.core_diameter + 2 * web_distance

    def get_port_area(self, web_distance: float) -> float:
        """Return the port area at a given web distance [m^2]."""
        return get_circle_area(diameter=self.get_core_diameter(web_distance))

    def get_core_area(self, web_distance: float) -> float:
        """Return the core (inner cylindrical) surface area [m^2]."""
        length = self.get_length(web_distance=web_distance)
        core_diameter = self.core_diameter + 2 * web_distance
        return get_cylinder_surface_area(length, core_diameter)

    def get_face_area(self, web_distance: float) -> float:
        """Return the annular face area at a given web distance [m^2]."""
        core_diameter = self.get_core_diameter(web_distance)
        return np.pi * (((self.outer_diameter**2) - (core_diameter) ** 2) / 4)

    def get_web_thickness(self) -> float:
        """
        Return the BATES web thickness [m].

        See: https://www.nakka-rocketry.net/design1.html.
        """
        return 0.5 * (self.outer_diameter - self.core_diameter)

    def get_optimal_length(self) -> float:
        """
        Return the optimal length for neutral burn of a BATES segment [mm].

        See: https://www.nakka-rocketry.net/th_grain.html.
        """
        return 1e3 * 0.5 * (3 * self.outer_diameter + self.core_diameter)

    def get_center_of_gravity(
        self, web_distance: float = 0.0
    ) -> np.typing.NDArray[np.float64]:
        """
        Return the center of gravity of a BATES segment.

        BATES is a symmetrical 2D geometry that burns radially. Due to its
        cylindrical symmetry, the center of gravity remains constant at the
        geometric center regardless of web distance burned.

        Args:
            web_distance: Web distance traveled [m]. Unused for BATES due to
                symmetry; included for API consistency.

        Returns:
            Center of gravity [x, y, z] [m], measured from the aft end (port,
            closest to nozzle). Always returns [length/2, 0, 0] for symmetric
            BATES grains.
        """
        # For symmetric BATES grains, CoG doesn't change with burn
        # The grain burns radially inward, maintaining axial symmetry
        # CoG is at geometric center, which is length/2 from the aft end (port)
        return np.array([self.length / 2, 0.0, 0.0], dtype=np.float64)

    def get_moment_of_inertia(
        self, ideal_density: float, web_distance: float = 0.0
    ) -> np.typing.NDArray[np.float64]:
        """
        Return the moment of inertia tensor of the BATES segment.

        Treats the segment as a hollow cylinder and evaluates the tensor at
        its center of gravity.

        Args:
            ideal_density: Propellant ideal density [kg/m^3].
            web_distance: Web distance traveled [m].

        Returns:
            A 3x3 inertia tensor [kg-m^2].
        """
        r_inner = (self.core_diameter + 2 * web_distance) / 2
        r_outer = self.outer_diameter / 2
        current_length = self.get_length(web_distance)

        volume = self.get_volume(web_distance)
        mass = volume * ideal_density * self.density_ratio

        r_sum_sq = r_inner**2 + r_outer**2

        # Ixx: moment about axial axis
        Ixx = mass * r_sum_sq / 2

        # Iyy, Izz: moments about radial axes
        Iyy = mass * (r_sum_sq / 4 + current_length**2 / 12)
        Izz = Iyy

        return np.array(
            [[Ixx, 0.0, 0.0], [0.0, Iyy, 0.0], [0.0, 0.0, Izz]], dtype=np.float64
        )
