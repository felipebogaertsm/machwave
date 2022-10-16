# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at me@felipebm.com.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from abc import ABC
from typing import Callable, Optional

import numpy as np
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter

from . import FMMGrainSegment
from .. import GrainSegment3D


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
        map_dim: Optional[int] = 100,
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
            map_y, map_z, map_x = np.meshgrid(
                np.linspace(-1, 1, self.map_dim),
                np.linspace(
                    1, 0, int(self.map_dim * self.length / self.outer_diameter)
                ),  # z axis
                np.linspace(-1, 1, self.map_dim),
            )

            self.maps = (map_x, map_y, map_z)

        return self.maps

    def get_mask(self) -> np.ndarray:
        if self.mask is None:
            map_x, map_y, _ = self.get_maps()
            self.mask = (map_x**2 + map_y**2) > 1

        return self.mask

    def get_burn_area(self, web_distance: float) -> float:
        """
        NOTE: Still needs to be tested.
        """
        if web_distance > self.get_web_thickness():
            return 0

        return self.get_face_area_interp_func()(self.normalize(web_distance))

    def get_volume_per_element(self) -> float:
        return (self.denormalize(self.get_cell_size()) * 2) ** 3

    def get_volume(self, web_distance: float) -> float:
        face_map = self.get_face_map(web_distance=web_distance)
        active_elements = np.count_nonzero(face_map == 1)
        volume_per_element = self.get_volume_per_element()
        return active_elements * volume_per_element
