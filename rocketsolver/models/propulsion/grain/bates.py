# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import numpy as np

from . import GrainSegment, GrainGeometryError


class BatesSegment(GrainSegment):
    def __init__(
        self,
        outer_diameter: float,
        core_diameter: float,
        length: float,
        spacing: float,
    ) -> None:
        self.outer_diameter = outer_diameter
        self.core_diameter = core_diameter
        self.length = length
        self.spacing = spacing

        self.validate()

    def validate(self) -> None:
        """
        Validates segment's geometry. They include:

        - Outer diameter shall be larger than core diameter
        - Core diameter shall be larger than 0
        - Length shall be larger than 0
        - Spacing shall be larger than 0

        :rtype: None
        """
        try:
            assert self.outer_diameter > self.core_diameter
            assert self.core_diameter > 0
            assert self.length > 0
            assert self.spacing >= 0
        except AssertionError:
            raise GrainGeometryError("Invalid segment geometry")

    @property
    def total_web_thickness(self) -> float:
        """
        Calculates the total web thickness of the segment.
        More details on the web thickness of BATES grains can be found in:
        https://www.nakka-rocketry.net/design1.html

        :return: The total web thickness of the segment
        :rtype: float
        """
        return 0.5 * (self.outer_diameter - self.core_diameter)

    def get_optimal_length(self) -> float:
        """
        Returns the optimal length for BATES segment.
        More details on the calculation:
        https://www.nakka-rocketry.net/th_grain.html

        :return: Optimal length for neutral burn of BATES segment
        :rtype: float
        """
        return 1e3 * 0.5 * (3 * self.outer_diameter + self.core_diameter)

    def get_burn_area(self, web_thickness: float) -> float:
        """
        Calculates burn area in function of the instant web thickness.

        :param float web_thickness: Instant web thickness
        :return: Burn area in function of the instant web thickness
        :rtype: float
        """
        if self.total_web_thickness >= web_thickness:
            return np.pi * (
                (
                    (self.outer_diameter**2)
                    - (self.core_diameter + 2 * web_thickness) ** 2
                )
                / 2
                + (
                    (self.length - 2 * web_thickness)
                    * (self.core_diameter + 2 * web_thickness)
                )
            )
        else:
            return 0

    def get_volume(self, web_thickness: float) -> float:
        """
        Calculates volume in function of the instant web thickness.

        :param float web_thickness: Instant web thickness
        :return: Segment volume in function of the instant web thickness
        :rtype: float
        """
        if self.total_web_thickness >= web_thickness:
            return (np.pi / 4) * (
                (
                    (self.outer_diameter**2)
                    - ((self.core_diameter + 2 * web_thickness) ** 2)
                )
                * (self.length - 2 * web_thickness)
            )
        else:
            return 0
