from typing import Optional

import numpy as np

from .. import GrainGeometryError
from ..fmm._2d import FMMGrainSegment2D
from rocketsolver.services.decorators import validate_assertions


class DGrainSegment(FMMGrainSegment2D):
    def __init__(
        self,
        length: float,
        outer_diameter: float,
        spacing: float,
        slot_offset: float,
        inhibited_ends: Optional[int] = 0,
    ) -> None:
        self.slot_offset = slot_offset

        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            spacing=spacing,
            inhibited_ends=inhibited_ends,
        )

    @validate_assertions(exception=GrainGeometryError)
    def validate(self) -> None:
        super().validate()

        assert self.slot_offset >= 0
        assert self.slot_offset < self.outer_diameter / 2

    def get_initial_face_map(self) -> np.ndarray:
        slot_offset_normalized = self.normalize(self.slot_offset)
        map_x = self.get_maps()[0]
        core_map = self.get_empty_face_map()
        core_map[map_x > slot_offset_normalized] = 0
        return core_map
