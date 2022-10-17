# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at me@felipebm.com.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from abc import ABC
from typing import Optional

import numpy as np

from . import FMMGrainSegment
from .. import GrainSegment3D
from rocketsolver.utils.geometric import get_length, get_contours


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

        self.map_dim = 10

    def get_normalized_length(self) -> int:
        return int(self.map_dim * self.length / self.outer_diameter)

    def get_maps(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        if self.maps is None:
            map_y, map_z, map_x = np.meshgrid(
                np.linspace(-1, 1, self.map_dim),
                np.linspace(1, 0, self.get_normalized_length()),  # z axis
                np.linspace(-1, 1, self.map_dim),
            )

            self.maps = (map_x, map_y, map_z)

        return self.maps

    def get_mask(self) -> np.ndarray:
        if self.mask is None:
            map_x, map_y, _ = self.get_maps()
            self.mask = (map_x**2 + map_y**2) > 1

        return self.mask

    def get_contours(
        self, web_distance: float, length_normalized: float
    ) -> np.ndarray:
        map_dist = self.normalize(web_distance)
        valid = np.logical_not(self.get_mask())

        map = np.logical_and(self.get_regression_map() > (map_dist), valid)

        return get_contours(
            map[length_normalized],
            map_dist,
        )

    def get_burn_area(self, web_distance: float) -> float:
        """
        NOTE: Still needs to be tested.
        """
        if web_distance > self.get_web_thickness():
            return 0

        burn_area_array = np.array([])

        for i in range(self.get_normalized_length()):
            contours = self.get_contours(
                web_distance=web_distance, length_normalized=i
            )
            perimeter = np.sum(
                [
                    self.map_to_length(get_length(contour, self.map_dim))
                    for contour in contours
                ]
            )

            burn_area_array = np.append(
                burn_area_array, perimeter * self.length / self.map_dim
            )

        return np.sum(burn_area_array)

    def get_volume_per_element(self) -> float:
        return (self.denormalize(self.get_cell_size()) * 2) ** 3

    def get_volume(self, web_distance: float) -> float:
        face_map = self.get_face_map(web_distance=web_distance)
        active_elements = np.count_nonzero(face_map == 1)
        volume_per_element = self.get_volume_per_element()
        return active_elements * volume_per_element
