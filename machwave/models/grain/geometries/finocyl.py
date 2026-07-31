import numpy as np

import machwave.models.grain as grain
import machwave.models.grain.base as grain_base
import machwave.models.grain.fmm as grain_fmm


class FinocylGrainSegment(grain_fmm.FMMGrainSegment3D):
    """Grain segment with a central bore and radial fins over a partial axial section."""

    def __init__(
        self,
        length: float,
        outer_diameter: float,
        core_diameter: float,
        number_of_fins: int,
        fin_length: float,
        fin_width: float,
        finned_length: float,
        fin_axial_offset: float = 0.0,
        transition_length: float = 0.0,
        inhibited_surfaces: grain_base.InhibitedSurfaces | None = None,
        grid_resolution: int = grain_fmm.DEFAULT_GRID_RESOLUTION,
        density_ratio: float = 1.0,
    ) -> None:
        """
        Initialize a finocyl grain segment.

        Args:
            length: Segment length [m].
            outer_diameter: Outer diameter [m].
            core_diameter: Central bore diameter [m].
            number_of_fins: Number of evenly spaced radial fins.
            fin_length: Radial penetration of each fin, measured from the bore
                edge.
            fin_width: Tangential thickness of each fin slot [m].
            finned_length: Axial extent of the finned section [m].
            fin_axial_offset: Axial position where the finned section begins,
                measured from the aft (nozzle) end [m].
            transition_length: Axial length over which the fins taper linearly in
                depth between full depth and the surrounding cylindrical bore,
                applied at each interface between the finned and cylindrical
                sections. A value of 0.0 gives an abrupt step [m].
            inhibited_surfaces: Surfaces inhibited from burning.
            grid_resolution: Grid points per axis of the cross-section.
            density_ratio: Ratio of real to ideal propellant density.
        """
        self.core_diameter = core_diameter
        self.number_of_fins = int(number_of_fins)
        self.fin_length = fin_length
        self.fin_width = fin_width
        self.finned_length = finned_length
        self.fin_axial_offset = fin_axial_offset
        self.transition_length = transition_length

        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            inhibited_surfaces=inhibited_surfaces,
            grid_resolution=grid_resolution,
            density_ratio=density_ratio,
        )

    def validate(self) -> None:
        """Validate finocyl segment geometry."""
        super().validate()

        if not self.core_diameter > 0:
            raise grain.GrainGeometryError(
                f"Core diameter must be positive, got {self.core_diameter}"
            )
        if not self.core_diameter < self.outer_diameter:
            raise grain.GrainGeometryError(
                f"Core diameter ({self.core_diameter}) must be less than "
                f"outer diameter ({self.outer_diameter})"
            )
        if not isinstance(self.number_of_fins, int):
            raise grain.GrainGeometryError(
                f"Number of fins must be an integer, got "
                f"{type(self.number_of_fins).__name__}"
            )
        if not self.number_of_fins > 0:
            raise grain.GrainGeometryError(
                f"Number of fins must be positive, got {self.number_of_fins}"
            )
        if not self.number_of_fins < 12:
            raise grain.GrainGeometryError(
                f"Number of fins must be less than 12, got {self.number_of_fins}"
            )
        if not self.fin_length > 0:
            raise grain.GrainGeometryError(
                f"Fin length must be positive, got {self.fin_length}"
            )
        if not self.fin_width > 0:
            raise grain.GrainGeometryError(
                f"Fin width must be positive, got {self.fin_width}"
            )

        fin_tip_diameter = self.core_diameter + 2 * self.fin_length
        if not fin_tip_diameter < self.outer_diameter:
            raise grain.GrainGeometryError(
                f"Fin tip diameter ({fin_tip_diameter}) must be less than "
                f"outer diameter ({self.outer_diameter})"
            )

        if self.number_of_fins >= 2:
            fin_tip_radius = self.core_diameter / 2 + self.fin_length
            max_fin_width = 2 * fin_tip_radius * np.tan(np.pi / self.number_of_fins)
            if not self.fin_width < max_fin_width:
                raise grain.GrainGeometryError(
                    f"Fin width ({self.fin_width}) must be less than "
                    f"{max_fin_width} to avoid overlapping fins"
                )

        if not self.finned_length > 0:
            raise grain.GrainGeometryError(
                f"Finned length must be positive, got {self.finned_length}"
            )
        if not self.finned_length <= self.length:
            raise grain.GrainGeometryError(
                f"Finned length ({self.finned_length}) must not exceed "
                f"segment length ({self.length})"
            )
        if not self.fin_axial_offset >= 0:
            raise grain.GrainGeometryError(
                f"Fin axial offset must be non-negative, got {self.fin_axial_offset}"
            )
        if not self.fin_axial_offset + self.finned_length <= self.length:
            raise grain.GrainGeometryError(
                f"Finned section (offset {self.fin_axial_offset} + length "
                f"{self.finned_length}) must fit within the segment length "
                f"({self.length})"
            )
        if not self.transition_length >= 0:
            raise grain.GrainGeometryError(
                f"Transition length must be non-negative, got {self.transition_length}"
            )

        tapering_interfaces = (self.fin_axial_offset > 0) + (
            self.fin_axial_offset + self.finned_length < self.length
        )
        if not tapering_interfaces * self.transition_length <= self.finned_length:
            raise grain.GrainGeometryError(
                f"Transition length ({self.transition_length}) is too large for the "
                f"fins to reach full depth over a finned length of "
                f"{self.finned_length} with {tapering_interfaces} tapering "
                f"interface(s)"
            )

    def _fin_depth_fraction(
        self, axial_position: np.typing.NDArray[np.float64]
    ) -> np.typing.NDArray[np.float64]:
        """
        Return the fin depth as a fraction of full depth at each axial position.

        Arguments:
            axial_position: Axial position(s) along the grain, measured from the aft
                (nozzle) end [m].

        Returns:
            Fin depth fraction(s) between 0 and 1, where 1 corresponds to the full fin
            length.
        """
        fin_start = self.fin_axial_offset
        fin_end = self.fin_axial_offset + self.finned_length

        if self.transition_length == 0:
            return ((axial_position >= fin_start) & (axial_position <= fin_end)).astype(
                np.float64
            )

        rise = (
            np.clip((axial_position - fin_start) / self.transition_length, 0.0, 1.0)
            if fin_start > 0
            else (axial_position >= fin_start).astype(np.float64)
        )
        fall = (
            np.clip((fin_end - axial_position) / self.transition_length, 0.0, 1.0)
            if fin_end < self.length
            else (axial_position <= fin_end).astype(np.float64)
        )
        return np.minimum(rise, fall)

    def generate_initial_face_map(self) -> np.typing.NDArray[np.int_]:
        """Return the initial face map for the finocyl port."""
        map_x, map_y, map_z = self.get_coordinate_grids()
        core_map = self.get_empty_face_map()

        core_radius_normalized = self.normalize(self.core_diameter) / 2
        fin_width_normalized = self.normalize(self.fin_width)
        fin_length_normalized = self.normalize(self.fin_length)

        radius = np.sqrt(map_x**2 + map_y**2)
        core_map[radius < core_radius_normalized] = 0

        axial_position = (1 - map_z) * self.length
        local_fin_tip_normalized = core_radius_normalized + (
            self._fin_depth_fraction(axial_position) * fin_length_normalized
        )

        for i in range(self.number_of_fins):
            theta = 2 * np.pi / self.number_of_fins * i
            within_width = (
                np.abs(np.cos(theta) * map_x + np.sin(theta) * map_y)
                < fin_width_normalized / 2
            )
            radial = np.sin(theta) * map_x - np.cos(theta) * map_y
            within_length = (radial > 0) & (radial < local_fin_tip_normalized)
            core_map[within_width & within_length] = 0

        return core_map
