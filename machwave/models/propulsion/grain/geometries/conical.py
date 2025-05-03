import numpy as np

from machwave.models.propulsion.grain import GrainGeometryError
from machwave.models.propulsion.grain.fmm import FMMGrainSegment3D
from machwave.services.decorators import validate_assertions


class ConicalGrainSegment(FMMGrainSegment3D):
    def __init__(
        self,
        length: float,
        outer_diameter: float,
        upper_core_diameter: float,
        lower_core_diameter: float,
        spacing: float,
        inhibited_ends: int = 0,
    ) -> None:
        self.upper_core_diameter = upper_core_diameter
        self.lower_core_diameter = lower_core_diameter

        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            spacing=spacing,
            inhibited_ends=inhibited_ends,
        )

    @validate_assertions(exception=GrainGeometryError)
    def validate(self) -> None:
        super().validate()

        assert self.upper_core_diameter > 0
        assert self.upper_core_diameter < self.outer_diameter

        assert self.lower_core_diameter > 0
        assert self.lower_core_diameter < self.outer_diameter

    def get_initial_face_map(self) -> np.typing.NDArray[np.int_]:
        map_x, map_y, map_z = self.get_maps()
        core_map = self.get_empty_face_map()

        upper_core_norm = self.normalize(self.upper_core_diameter)
        lower_core_norm = self.normalize(self.lower_core_diameter)

        radius = np.sqrt(map_x**2 + map_y**2)
        core_diameter = map_z * (upper_core_norm - lower_core_norm) + lower_core_norm

        # Create the ring:
        core_map[radius < core_diameter / 2] = 0
        core_map[0] = 0  # Inhibit the bottom end
        core_map[-1] = 0  # Inhibit the top end

        return core_map
