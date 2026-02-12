import numpy as np

from machwave.core.geometric import (
    get_circle_area,
    get_cylinder_surface_area,
)
from machwave.models.propulsion.grain import GrainGeometryError, GrainSegment2D


class BatesSegment(GrainSegment2D):
    def __init__(
        self,
        outer_diameter: float,
        core_diameter: float,
        length: float,
        density_ratio: float = 1.0,
    ) -> None:
        self.core_diameter = core_diameter

        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            inhibited_ends=0,
            density_ratio=density_ratio,
        )

    def validate(self) -> None:
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
        return self.core_diameter + 2 * web_distance

    def get_port_area(self, web_distance: float) -> float:
        return get_circle_area(diameter=self.get_core_diameter(web_distance))

    def get_core_area(self, web_distance: float) -> float:
        length = self.get_length(web_distance=web_distance)
        core_diameter = self.core_diameter + 2 * web_distance
        return get_cylinder_surface_area(length, core_diameter)

    def get_face_area(self, web_distance: float) -> float:
        core_diameter = self.get_core_diameter(web_distance)
        return np.pi * (((self.outer_diameter**2) - (core_diameter) ** 2) / 4)

    def get_web_thickness(self) -> float:
        """
        More details on the web thickness of BATES grains can be found in:
        https://www.nakka-rocketry.net/design1.html
        """
        return 0.5 * (self.outer_diameter - self.core_diameter)

    def get_optimal_length(self) -> float:
        """
        Returns the optimal length for BATES segment.
        More details on the calculation:
        https://www.nakka-rocketry.net/th_grain.html

        :return: Optimal length for neutral burn of BATES segment
        :rtype: float
        """
        return 1e3 * 0.5 * (3 * self.outer_diameter + self.core_diameter)

    def get_center_of_gravity(
        self, web_distance: float = 0.0
    ) -> np.typing.NDArray[np.float64]:
        """
        Calculate the center of gravity of the BATES grain segment.

        BATES is a symmetrical 2D geometry that burns radially. Due to its
        cylindrical symmetry, the center of gravity remains constant at the
        geometric center regardless of web distance burned.

        Args:
            web_distance: Web distance traveled (unused for BATES due to symmetry),
                         in meters. Included for API consistency.

        Returns:
            Center of gravity in 3D space [x, y, z], in meters, measured from
            the aft end (port, closest to nozzle). Always returns [length/2, 0, 0]
            for symmetric BATES grains.
        """
        # For symmetric BATES grains, CoG doesn't change with burn
        # The grain burns radially inward, maintaining axial symmetry
        # CoG is at geometric center, which is length/2 from the aft end (port)
        return np.array([self.length / 2, 0.0, 0.0], dtype=np.float64)

    def get_moment_of_inertia(
        self, ideal_density: float, web_distance: float = 0.0
    ) -> np.typing.NDArray[np.float64]:
        """
        Calculate the moment of inertia tensor of the BATES grain segment (hollow
        cylinder) at its center of gravity.

        Args:
            ideal_density: Propellant ideal density [kg/m^3].
            web_distance: Web distance traveled [m].

        Returns:
            A 3x3 inertia tensor [kg-m^2].
        """
        # Geometry at given web distance
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
