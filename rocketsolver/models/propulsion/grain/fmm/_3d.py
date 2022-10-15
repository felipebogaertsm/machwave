# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at me@felipebm.com.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from abc import ABC, abstractmethod
from typing import Optional

import numpy as np

from . import FMMGrainSegment
from .. import GrainSegment3D, GrainGeometryError
from rocketsolver.utils.decorators import validate_assertions


class FMMGrainSegment3D(FMMGrainSegment, GrainSegment3D, ABC):
    """
    Fast Marching Method (FMM) implementation for 3D grain segment.

    This class was inspired by the Andrew Reilley's software openMotor, in
    particular the fmm module.
    openMotor's repository can be accessed at:
    https://github.com/reilleya/openMotor
    """

    def __init__(
        self,
        length: float,
        outer_diameter: float,
        spacing: float,
        inhibited_ends: Optional[int] = 0,
        map_dim: Optional[int] = 1000,
    ) -> None:

        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            spacing=spacing,
            inhibited_ends=inhibited_ends,
            map_dim=map_dim,
        )

    def get_maps(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        if self.maps is None:
            map_x, map_y, map_z = np.meshgrid(
                np.linspace(-1, 1, self.map_dim),
                np.linspace(-1, 1, self.map_dim),
                np.linspace(0, 1, self.map_dim),  # z axis
            )

        for i in range(self.map_dim):
            z = np.ones_like(map_x[0]) * (i) / (self.map_dim - 1)

            if i == 0:
                map_z = np.array([z])
            else:
                map_z = np.append(map_z, [z], axis=0)

        self.maps = (map_x, map_y, map_z)
        return self.maps

    def get_burn_area(self, web_distance: float) -> float:
        """
        NOTE: Still needs to be implemented.
        """
        pass

    def get_volume(self, web_distance: float) -> float:
        """
        NOTE: Still needs to be implemented.
        """
        pass
