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
from skimage import measure
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter

from .. import GrainSegment
from rocketsolver.utils.geometric import get_length


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

    @abstractmethod
    def map_to_length(self, value: float) -> float:
        """
        Converts pixels to meters. Used to extract real distances from pixel
        distances such as contour lengths
        """
        pass

    @abstractmethod
    def get_segment_length(self, web_thickness: float) -> float:
        """
        Gets instantaneous segment length, in function of the web thickness
        traveled.
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

    def get_face_area(self, web_thickness: float) -> float:
        """
        NOTE: Still needs to implement control for when web thickness is over.
        """

        map_distance = self.normalize(web_thickness)
        return self.get_face_area_interp_func()(map_distance)

    def get_core_perimeter(self, web_thickness: float) -> float:
        """
        Not implemented yet.
        """
        map_dist = self.normalize(web_thickness)

        core_perimeter = 0
        contours = measure.find_contours(
            self.get_regression_map(), map_dist, fully_connected="low"
        )

        for contour in contours:
            core_perimeter += self.map_to_length(
                get_length(contour, self.map_dim)
            )

        return core_perimeter

    def get_core_area(self, web_thickness: float) -> float:
        """
        Not implemented yet.
        """
        return self.get_core_perimeter(web_thickness) * (
            self.get_segment_length(web_thickness=web_thickness)
            - 2 * web_thickness
        )

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

    def get_face_area_interp_func(self):
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
        return interp1d(polled, face_area)
