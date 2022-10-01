# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at me@felipebm.com.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from abc import ABC, abstractmethod
from typing import Optional

import numpy as np

from rocketsolver.utils.decorators import validate_assertions


class GrainGeometryError(Exception):
    def __init__(self, message: float) -> None:
        self.message = message

        super().__init__(self.message)


class GrainSegment(ABC):
    """
    Class that represents a grain segment.
    """

    def __init__(
        self,
        spacing: float,
        inhibited_ends: Optional[int] = 0,
    ) -> None:
        self.spacing = spacing
        self.inhibited_ends = inhibited_ends

        self.validate()

    @abstractmethod
    def get_web_thickness(self) -> float:
        """
        Calculates the total web thickness of the segment.

        :return: The total web thickness of the segment
        :rtype: float
        """
        pass

    @abstractmethod
    def get_length(self, web_distance: float) -> float:
        pass

    @abstractmethod
    def get_burn_area(self, web_distance: float) -> float:
        """
        Calculates burn area in function of the web distance traveled.

        :param float web_distance: Web distance traveled
        :return: Burn area in function of the web distance traveled
        :rtype: float
        """
        pass

    @abstractmethod
    def get_volume(self, web_distance: float) -> float:
        """
        Calculates volume in function of the web distance traveled.

        :param float web_distance: Web distance traveled
        :return: Segment volume in function of the instant web thickness
        :rtype: float
        """
        pass

    @validate_assertions(exception=GrainGeometryError)
    def validate(self) -> None:
        """
        Validates grain geometry.
        For every attribute that a child class adds, it must be validated here.

        :rtype: None
        """
        assert self.spacing >= 0
        assert self.inhibited_ends in [0, 1, 2]


class GrainSegment2D(GrainSegment, ABC):
    """
    Class that represents a 2D grain segment.

    A 2D grain segment is a segment that has the same cross sectional geometry
    throughout its length.

    Some examples of 2D grain geometries:
    - BATES
    - Tubular
    - Pseudo-finocyl

    Some examples of non-2D (3D) grain geometries:
    - Conical
    - Finocyl
    """

    def __init__(
        self,
        length: float,
        outer_diameter: float,
        spacing: float,
        inhibited_ends: Optional[int] = 0,
    ) -> None:
        self.length = length
        self.outer_diameter = outer_diameter

        super().__init__(
            spacing=spacing,
            inhibited_ends=inhibited_ends,
        )

    @abstractmethod
    def get_core_area(self, web_distance: float) -> float:
        """
        Calculates the core area in function of the web distance traveled.

        Example:
        In a simple tubular geometry, the core area would be equal to the
        instant length of the segment times the instant core area.

        :param float web_distance: Web distance traveled
        :return: Core area in function of the web distance traveled
        :rtype: float
        """
        pass

    @abstractmethod
    def get_face_area(self, web_distance: float) -> float:
        """
        Calculates the face area in function of the web distance traveled.

        Example:
        In a simple tubular geometry, the face area would be equal to the
        outer diameter area minus the instantaneous core diameter area.

        :param float web_distance: Web distance traveled
        :return: Face area in function of the web distance traveled
        :rtype: float
        """
        pass

    @validate_assertions(exception=GrainGeometryError)
    def validate(self) -> None:
        super().validate()

        assert self.length > 0
        assert self.outer_diameter > 0

    def get_length(self, web_distance: float) -> float:
        return self.length - web_distance * (2 - self.inhibited_ends)

    def get_burn_area(self, web_distance: float) -> float:
        core_area = self.get_core_area(web_distance=web_distance)
        single_face_area = self.get_face_area(web_distance=web_distance)
        total_face_area = (2 - self.inhibited_ends) * single_face_area
        return core_area + total_face_area

    def get_volume(self, web_distance: float) -> float:
        return self.length * self.get_face_area(web_distance=web_distance)


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

    def get_burn_area(self, web_distance: float) -> float:
        """
        Calculates the BATES burn area given the web distance.

        :param float web_distance: Instant web thickness value
        :return float: Instant burn area, in m^2 and in function of web
        :rtype: float
        """
        return np.sum(
            [segment.get_burn_area(web_distance) for segment in self.segments]
        )

    def get_propellant_volume(self, web_distance: float) -> float:
        """
        Calculates the BATES grain volume given the web distance.

        :param float web_distance: Instant web thickness value
        :return: Instant propellant volume, in m^3 and in function of web
        :rtype: float
        """
        return np.sum(
            [segment.get_volume(web_distance) for segment in self.segments]
        )

    def get_mass_flux_per_segment(
        self,
        burn_rate: np.ndarray,
        propellant_density: float,
        web_distance: np.ndarray,
    ) -> np.ndarray:
        """
        Returns a numpy multidimensional array with the mass flux for each
        grain.
        """
        segment_mass_flux = np.zeros(
            (self.segment_count, np.size(web_distance))
        )
        total_burn_area = np.zeros((self.segment_count, np.size(web_distance)))

        for j in range(self.segment_count):  # iterating through each segment
            for i in range(np.size(burn_rate)):
                for _ in range(j + 1):
                    total_burn_area[j, i] = total_burn_area[
                        j, i
                    ] + self.segments[j].get_burn_area(web_distance[i])

                segment_mass_flux[j, i] = (
                    total_burn_area[j, i] * propellant_density * burn_rate[i]
                ) / (self.segments[j].get_core_area(web_distance[i]))

        return segment_mass_flux
