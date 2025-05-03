import numpy as np

from machwave.models.propulsion.grain import GrainGeometryError, GrainSegment2D
from machwave.services.decorators import validate_assertions
from machwave.services.math.geometric import (
    get_circle_area,
    get_cylinder_surface_area,
)


class BatesSegment(GrainSegment2D):
    def __init__(
        self,
        outer_diameter: float,
        core_diameter: float,
        length: float,
        spacing: float,
    ) -> None:
        self.core_diameter = core_diameter

        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            spacing=spacing,
            inhibited_ends=0,
        )

    @validate_assertions(exception=GrainGeometryError)
    def validate(self) -> None:
        super().validate()

        assert self.outer_diameter > self.core_diameter
        assert self.core_diameter > 0

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

    def get_center_of_gravity(self, *args, **kwargs) -> np.typing.NDArray[np.float64]:
        """
        BATES is a symmetrical 2D geometry, so the center of gravity is always
        at the middle of the segment along the axial (length) direction.

        Returns:
            Center of gravity in 3D space [x, y, z].
        """
        return np.array([self.length / 2, 0.0, 0.0], dtype=np.float64)
