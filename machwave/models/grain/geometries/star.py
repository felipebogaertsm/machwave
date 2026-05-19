import numpy as np

from machwave.models.grain import GrainGeometryError
from machwave.models.grain.base import InhibitedSurfaces
from machwave.models.grain.fmm import FMMGrainSegment2D


class StarGrainSegment(FMMGrainSegment2D):
    """Star grain segment with a radial point pattern as the port."""

    def __init__(
        self,
        length: float,
        outer_diameter: float,
        number_of_points: int,
        point_length: float,
        point_width: float,
        inhibited_surfaces: InhibitedSurfaces | None = None,
        density_ratio: float = 1.0,
    ) -> None:
        """
        Initialize a star grain segment.

        Args:
            length: Segment length [m].
            outer_diameter: Outer diameter [m].
            number_of_points: Number of star points (must be < 12).
            point_length: Radial length of each point [m].
            point_width: Width of each point at the base [m].
            inhibited_surfaces: Surfaces inhibited from burning.
            density_ratio: Ratio of real to ideal propellant density.
        """
        self.number_of_points = int(number_of_points)
        self.point_length = point_length
        self.point_width = point_width

        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            inhibited_surfaces=inhibited_surfaces,
            density_ratio=density_ratio,
        )

    def validate(self) -> None:
        """Validate star segment geometry."""
        super().validate()

        if not self.number_of_points > 0:
            raise GrainGeometryError(
                f"Number of points must be positive, got {self.number_of_points}"
            )
        if not self.number_of_points < 12:
            raise GrainGeometryError(
                f"Number of points must be less than 12, got {self.number_of_points}"
            )
        if not isinstance(self.number_of_points, int):
            raise GrainGeometryError(
                f"Number of points must be an integer, got {type(self.number_of_points).__name__}"
            )
        if not self.point_length > 0:
            raise GrainGeometryError(
                f"Point length must be positive, got {self.point_length}"
            )
        if not self.point_width > 0:
            raise GrainGeometryError(
                f"Point width must be positive, got {self.point_width}"
            )

    def get_initial_face_map(self) -> np.typing.NDArray[np.int_]:
        """
        Return the initial face map for a star grain segment.

        References:
            openMotor, https://github.com/reilleya/openMotor
        """
        map_x, map_y = self.get_maps()
        core_map = self.get_empty_face_map()

        point_length_norm = self.normalize(self.point_length)
        point_width_norm = self.normalize(self.point_width)

        radius = (map_x**2 + map_y**2) ** 0.5

        for i in range(0, self.number_of_points):
            theta = 2 * np.pi / self.number_of_points * i
            rect = abs(np.cos(theta) * map_x + np.sin(theta) * map_y)

            width = point_width_norm / 2 * (1 - (radius / point_length_norm))
            vect = rect < width
            near = np.sin(theta) * map_x - np.cos(theta) * map_y > -0.025

            core_map[np.logical_and(vect, near)] = 0

        return core_map
