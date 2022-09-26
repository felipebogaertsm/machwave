# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from typing import Optional

import numpy as np

from . import FMMGrainSegment2D


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

    def validate(self) -> None:
        assert self.slot_offset > 0
        assert self.slot_offset < self.outer_diameter / 2

    def map_to_area(self, value):
        return (self.outer_diameter**2) * (value / (self.map_dim**2))

    def map_to_length(self, value: float) -> float:
        return self.outer_diameter * (value / self.map_dim)

    def get_face_map(self) -> np.ndarray:
        slot_offset_normalized = self.normalize(self.slot_offset)
        map_x = self.get_maps()[0]
        core_map = self.get_empty_face_map()
        core_map[map_x > slot_offset_normalized] = 0
        return core_map
