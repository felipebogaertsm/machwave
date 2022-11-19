# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at me@felipebm.com.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from abc import ABC
from typing import Optional

import numpy as np

from ._3d import FMMGrainSegment3D


class FMMSTLGrainSegment(FMMGrainSegment3D, ABC):
    """
    Fast Marching Method (FMM) implementation for a grain segment obtained
    from an STL file.
    """

    def __init__(
        self,
        file_path: str,
        spacing: float,
        inhibited_ends: Optional[int] = 0,
        map_dim: Optional[int] = 1000,
    ) -> None:

        self.file_path = file_path

        # "Cache" variables:
        self.face_area_interp_func = None

        # NOTE: write methods to obtain these values:
        length = 0
        outer_diameter = 0

        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            spacing=spacing,
            inhibited_ends=inhibited_ends,
            map_dim=map_dim,
        )

    def get_maps(self) -> tuple[np.ndarray, np.ndarray]:
        """
        NOTE: STILL NEEDS TO BE IMPLEMENTED.
        """
        pass
