from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import numpy as np


class GrainGeometryError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message

        super().__init__(self.message)


@dataclass(frozen=True, slots=True)
class InhibitedSurfaces:
    """Describes which surfaces of a grain segment are inhibited.

    Attributes:
        outer_surface: If True, the outer cylindrical surface is inhibited.
        inner_surface: If True, the inner surface is inhibited.
        upper_end: If True, the upper end (towards bulkhead) face is inhibited.
        lower_end: If True, the lower end (towards nozzle) face is inhibited.
    """

    outer_surface: bool = True
    inner_surface: bool = False
    upper_end: bool = False
    lower_end: bool = False

    def __post_init__(self) -> None:
        if (
            self.outer_surface
            and self.inner_surface
            and self.upper_end
            and self.lower_end
        ):
            raise GrainGeometryError(
                "All surfaces cannot be inhibited at the same time."
            )


class GrainSegment(ABC):
    """
    Represents a grain segment.
    """

    def __init__(
        self,
        length: float,
        outer_diameter: float,
        inhibited_surfaces: InhibitedSurfaces | None = None,
        density_ratio: float = 1.0,
    ) -> None:
        self.length = length
        self.outer_diameter = outer_diameter
        self.inhibited_surfaces = (
            inhibited_surfaces
            if inhibited_surfaces is not None
            else InhibitedSurfaces()
        )
        self.density_ratio = density_ratio

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
    def get_port_area(self, web_distance: float, *args: Any, **kwargs: Any) -> float:
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
        Calculates the center of gravity of the segment.

        The coordinate system origin is at the port, closest to the nozzle,
        with positive x-direction pointing toward the bulkhead.

        :return: The center of gravity of the segment [x, y, z] in meters
        :rtype: np.typing.NDArray[np.float64]
        """
        pass

    @abstractmethod
    def get_moment_of_inertia(self, *args, **kwargs) -> np.typing.NDArray[np.float64]:
        """
        Calculates the moment of inertia tensor of the segment at its center of gravity.

        Returns:
            A 3x3 array representing the inertia tensor [kg-m^2] with components:
                [[Ixx, Ixy, Ixz],
                 [Iyx, Iyy, Iyz],
                 [Izx, Izy, Izz]]
        """
        pass

    def get_mass(self, web_distance: float, ideal_density: float) -> float:
        """
        Calculates the mass of the segment at a given web distance.

        :param float web_distance: Web distance traveled [m]
        :param float ideal_density: Ideal propellant density [kg/m^3]
        :return: Mass of the segment at the given web distance [kg]
        :rtype: float
        """
        if ideal_density <= 0:
            raise ValueError(f"ideal_density must be > 0 (got {ideal_density})")

        return self.get_volume(web_distance) * ideal_density * self.density_ratio

    def validate(self) -> None:
        """
        Validates grain geometry.
        For every attribute that a child class adds, it must be validated here.
        """
        if not isinstance(self.inhibited_surfaces, InhibitedSurfaces):
            raise GrainGeometryError(
                "inhibited_surfaces must be an InhibitedSurfaces instance"
            )
        if not self.length > 0:
            raise GrainGeometryError(f"Length must be positive, got {self.length}")
        if not self.outer_diameter > 0:
            raise GrainGeometryError(
                f"Outer diameter must be positive, got {self.outer_diameter}"
            )
        if not (0.0 <= self.density_ratio <= 1.0):
            raise GrainGeometryError(
                f"Density ratio must be between 0.0 and 1.0, got {self.density_ratio}"
            )


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
        inhibited_surfaces: InhibitedSurfaces | None = None,
        density_ratio: float = 1.0,
    ) -> None:
        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            inhibited_surfaces=inhibited_surfaces,
            density_ratio=density_ratio,
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
        exposed_ends = (not self.inhibited_surfaces.upper_end) + (
            not self.inhibited_surfaces.lower_end
        )
        return self.length - web_distance * exposed_ends

    def get_burn_area(self, web_distance: float) -> float:
        if web_distance > self.get_web_thickness():
            return 0

        core_area = (
            0.0
            if self.inhibited_surfaces.inner_surface
            else self.get_core_area(web_distance=web_distance)
        )
        single_face_area = self.get_face_area(web_distance=web_distance)
        exposed_ends = (not self.inhibited_surfaces.upper_end) + (
            not self.inhibited_surfaces.lower_end
        )
        total_face_area = exposed_ends * single_face_area
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
        inhibited_surfaces: InhibitedSurfaces | None = None,
        density_ratio: float = 1.0,
    ) -> None:
        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            inhibited_surfaces=inhibited_surfaces,
            density_ratio=density_ratio,
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
        exposed_ends = (not self.inhibited_surfaces.upper_end) + (
            not self.inhibited_surfaces.lower_end
        )
        return self.length - web_distance * exposed_ends


class Grain:
    def __init__(self, spacing: float = 0.0) -> None:
        """
        Initialize a grain assembly.

        Args:
            spacing: Distance between segments in meters. Default is 0.0
                (no spacing).
        """
        self.segments: list[GrainSegment] = []
        self.spacing = spacing

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

    def get_effective_density_ratio(self, *, web_distance: float) -> float:
        r"""Return an effective (burn-area weighted) density ratio.

        Used for gas generation terms where $\dot{m} \propto A_b r \rho_p$.
        """
        burn_areas = np.asarray(
            [seg.get_burn_area(web_distance) for seg in self.segments],
            dtype=np.float64,
        )
        total_burn_area = float(np.sum(burn_areas))
        if total_burn_area <= 0:
            return 0.0

        density_ratios = np.asarray(
            [seg.density_ratio for seg in self.segments], dtype=np.float64
        )
        return float(np.sum(burn_areas * density_ratios) / total_burn_area)

    def get_real_density(self, *, web_distance: float, ideal_density: float) -> float:
        """Return grain *effective real* propellant density [kg/m^3]."""
        if ideal_density <= 0:
            raise ValueError(f"ideal_density must be > 0 (got {ideal_density})")
        return ideal_density * self.get_effective_density_ratio(
            web_distance=web_distance
        )

    def get_propellant_mass(
        self, *, web_distance: float, ideal_density: float
    ) -> float:
        """Return remaining propellant mass [kg] at a given web distance."""
        if ideal_density <= 0:
            raise ValueError(f"ideal_density must be > 0 (got {ideal_density})")

        volumes = np.asarray(
            [seg.get_volume(web_distance) for seg in self.segments], dtype=np.float64
        )
        density_ratios = np.asarray(
            [seg.density_ratio for seg in self.segments], dtype=np.float64
        )
        return float(np.sum(volumes * density_ratios) * ideal_density)

    @property
    def total_length(self) -> float:
        """
        Calculates total length of the grain.

        Example:
        - 1 segment of 0.5 m length -> total length = 0.5 m
        - 2 segments of 0.5 m length with 0.1 m spacing -> total length = 1.1 m
        - 3 segments of 0.5 m length with 0.1 m spacing -> total length = 1.7 m

        :rtype: float
        """
        total_segment_length = np.sum([grain.length for grain in self.segments])
        if len(self.segments) > 1:  # add spacing between segments
            total_segment_length += self.spacing * (len(self.segments) - 1)
        return total_segment_length

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
        """
        Calculates the center of gravity of the grain.

        Takes the mass-weighted average of all segment centers of gravity,
        accounting for varying density ratios and spacing between segments.

        Args:
            web_distance: Web distance traveled [m].

        Returns:
            A 1D array of shape (3,) representing the [x, y, z] coordinates
            of the center of gravity [m]. Origin is at the port of the grain
            (closest to nozzle), with positive x pointing toward bulkhead.

        Raises:
            ValueError: If no segments are found in the grain.
        """
        if not self.segments:
            raise ValueError("No segments found, cannot compute CoG.")

        weighted_cogs = []
        # Iterate segments in reverse order (last added is closest to port)
        axial_position = 0.0

        for segment in reversed(self.segments):
            # Segment's local CoG, relative to its own port
            local_cog = segment.get_center_of_gravity(web_distance=web_distance)

            # Global CoG position from grain's port
            global_cog = local_cog.copy()
            global_cog[0] = axial_position + local_cog[0]

            mass = segment.get_volume(web_distance=web_distance) * segment.density_ratio
            weighted_cogs.append(global_cog * mass)

            # Move to next segment
            axial_position += segment.length + self.spacing

        total_weighted_cogs = np.stack(weighted_cogs, axis=0).sum(
            axis=0, dtype=np.float64
        )
        volumes = np.asarray(
            [seg.get_volume(web_distance) for seg in self.segments], dtype=np.float64
        )
        density_ratios = np.asarray(
            [seg.density_ratio for seg in self.segments], dtype=np.float64
        )
        total_mass_normalized = float(np.sum(volumes * density_ratios))

        return (total_weighted_cogs / total_mass_normalized).astype(np.float64)

    def get_moment_of_inertia(
        self, ideal_density: float, web_distance: float = 0.0
    ) -> np.typing.NDArray[np.float64]:
        """
        Combines the inertia tensors of all grain segments using the parallel axis
        theorem, accounting for varying density ratios and spacing between segments.

        Args:
            ideal_density: Propellant ideal density [kg/m^3].
            web_distance: Web distance traveled [m].

        Returns:
            A 3x3 inertia tensor [kg-m^2] at the grain's center of gravity:
                [[Ixx, Ixy, Ixz],
                 [Ixy, Iyy, Iyz],
                 [Ixz, Iyz, Izz]]

            Coordinate system: Origin at grain's center of gravity, with:
            - x-axis: axial direction (toward bulkhead)
            - y-axis: radial direction
            - z-axis: radial direction

        Raises:
            ValueError: If no segments are found in the grain.
        """
        if not self.segments:
            raise ValueError("No segments found, cannot compute moment of inertia.")

        grain_cog = self.get_center_of_gravity(web_distance)
        total_inertia = np.zeros((3, 3), dtype=np.float64)

        axial_position = 0.0
        for segment in reversed(self.segments):  # last added is closest to port
            # From segment's own port
            local_cog = segment.get_center_of_gravity(web_distance=web_distance)

            global_cog = local_cog.copy()  # from grain's port
            global_cog[0] = axial_position + local_cog[0]

            segment_mass = segment.get_mass(
                web_distance=web_distance, ideal_density=ideal_density
            )
            segment_moi = segment.get_moment_of_inertia(
                web_distance=web_distance, ideal_density=ideal_density
            )

            # Vector from grain CoG to segment CoG
            r = global_cog - grain_cog

            # Apply parallel axis theorem
            r_squared = float(np.dot(r, r))
            identity = np.eye(3, dtype=np.float64)
            outer_product = np.outer(r, r)
            parallel_axis_correction = segment_mass * (
                r_squared * identity - outer_product
            )

            # Add this segment's contribution to total inertia
            total_inertia += segment_moi + parallel_axis_correction

            # Move to next segment
            axial_position += segment.length + self.spacing

        return total_inertia.astype(np.float64)

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
        ideal_density: float,
        web_distance: np.ndarray,
    ) -> np.ndarray:
        """
        Returns a numpy multidimensional array with the mass flux for each
        grain.
        """
        segment_mass_flux = np.zeros((self.segment_count, np.size(web_distance)))

        if ideal_density <= 0:
            raise ValueError(f"ideal_density must be > 0 (got {ideal_density})")

        for j in range(self.segment_count):  # iterating through each segment
            for i in range(np.size(burn_rate)):
                core_area = self.segments[j].get_port_area(web_distance[i])
                burn_area = 0

                for k in range(j + 1):
                    burn_area = burn_area + (
                        self.segments[j - k].get_burn_area(web_distance[i])
                        * self.segments[j - k].density_ratio
                    )

                segment_mass_flux[j, i] = (burn_area * ideal_density * burn_rate[i]) / (
                    core_area
                )

        return segment_mass_flux
