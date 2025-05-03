import numpy as np

from machwave.models.propulsion.grain import GrainGeometryError
from machwave.models.propulsion.grain.fmm import FMMGrainSegment2D
from machwave.services.decorators import validate_assertions


class RodAndTubeGrainSegment(FMMGrainSegment2D):
    def __init__(
        self,
        length: float,
        outer_diameter: float,
        rod_outer_diameter: float,
        tube_inner_diameter: float,
        spacing: float,
        inhibited_ends: int = 0,
    ) -> None:
        self.rod_outer_diameter = rod_outer_diameter
        self.tube_inner_diameter = tube_inner_diameter

        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            spacing=spacing,
            inhibited_ends=inhibited_ends,
        )

    @validate_assertions(exception=GrainGeometryError)
    def validate(self) -> None:
        super().validate()

        assert self.rod_outer_diameter > 0
        assert self.tube_inner_diameter > self.rod_outer_diameter
        assert self.tube_inner_diameter < self.outer_diameter

    def get_initial_face_map(self) -> np.typing.NDArray[np.int_]:
        """
        NOTE: Still needs to correctly implement wagon wheel ports.
        """
        map_x, map_y = self.get_maps()
        core_map = self.get_empty_face_map()

        rod_od_norm = self.normalize(self.rod_outer_diameter)
        tube_id_norm = self.normalize(self.tube_inner_diameter)

        radius = np.sqrt(map_x**2 + map_y**2)

        # Create the ring:
        core_map[(radius > rod_od_norm / 2) & (radius < tube_id_norm / 2)] = 0

        return core_map
