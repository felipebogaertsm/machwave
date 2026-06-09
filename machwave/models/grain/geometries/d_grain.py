import numpy as np

import machwave.models.grain as grain
import machwave.models.grain.base as grain_base
import machwave.models.grain.fmm as grain_fmm


class DGrainSegment(grain_fmm.FMMGrainSegment2D):
    """D-shaped grain segment with a single offset planar slot."""

    def __init__(
        self,
        length: float,
        outer_diameter: float,
        slot_offset: float,
        inhibited_surfaces: grain_base.InhibitedSurfaces | None = None,
        grid_resolution: int = grain_fmm.DEFAULT_GRID_RESOLUTION,
        density_ratio: float = 1.0,
    ) -> None:
        """
        Initialize a D-grain segment.

        Args:
            length: Segment length [m].
            outer_diameter: Outer diameter [m].
            slot_offset: Distance from the grain center to the slot face [m].
            inhibited_surfaces: Surfaces inhibited from burning.
            grid_resolution: Grid points per axis of the cross-section.
            density_ratio: Ratio of real to ideal propellant density.
        """
        self.slot_offset = slot_offset

        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            inhibited_surfaces=inhibited_surfaces,
            grid_resolution=grid_resolution,
            density_ratio=density_ratio,
        )

    def validate(self) -> None:
        """Validate D-grain segment geometry."""
        super().validate()

        if not self.slot_offset >= 0:
            raise grain.GrainGeometryError(
                f"Slot offset must be non-negative, got {self.slot_offset}"
            )
        max_slot_offset = self.outer_diameter / 2
        if not self.slot_offset < max_slot_offset:
            raise grain.GrainGeometryError(
                f"Slot offset ({self.slot_offset}) must be less than "
                f"half the outer diameter ({max_slot_offset})"
            )

    def generate_initial_face_map(self) -> np.typing.NDArray[np.int_]:
        """Return the initial face map for the D-grain port."""
        slot_offset_normalized = self.normalize(self.slot_offset)
        map_x = self.get_coordinate_grids()[0]
        core_map = self.get_empty_face_map()
        core_map[map_x > slot_offset_normalized] = 0
        return core_map
