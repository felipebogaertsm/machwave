import numpy as np

from machwave.models.grain import GrainGeometryError
from machwave.models.grain.base import InhibitedSurfaces
from machwave.models.grain.fmm import FMMGrainSegment2D


class MultiPortGrainSegment(FMMGrainSegment2D):
    """Grain segment with multiple circular ports arranged radially."""

    def __init__(
        self,
        length: float,
        outer_diameter: float,
        port_diameter: float,
        port_radial_count: float,
        port_level_count: float,
        inhibited_surfaces: InhibitedSurfaces | None = None,
        density_ratio: float = 1.0,
    ) -> None:
        """
        Initialize a multi-port grain segment.

        Args:
            length: Segment length [m].
            outer_diameter: Outer diameter [m].
            port_diameter: Diameter of each port [m].
            port_radial_count: Number of ports per concentric ring.
            port_level_count: Number of concentric rings of ports.
            inhibited_surfaces: Surfaces inhibited from burning.
            density_ratio: Ratio of real to ideal propellant density.
        """
        self.port_diameter = port_diameter
        self.port_radial_count = int(port_radial_count)
        self.port_level_count = int(port_level_count)

        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            inhibited_surfaces=inhibited_surfaces,
            density_ratio=density_ratio,
        )

    def validate(self) -> None:
        """Validate multi-port segment geometry."""
        super().validate()

        if not self.port_diameter > 0:
            raise GrainGeometryError(
                f"Port diameter must be positive, got {self.port_diameter}"
            )
        if not self.port_level_count > 0:
            raise GrainGeometryError(
                f"Port level count must be positive, got {self.port_level_count}"
            )
        max_port_size = self.outer_diameter / 2
        total_port_size = self.port_level_count * self.port_diameter
        if not total_port_size < max_port_size:
            raise GrainGeometryError(
                f"Total port size ({total_port_size}) must be less than "
                f"half the outer diameter ({max_port_size})"
            )
        if not self.port_radial_count > 0:
            raise GrainGeometryError(
                f"Port radial count must be positive, got {self.port_radial_count}"
            )

    def get_initial_face_map(self) -> np.typing.NDArray[np.int_]:
        """NOTE: Still needs to correctly implement wagon wheel ports."""
        map_x, map_y = self.get_maps()
        core_map = self.get_empty_face_map()

        od_norm = self.normalize(self.outer_diameter)
        port_od_norm = self.normalize(self.port_diameter)

        for radius in range(self.port_radial_count):
            angle = np.pi * 2 * radius / self.port_radial_count

            for level in range(self.port_level_count):
                radial_distance = od_norm * level / (self.port_level_count) / 2

                x_offset = radial_distance * np.cos(angle)
                y_offset = radial_distance * np.sin(angle)

                radius = np.sqrt((map_x - x_offset) ** 2 + (map_y - y_offset) ** 2)
                core_map[radius < port_od_norm / 2] = 0

        return core_map
