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


class WagonWheelGrainSegment(FMMGrainSegment2D):
    def __init__(
        self,
        length: float,
        outer_diameter: float,
        core_diameter: float,
        number_of_ports: int,
        port_inner_diameter: float,
        port_outer_diameter: float,
        port_angular_width: float,
        spacing: float,
        inhibited_ends: Optional[int] = 0,
    ) -> None:
        self.core_diameter = core_diameter
        self.number_of_ports = int(number_of_ports)
        self.port_inner_diameter = port_inner_diameter
        self.port_outer_diameter = port_outer_diameter
        self.port_angular_width = port_angular_width

        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            spacing=spacing,
            inhibited_ends=inhibited_ends,
        )

    @validate_assertions(exception=GrainGeometryError)
    def validate(self) -> None:
        super().validate()

        assert self.number_of_ports > 0
        assert self.number_of_ports % 2 == 0
        assert isinstance(self.number_of_ports, int)
        assert self.port_inner_diameter > self.core_diameter
        assert self.port_outer_diameter > self.port_inner_diameter
        assert self.port_angular_width > 0
        assert self.port_angular_width < 360 / self.number_of_ports

    def get_initial_face_map(self) -> np.ndarray:
        """
        NOTE: Still needs to correctly implement wagon wheel ports.
        """
        map_x, map_y = self.get_maps()
        core_map = self.get_empty_face_map()

        core_diameter_norm = self.normalize(self.core_diameter)
        port_inner_diameter_norm = self.normalize(self.port_inner_diameter)
        port_outer_diameter_norm = self.normalize(self.port_outer_diameter)

        # Create the core:
        core_map[map_x**2 + map_y**2 < (core_diameter_norm / 2) ** 2] = 0

        radius = map_x**2 + map_y**2

        # Create the ports:
        for port_index in range(int(self.number_of_ports)):
            displacement_angle = (
                2 * np.pi / self.number_of_ports * (port_index)
            )

            theta_2 = (
                np.deg2rad(self.port_angular_width / 2) + displacement_angle
            )
            theta_1 = displacement_angle - np.deg2rad(
                self.port_angular_width / 2
            )

            map_x_y_arctan = np.arctan(map_y / map_x)

            core_map[
                (radius < (port_outer_diameter_norm / 2) ** 2)
                & (radius > (port_inner_diameter_norm / 2) ** 2)
                & (np.abs(map_x_y_arctan) < theta_2)
                & (np.abs(map_x_y_arctan) > theta_1)
            ] = 0

        return core_map
