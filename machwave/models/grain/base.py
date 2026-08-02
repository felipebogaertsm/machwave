import inspect
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import numpy as np


class GrainGeometryError(Exception):
    """Raised when a grain geometry is invalid."""

    def __init__(self, message: str) -> None:
        self.message = message

        super().__init__(self.message)


@dataclass(frozen=True, slots=True)
class InhibitedSurfaces:
    """
    Describes which surfaces of a grain segment are inhibited.

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
        """Reject configurations where every surface is inhibited."""
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
    """Represents a grain segment."""

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

    @property
    def exposed_end_count(self) -> int:
        """Return the number of uninhibited end faces."""
        return (not self.inhibited_surfaces.upper_end) + (
            not self.inhibited_surfaces.lower_end
        )

    def get_axial_web_thickness(self) -> float:
        """
        Return the web distance at which the end faces consume the segment [m].

        Infinite when both ends are inhibited, since no end face regresses.
        """
        if self.exposed_end_count == 0:
            return math.inf
        return self.length / self.exposed_end_count

    @abstractmethod
    def get_web_thickness(self) -> float:
        """Return the total web thickness of the segment [m]."""
        pass

    @abstractmethod
    def get_length(self, web_distance: float) -> float:
        """Return the segment length at a given web distance [m]."""
        pass

    @abstractmethod
    def get_port_area(self, web_distance: float, *args: Any, **kwargs: Any) -> float:
        """
        Return the port area as a function of the web distance traveled.

        This method assumes a 2D or simplified model where the port area can
        be represented by a single scalar value at a given web distance.

        Args:
            web_distance: Distance traveled into the grain web [m].
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Port area [m^2].
        """
        pass

    def get_minimum_port_area(self, web_distance: float) -> float:
        """
        Return the smallest port area along the segment [m^2].

        The cross section of a segment with no axial variation is the same at
        every station, so this is its port area. Segments whose cross section
        varies along the length must override this.

        Args:
            web_distance: Distance traveled into the grain web [m].

        Returns:
            Smallest port area along the segment [m^2].
        """
        return self.get_port_area(web_distance)

    @abstractmethod
    def get_burn_area(self, web_distance: float) -> float:
        """
        Return the burn area at a given web distance.

        Args:
            web_distance: Web distance traveled [m].

        Returns:
            Burn area [m^2].
        """
        pass

    @abstractmethod
    def get_volume(self, web_distance: float) -> float:
        """
        Return the segment volume at a given web distance.

        Args:
            web_distance: Web distance traveled [m].

        Returns:
            Segment volume [m^3].
        """
        pass

    @abstractmethod
    def get_center_of_gravity(self, *args, **kwargs) -> np.typing.NDArray[np.float64]:
        """
        Return the center of gravity of the segment.

        Implementations must place the origin at the segment's own port face,
        the one closest to the nozzle, with positive x pointing toward the
        bulkhead. The origin is the initial position of that face and does not
        move as the face regresses.

        Returns:
            Center of gravity of the segment as `(x, y, z)` [m].
        """
        pass

    @abstractmethod
    def get_moment_of_inertia(self, *args, **kwargs) -> np.typing.NDArray[np.float64]:
        """
        Return the moment of inertia tensor at the segment's center of gravity.

        Returns:
            A 3x3 inertia tensor [kg-m^2] with components:

                [[Ixx, Ixy, Ixz],
                 [Iyx, Iyy, Iyz],
                 [Izx, Izy, Izz]]
        """
        pass

    def get_mass(
        self,
        web_distance: float,
        ideal_density: float,
        volume: float | None = None,
    ) -> float:
        """
        Return the mass of the segment at a given web distance.

        Args:
            web_distance: Web distance traveled [m].
            ideal_density: Ideal propellant density [kg/m^3].
            volume: Segment volume at `web_distance` [m^3], for callers that
                already hold it. Computed here when omitted.

        Returns:
            Mass of the segment [kg].
        """
        if ideal_density <= 0:
            raise ValueError(f"ideal_density must be > 0 (got {ideal_density})")

        if volume is None:
            volume = self.get_volume(web_distance)

        return volume * ideal_density * self.density_ratio

    def validate(self) -> None:
        """
        Validate grain geometry.

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
    A 2D grain segment with uniform cross section along its length.

    Examples of 2D grain geometries: BATES, tubular, pseudo-finocyl.
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
        Return the core area at a given web distance.

        In a simple tubular geometry, the core area equals the instant length
        of the segment times the instant inner circumference. Not to be confused
        with port area.

        Args:
            web_distance: Web distance traveled [m].

        Returns:
            Core area [m^2].
        """
        pass

    @abstractmethod
    def get_face_area(self, web_distance: float) -> float:
        """
        Return the face area at a given web distance.

        In a simple tubular geometry, the face area equals the outer diameter
        area minus the instantaneous core diameter area.

        Args:
            web_distance: Web distance traveled [m].

        Returns:
            Face area [m^2].
        """
        pass

    def get_length(self, web_distance: float) -> float:
        """Return the segment length at a given web distance [m]."""
        return max(0.0, self.length - web_distance * self.exposed_end_count)

    def get_burn_area(self, web_distance: float) -> float:
        """Return the segment burn area at a given web distance [m^2]."""
        if web_distance > self.get_web_thickness():
            return 0.0

        core_area = (
            0.0
            if self.inhibited_surfaces.inner_surface
            else self.get_core_area(web_distance=web_distance)
        )
        single_face_area = self.get_face_area(web_distance=web_distance)
        total_face_area = self.exposed_end_count * single_face_area
        return core_area + total_face_area

    def get_volume(self, web_distance: float) -> float:
        """Return the segment volume at a given web distance [m^3]."""
        if web_distance > self.get_web_thickness():
            return 0.0

        return self.get_length(web_distance=web_distance) * self.get_face_area(
            web_distance=web_distance
        )


class GrainSegment3D(GrainSegment, ABC):
    """
    A 3D grain segment with cross section varying along its length.

    Examples of 3D grain geometries: conical, finocyl.
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
        Return the port area at a given web distance and axial height.

        Args:
            web_distance: Distance traveled into the grain web [m].
            z: Axial position (height) along the grain [m].

        Returns:
            Port area at the given web distance and height [m^2].
        """
        pass

    def get_length(self, web_distance: float) -> float:
        """Return the segment length at a given web distance [m]."""
        return max(0.0, self.length - web_distance * self.exposed_end_count)


class Grain:
    """Assembly of one or more grain segments."""

    def __init__(self, spacing: float = 0.0) -> None:
        """
        Initialize a grain assembly.

        Args:
            spacing: Distance between segments [m]. Default is 0.0 (no spacing).
        """
        self.segments: list[GrainSegment] = []
        self.spacing = spacing

    def add_segment(self, new_segment: GrainSegment) -> None:
        """
        Add a new segment to the grain.

        Args:
            new_segment: The new segment to be added.

        Raises:
            TypeError: If `new_segment` is not a `GrainSegment` instance.
        """
        if isinstance(new_segment, GrainSegment):
            self.segments.append(new_segment)
        else:
            raise TypeError("Argument is not a GrainSegment class instance")

    def get_propellant_mass_per_segment(
        self, *, web_distance: float, ideal_density: float
    ) -> np.typing.NDArray[np.float64]:
        """
        Return per-segment propellant mass at a given web distance.

        Args:
            web_distance: Web distance traveled [m].
            ideal_density: Propellant ideal density [kg/m^3].

        Returns:
            Per-segment mass array of shape `(segment_count,)` [kg].
        """
        if ideal_density <= 0:
            raise ValueError(f"ideal_density must be > 0 (got {ideal_density})")

        volumes = self.get_propellant_volume_per_segment(web_distance)
        density_ratios = self.get_density_ratio_per_segment()
        return volumes * density_ratios * ideal_density

    def get_propellant_mass(
        self, *, web_distance: float, ideal_density: float
    ) -> float:
        """Return remaining propellant mass [kg] at a given web distance."""
        return float(
            np.sum(
                self.get_propellant_mass_per_segment(
                    web_distance=web_distance, ideal_density=ideal_density
                )
            )
        )

    @property
    def total_length(self) -> float:
        """
        Return the total length of the grain [m].

        Examples:
            - 1 segment of 0.5 m length -> total length = 0.5 m.
            - 2 segments of 0.5 m length with 0.1 m spacing -> total length = 1.1 m.
            - 3 segments of 0.5 m length with 0.1 m spacing -> total length = 1.7 m.
        """
        total_segment_length = np.sum([grain.length for grain in self.segments])
        if len(self.segments) > 1:  # add spacing between segments
            total_segment_length += self.spacing * (len(self.segments) - 1)
        return total_segment_length

    @property
    def segment_count(self) -> int:
        """Return the number of segments in the grain."""
        return len(self.segments)

    def get_center_of_gravity(
        self,
        web_distance: float,
        *,
        volume_per_segment: np.typing.NDArray[np.float64] | None = None,
    ) -> np.typing.NDArray[np.float64]:
        """
        Return the center of gravity of the grain.

        Takes the mass-weighted average of all segment centers of gravity,
        accounting for varying density ratios and spacing between segments.

        Args:
            web_distance: Web distance traveled [m].
            volume_per_segment: Per-segment volume at `web_distance` [m^3], for
                callers that already hold it. Computed here when omitted.

        Returns:
            A 1D array of shape (3,) with the [x, y, z] coordinates of the
            center of gravity [m]. Origin is at the port of the grain (closest
            to nozzle), with positive x pointing toward bulkhead. Add
            `SolidMotorThrustChamber.nozzle_exit_to_grain_port_distance` to
            reach the motor frame, which is measured from the nozzle exit.

        Raises:
            ValueError: If no segments are found in the grain.
        """
        if not self.segments:
            raise ValueError("No segments found, cannot compute CoG.")

        volumes = (
            self.get_propellant_volume_per_segment(web_distance)
            if volume_per_segment is None
            else volume_per_segment
        )
        density_ratios = self.get_density_ratio_per_segment()

        weighted_cogs = []
        global_cogs = []
        # Iterate segments in reverse order (last added is closest to port)
        axial_position = 0.0

        for index in reversed(range(self.segment_count)):
            segment = self.segments[index]
            # Segment's local CoG, relative to its own port
            local_cog = segment.get_center_of_gravity(web_distance=web_distance)

            # Global CoG position from grain's port
            global_cog = local_cog.copy()
            global_cog[0] = axial_position + local_cog[0]
            global_cogs.append(global_cog)

            weighted_cogs.append(global_cog * (volumes[index] * density_ratios[index]))

            axial_position += segment.length + self.spacing

        total_mass_normalized = float(np.sum(volumes * density_ratios))

        if total_mass_normalized <= 0.0:
            weights = self.get_propellant_volume_per_segment(0.0)[::-1]
            return np.average(
                np.stack(global_cogs, axis=0), axis=0, weights=weights
            ).astype(np.float64)

        total_weighted_cogs = np.stack(weighted_cogs, axis=0).sum(
            axis=0, dtype=np.float64
        )
        return (total_weighted_cogs / total_mass_normalized).astype(np.float64)

    def get_moment_of_inertia(
        self,
        ideal_density: float,
        web_distance: float = 0.0,
        *,
        volume_per_segment: np.typing.NDArray[np.float64] | None = None,
        center_of_gravity: np.typing.NDArray[np.float64] | None = None,
    ) -> np.typing.NDArray[np.float64]:
        """
        Combine the inertia tensors of all grain segments.

        Uses the parallel axis theorem, accounting for varying density ratios
        and spacing between segments.

        Args:
            ideal_density: Propellant ideal density [kg/m^3].
            web_distance: Web distance traveled [m].
            volume_per_segment: Per-segment volume at `web_distance` [m^3], for
                callers that already hold it. Computed here when omitted.
            center_of_gravity: Grain center of gravity at `web_distance` [m],
                for callers that already hold it. Computed here when omitted.

        Returns:
            A 3x3 inertia tensor [kg-m^2] at the grain's center of gravity:

                [[Ixx, Ixy, Ixz],
                 [Ixy, Iyy, Iyz],
                 [Ixz, Iyz, Izz]]

            Coordinate system: origin at grain's center of gravity, with x-axis
            in the axial direction (toward bulkhead) and y-/z-axes in the
            radial plane.

        Raises:
            ValueError: If no segments are found in the grain.
        """
        if not self.segments:
            raise ValueError("No segments found, cannot compute moment of inertia.")

        volumes = (
            self.get_propellant_volume_per_segment(web_distance)
            if volume_per_segment is None
            else volume_per_segment
        )
        grain_cog = (
            self.get_center_of_gravity(web_distance, volume_per_segment=volumes)
            if center_of_gravity is None
            else center_of_gravity
        )
        total_inertia = np.zeros((3, 3), dtype=np.float64)

        axial_position = 0.0
        for index in reversed(range(self.segment_count)):  # last added is at the port
            segment = self.segments[index]
            local_cog = segment.get_center_of_gravity(web_distance=web_distance)

            global_cog = local_cog.copy()
            global_cog[0] = axial_position + local_cog[0]

            segment_mass = segment.get_mass(
                web_distance=web_distance,
                ideal_density=ideal_density,
                volume=float(volumes[index]),
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

            total_inertia += segment_moi + parallel_axis_correction

            axial_position += segment.length + self.spacing

        return total_inertia.astype(np.float64)

    def get_density_ratio_per_segment(self) -> np.typing.NDArray[np.float64]:
        """
        Return per-segment density ratios.

        Returns:
            Per-segment density-ratio array of shape `(segment_count,)`.
        """
        return np.asarray(
            [segment.density_ratio for segment in self.segments],
            dtype=np.float64,
        )

    def get_burn_area_per_segment(
        self, web_distance: float
    ) -> np.typing.NDArray[np.float64]:
        """
        Return per-segment burn area at a given web distance.

        Args:
            web_distance: Web distance traveled [m].

        Returns:
            Per-segment burn area array of shape `(segment_count,)` [m^2].
        """
        return np.asarray(
            [segment.get_burn_area(web_distance) for segment in self.segments],
            dtype=np.float64,
        )

    def get_burn_area(self, web_distance: float) -> float:
        """
        Return the grain burn area at a given web distance.

        Args:
            web_distance: Web distance traveled [m].

        Returns:
            Total burn area summed across all segments [m^2].
        """
        return float(np.sum(self.get_burn_area_per_segment(web_distance)))

    def get_propellant_volume_per_segment(
        self, web_distance: float
    ) -> np.typing.NDArray[np.float64]:
        """
        Return per-segment propellant volume at a given web distance.

        Args:
            web_distance: Web distance traveled [m].

        Returns:
            Per-segment volume array of shape `(segment_count,)` [m^3].
        """
        return np.asarray(
            [segment.get_volume(web_distance) for segment in self.segments],
            dtype=np.float64,
        )

    def get_propellant_volume(self, web_distance: float) -> float:
        """
        Return the grain propellant volume at a given web distance.

        Args:
            web_distance: Web distance traveled [m].

        Returns:
            Total propellant volume summed across all segments [m^3].
        """
        return float(np.sum(self.get_propellant_volume_per_segment(web_distance)))

    def get_mass_flux_per_segment(
        self,
        burn_rate: np.ndarray,
        ideal_density: float,
        web_distance: np.ndarray,
    ) -> np.ndarray:
        """
        Return mass flux per segment over time.

        Args:
            burn_rate: Burn rate samples [m/s].
            ideal_density: Propellant ideal density [kg/m^3].
            web_distance: Web distance samples [m].

        Returns:
            Mass flux array of shape `(segment_count, len(web_distance))`
            [kg/(s-m^2)].
        """
        segment_mass_flux = np.zeros((self.segment_count, np.size(web_distance)))

        if ideal_density <= 0:
            raise ValueError(f"ideal_density must be > 0 (got {ideal_density})")

        for j in range(self.segment_count):  # iterating through each segment
            for i in range(np.size(burn_rate)):
                core_area = self.segments[j].get_minimum_port_area(web_distance[i])
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

    def get_segment_mismatches(self) -> list[str]:
        """
        Return per-attribute descriptions of where segments diverge.

        Uses the first segment as reference.

        Returns:
            One description per divergent (segment, attribute) pair.
        """
        if len(self.segments) < 2:
            return []

        first_segment = self.segments[0]
        mismatches: list[str] = []
        base_message = (
            "Segment {index} '{name}' value {value_other!r} differs from "
            "segment 1 value {value_first!r}"
        )
        skipped_kinds = (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        )  # skip *args and **kwargs

        for index, segment in enumerate(self.segments[1:], start=1):
            real_index = index + 1  # 1 based indexing

            if type(segment) is not type(first_segment):
                mismatches.append(
                    base_message.format(
                        index=real_index,
                        name="type",
                        value_other=type(segment).__name__,
                        value_first=type(first_segment).__name__,
                    )
                )
                continue

            parameters = inspect.signature(type(first_segment).__init__).parameters
            for name, parameter in parameters.items():
                if name == "self" or parameter.kind in skipped_kinds:
                    continue
                if not (hasattr(first_segment, name) and hasattr(segment, name)):
                    continue
                value_first = getattr(first_segment, name)
                value_other = getattr(segment, name)

                if isinstance(value_first, float) and isinstance(value_other, float):
                    if math.isclose(
                        value_first, value_other, rel_tol=1e-9, abs_tol=1e-12
                    ):
                        continue
                elif value_first == value_other:
                    continue

                mismatches.append(
                    base_message.format(
                        index=real_index,
                        name=name,
                        value_other=value_other,
                        value_first=value_first,
                    )
                )

        return mismatches
