from abc import ABC, abstractmethod

import numpy as np

from machwave.services.decorators import validate_assertions


class GrainGeometryError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message

        super().__init__(self.message)


class GrainSegment(ABC):
    """
    Class that represents a grain segment.
    """

    def __init__(
        self,
        length: float,
        outer_diameter: float,
        spacing: float,
        inhibited_ends: int = 0,
    ) -> None:
        self.length = length
        self.outer_diameter = outer_diameter
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
    def get_port_area(self, web_distance: float, *args, **kwargs) -> float:
        """
        Calculates the port area as a function of the web distance traveled.

        This method assumes a 2D or simplified model where the port area can
        be represented by a single scalar value at a given web distance.

        Args:
            web_distance: Distance traveled into the grain web.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            A float representing the port area.
        """
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

    @abstractmethod
    def get_center_of_gravity(self, *args, **kwargs) -> np.typing.NDArray[np.float64]:
        """
        Calculates the center of gravity of the segments in relation to the
        upper end of the segment (closest to the bulkhead).

        :return: The center of gravity of the segment
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
        assert self.length > 0
        assert self.outer_diameter > 0


class GrainSegment2D(GrainSegment, ABC):
    """
    Class that represents a 2D grain segment.

    A 2D grain segment is a segment that has the same cross sectional geometry
    throughout its length.

    Some examples of 2D grain geometries:
    - BATES
    - Tubular
    - Pseudo-finocyl
    """

    def __init__(
        self,
        length: float,
        outer_diameter: float,
        spacing: float,
        inhibited_ends: int = 0,
    ) -> None:
        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
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

        Not to be confused with port area!

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

    def get_length(self, web_distance: float) -> float:
        return self.length - web_distance * (2 - self.inhibited_ends)

    def get_burn_area(self, web_distance: float) -> float:
        if web_distance > self.get_web_thickness():
            return 0

        core_area = self.get_core_area(web_distance=web_distance)
        single_face_area = self.get_face_area(web_distance=web_distance)
        total_face_area = (2 - self.inhibited_ends) * single_face_area
        return core_area + total_face_area

    def get_volume(self, web_distance: float) -> float:
        if self.get_web_thickness() >= web_distance:
            return self.get_length(web_distance=web_distance) * self.get_face_area(
                web_distance=web_distance
            )
        else:
            return 0


class GrainSegment3D(GrainSegment, ABC):
    """
    Class that represents a 3D grain segment.

    Some examples of 3D grain geometries:
    - Conical
    - Finocyl
    """

    def __init__(
        self,
        length: float,
        outer_diameter: float,
        spacing: float,
        inhibited_ends: int = 0,
    ) -> None:
        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            spacing=spacing,
            inhibited_ends=inhibited_ends,
        )

    @abstractmethod
    def get_port_area(self, web_distance: float, z: float) -> float:
        """
        Calculates the port area as a function of the web distance traveled
        and a specified height (z).

        NOTE: This method is not implemented.

        Args:
            web_distance: The distance traveled into the grain web.
            z: The axial position (height) along the grain.

        Returns:
            The port area at the given web distance and height.
        """
        pass

    def get_length(self, web_distance: float) -> float:
        """
        NOTE: Modify later.
        """
        return self.length - web_distance * (2 - self.inhibited_ends)


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
        return np.sum([grain.length + grain.spacing for grain in self.segments])

    @property
    def segment_count(self) -> int:
        """
        Returns the number of segments in the grain.

        :rtype: int
        """
        return len(self.segments)

    def get_center_of_gravity(
        self, web_distance: float
    ) -> np.typing.NDArray[np.float64]:
        weighted_cogs = [
            segment.get_center_of_gravity(web_distance=web_distance)
            * segment.get_volume(web_distance=web_distance)
            for segment in self.segments
        ]
        # If there's a chance segments is empty, handle that:
        if not weighted_cogs:
            # raise an error or return a zero vector
            raise ValueError("No segments found, cannot compute CoG.")

        # Stack into shape (N, 3) and sum along axis=0 => guaranteed shape (3,)
        total_weighted_cogs = np.stack(weighted_cogs, axis=0).sum(
            axis=0, dtype=np.float64
        )

        propellant_vol = self.get_propellant_volume(web_distance=web_distance)

        return (total_weighted_cogs / propellant_vol).astype(np.float64)

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
        return np.sum([segment.get_volume(web_distance) for segment in self.segments])

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
        segment_mass_flux = np.zeros((self.segment_count, np.size(web_distance)))

        for j in range(self.segment_count):  # iterating through each segment
            for i in range(np.size(burn_rate)):
                core_area = self.segments[j].get_port_area(web_distance[i])
                burn_area = 0

                for k in range(j + 1):
                    burn_area = burn_area + self.segments[j - k].get_burn_area(
                        web_distance[i]
                    )

                segment_mass_flux[j, i] = (
                    burn_area * propellant_density * burn_rate[i]
                ) / (core_area)

        return segment_mass_flux
