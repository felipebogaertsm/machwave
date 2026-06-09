import numpy as np

import machwave.models.grain as grain
import machwave.models.grain.base as grain_base
import machwave.models.grain.fmm as grain_fmm


class RodAndTubeGrainSegment(grain_fmm.FMMGrainSegment2D):
    """Rod-and-tube grain segment: central rod inside a concentric tube."""

    def __init__(
        self,
        length: float,
        outer_diameter: float,
        rod_outer_diameter: float,
        tube_inner_diameter: float,
        inhibited_surfaces: grain_base.InhibitedSurfaces | None = None,
        grid_resolution: int = grain_fmm.DEFAULT_GRID_RESOLUTION,
        density_ratio: float = 1.0,
    ) -> None:
        """
        Initialize a rod-and-tube grain segment.

        Args:
            length: Segment length [m].
            outer_diameter: Outer (tube outer) diameter [m].
            rod_outer_diameter: Central rod outer diameter [m].
            tube_inner_diameter: Tube inner diameter [m].
            inhibited_surfaces: Surfaces inhibited from burning.
            grid_resolution: Grid points per axis of the cross-section.
            density_ratio: Ratio of real to ideal propellant density.
        """
        self.rod_outer_diameter = rod_outer_diameter
        self.tube_inner_diameter = tube_inner_diameter

        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            inhibited_surfaces=inhibited_surfaces,
            grid_resolution=grid_resolution,
            density_ratio=density_ratio,
        )

    def validate(self) -> None:
        """Validate rod-and-tube segment geometry."""
        super().validate()

        if not self.rod_outer_diameter > 0:
            raise grain.GrainGeometryError(
                f"Rod outer diameter must be positive, got {self.rod_outer_diameter}"
            )
        if not self.tube_inner_diameter > self.rod_outer_diameter:
            raise grain.GrainGeometryError(
                f"Tube inner diameter ({self.tube_inner_diameter}) must be greater than "
                f"rod outer diameter ({self.rod_outer_diameter})"
            )
        if not self.tube_inner_diameter < self.outer_diameter:
            raise grain.GrainGeometryError(
                f"Tube inner diameter ({self.tube_inner_diameter}) must be less than "
                f"outer diameter ({self.outer_diameter})"
            )

    def generate_initial_face_map(self) -> np.typing.NDArray[np.int_]:
        """NOTE: Still needs to correctly implement wagon wheel ports."""
        map_x, map_y = self.get_coordinate_grids()
        core_map = self.get_empty_face_map()

        rod_outer_diameter_normalized = self.normalize(self.rod_outer_diameter)
        tube_inner_diameter_normalized = self.normalize(self.tube_inner_diameter)

        radius = np.sqrt(map_x**2 + map_y**2)

        core_map[
            (radius > rod_outer_diameter_normalized / 2)
            & (radius < tube_inner_diameter_normalized / 2)
        ] = 0

        return core_map
