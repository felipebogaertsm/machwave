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

from .. import GrainSegment


class FMMGrainSegment(GrainSegment, ABC):
    def __init__(self, map_dim: Optional[int] = 10) -> None:
        self.map_dim = map_dim

        super().__init__()

    def validate(self) -> None:
        super().validate()

        # assert self.map_dim >= 100

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

    @abstractmethod
    def get_face_map(self):
        pass

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
