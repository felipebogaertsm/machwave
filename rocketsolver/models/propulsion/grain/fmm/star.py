# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at me@felipebm.com.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from typing import Optional

import numpy as np

from . import FMMGrainSegment2D
from .. import GrainGeometryError
from rocketsolver.utils.decorators import validate_assertions


class StarGrainSegment(FMMGrainSegment2D):
    def __init__(
        self,
        length: float,
        outer_diameter: float,
        number_of_points: int,
        point_length: float,
        point_width: float,
        spacing: float,
        inhibited_ends: Optional[int] = 0,
    ) -> None:
        self.number_of_points = int(number_of_points)
        self.point_length = point_length
        self.point_width = point_width

        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            spacing=spacing,
            inhibited_ends=inhibited_ends,
        )

    @validate_assertions(exception=GrainGeometryError)
    def validate(self) -> None:
        super().validate()

        assert self.number_of_points > 0
        assert isinstance(self.number_of_points, int)
        assert self.point_length > 0
        assert self.point_width > 0

    def get_face_map(self) -> np.ndarray:
        map_x, map_y = self.get_maps()
        core_map = self.get_empty_face_map()

        point_length_normalized = self.normalize(self.point_length)
        point_width_normalized = self.normalize(self.point_width)

        for i in range(0, self.number_of_points):
            theta = 2 * np.pi / self.number_of_points * i
            rect = abs(np.cos(theta) * map_x + np.sin(theta) * map_y)

            width = (
                point_width_normalized
                / 2
                * (
                    1
                    - (
                        ((map_x**2 + map_y**2) ** 0.5)
                        / point_length_normalized
                    )
                )
            )

            vect = rect < width
            near = np.sin(theta) * map_x - np.cos(theta) * map_y > -0.025

            core_map[np.logical_and(vect, near)] = 0

        return core_map
