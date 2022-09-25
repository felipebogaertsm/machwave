# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from abc import ABC, abstractmethod
from typing import Optional

import numpy as np
import skfmm
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter

from .. import GrainSegment


class FMMGrainSegment(GrainSegment, ABC):
    def __init__(self, map_dim: Optional[int] = 20) -> None:
        self.map_dim = map_dim

        super().__init__()

    @abstractmethod
    def get_face_map(self) -> np.ndarray:
        """
        Method needs to be implemented for each and every geometry.
        """
        pass

    @abstractmethod
    def map_to_area(self, value: float) -> float:
        """
        Used to convert sq pixels to sqm.
        For extracting real areas from the regression map.
        """
        pass

    def validate(self) -> None:
        """
        NOTE: Minimum map_dim still needs to be implemented/asserted.
        """
        super().validate()

    def normalize(self, value: int | float) -> float:
        return value / (0.5 * self.outer_diameter)

    def denormalize(self, value: int | float) -> float:
        return (value / 2) * (self.outer_diameter)

    def get_burn_area(self) -> float:
        """
        Not implemented yet.
        """
        pass

    def get_volume(self) -> float:
        """
        Not implemented yet.
        """
        pass

    def get_maps(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Returns a tuple, containing map_x in index 0 and map_y in index 1.
        """
        return np.meshgrid(
            np.linspace(-1, 1, self.map_dim), np.linspace(-1, 1, self.map_dim)
        )

    def get_mask(self) -> np.ndarray:
        map_x, map_y = self.get_maps()
        return (map_x**2 + map_y**2) > 1

    def get_empty_face_map(self) -> np.ndarray:
        """
        Returns the empty geometry map/mesh of the 2D grain face.

        https://pythonhosted.org/scikit-fmm/
        """
        return np.ones_like(self.get_maps()[0])

    def get_masked_face(self) -> np.ndarray:
        """
        Masks the face map.
        The mask is circular shaped and normalized to the shape of the matrix.
        """
        return np.ma.MaskedArray(self.get_face_map(), self.get_mask())

    def get_cell_size(self) -> float:
        return 1 / self.map_dim

    def get_regression_map(self):
        """
        Uses the fast marching method to generate an image of how the grain
        regresses from the core map. The map is stored under
        self.regressionMap.
        """
        return (
            skfmm.distance(self.get_masked_face(), dx=self.get_cell_size()) * 2
        )

    def unknown(self):
        """
        Function calculates many parameters, still needs to be organized.
        """
        regression_map = self.get_regression_map()
        max_dist = np.amax(regression_map)

        face_area = []
        polled = []
        valid = np.logical_not(self.get_mask())

        for i in range(int(max_dist * self.map_dim) + 2):
            polled.append(i / self.map_dim)
            face_area.append(
                self.map_to_area(
                    np.count_nonzero(
                        np.logical_and(
                            regression_map > (i / self.map_dim), valid
                        )
                    )
                )
            )

        face_area = savgol_filter(face_area, 31, 5)
        face_area_interp = interp1d(polled, face_area)
        print(face_area_interp)
