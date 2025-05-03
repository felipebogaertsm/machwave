import numpy as np

from machwave.models.propulsion.grain import GrainGeometryError
from machwave.models.propulsion.grain.fmm import FMMGrainSegment2D
from machwave.services.decorators import validate_assertions


class MultiPortGrainSegment(FMMGrainSegment2D):
    def __init__(
        self,
        length: float,
        outer_diameter: float,
        port_diameter: float,
        port_radial_count: float,
        port_level_count: float,
        spacing: float,
        inhibited_ends: int = 0,
    ) -> None:
        self.port_diameter = port_diameter
        self.port_radial_count = int(port_radial_count)
        self.port_level_count = int(port_level_count)

        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            spacing=spacing,
            inhibited_ends=inhibited_ends,
        )

    @validate_assertions(exception=GrainGeometryError)
    def validate(self) -> None:
        super().validate()

        assert self.port_diameter > 0
        assert self.port_level_count > 0
        assert self.port_level_count * self.port_diameter < self.outer_diameter / 2

        assert self.port_radial_count > 0

    def get_initial_face_map(self) -> np.typing.NDArray[np.int_]:
        """
        NOTE: Still needs to correctly implement wagon wheel ports.
        """
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
