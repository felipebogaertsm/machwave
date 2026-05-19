import numpy as np

from machwave.models.grain import GrainGeometryError
from machwave.models.grain.base import InhibitedSurfaces
from machwave.models.grain.fmm import FMMGrainSegment2D


class DGrainSegment(FMMGrainSegment2D):
    """D-shaped grain segment with a single offset planar slot."""

    def __init__(
        self,
        length: float,
        outer_diameter: float,
        slot_offset: float,
        inhibited_surfaces: InhibitedSurfaces | None = None,
        density_ratio: float = 1.0,
    ) -> None:
        """
        Initialize a D-grain segment.

        Args:
            length: Segment length [m].
            outer_diameter: Outer diameter [m].
            slot_offset: Distance from the grain center to the slot face [m].
            inhibited_surfaces: Surfaces inhibited from burning.
            density_ratio: Ratio of real to ideal propellant density.
        """
        self.slot_offset = slot_offset

        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            inhibited_surfaces=inhibited_surfaces,
            density_ratio=density_ratio,
        )

    def validate(self) -> None:
        """Validate D-grain segment geometry."""
        super().validate()

        if not self.slot_offset >= 0:
            raise GrainGeometryError(
                f"Slot offset must be non-negative, got {self.slot_offset}"
            )
        max_slot_offset = self.outer_diameter / 2
        if not self.slot_offset < max_slot_offset:
            raise GrainGeometryError(
                f"Slot offset ({self.slot_offset}) must be less than "
                f"half the outer diameter ({max_slot_offset})"
            )

    def get_initial_face_map(self) -> np.typing.NDArray[np.int_]:
        """Return the initial face map for the D-grain port."""
        slot_offset_normalized = self.normalize(self.slot_offset)
        map_x = self.get_maps()[0]
        core_map = self.get_empty_face_map()
        core_map[map_x > slot_offset_normalized] = 0
        return core_map
