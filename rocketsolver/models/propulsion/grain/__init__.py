# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from abc import ABC, abstractmethod

import numpy as np

from rocketsolver.utils.geometric import get_circle_area


class GrainGeometryError(Exception):
    def __init__(self, message: float) -> None:
        self.message = message

        super().__init__(self.message)


class GrainSegment(ABC):
    @abstractmethod
    def get_burn_area(self, web_distance: float) -> float:
        pass

    @abstractmethod
    def get_volume(self, web_distance: float) -> float:
        pass


class Grain:
    def __init__(self) -> None:
        self.segments: list[GrainSegment] = []

    def add_segment(self, new_segment: GrainSegment) -> None:
        """
        Adds a new segment to the grain.

        :param GrainSegment new_segment: The new segment to be added
        :rtype: None
        :raises Exceptiom: If the new_segment is not valid
        """
        if isinstance(new_segment, GrainSegment):
            self.segments.append(new_segment)
        else:
            raise Exception("Argument is not a GrainSegment class instance")

    @property
    def total_length(self) -> float:
        """
        Calculates total length of the grain.

        :rtype: float
        """
        return np.sum(
            [grain.length + grain.spacing for grain in self.segments]
        )

    @property
    def segment_count(self) -> int:
        """
        Returns the number of segments in the grain.

        :rtype: int
        """
        return len(self.segments)

    def get_burn_area(self, web_thickness: float) -> float:
        """
        Calculates the BATES burn area given the web distance.

        :param float web_thickness: Instant web thickness value
        :return float: Instant burn area, in m^2 and in function of web
        :rtype: float
        """
        return np.sum(
            [segment.get_burn_area(web_thickness) for segment in self.segments]
        )

    def get_propellant_volume(self, web_thickness: float) -> float:
        """
        Calculates the BATES grain volume given the web distance.

        :param float web_thickness: Instant web thickness value
        :return: Instant propellant volume, in m^3 and in function of web
        :rtype: float
        """
        return np.sum(
            [segment.get_volume(web_thickness) for segment in self.segments]
        )

    def get_mass_flux_per_segment(
        self,
        burn_rate: np.ndarray,
        propellant_density: float,
        web_thickness: np.ndarray,
    ) -> np.ndarray:
        """
        Returns a numpy multidimensional array with the mass flux for each
        grain.
        """
        segment_mass_flux = np.zeros(
            (self.segment_count, np.size(web_thickness))
        )
        segment_mass_flux = np.zeros(
            (self.segment_count, np.size(web_thickness))
        )
        total_burn_area = np.zeros(
            (self.segment_count, np.size(web_thickness))
        )

        for j in range(self.segment_count):  # iterating through each segment
            for i in range(np.size(burn_rate)):
                for _ in range(j + 1):
                    total_burn_area[j, i] = total_burn_area[
                        j, i
                    ] + self.segments[j].get_burn_area(web_thickness[i])

                segment_mass_flux[j, i] = (
                    total_burn_area[j, i] * propellant_density * burn_rate[i]
                ) / (
                    get_circle_area(
                        self.segments[j].core_diameter + web_thickness[i]
                    )
                )

        return segment_mass_flux
