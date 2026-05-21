import numpy as np

import machwave.models.grain as grain
import machwave.models.grain.base as grain_base
import machwave.models.grain.fmm as grain_fmm


class ConicalGrainSegment(grain_fmm.FMMGrainSegment3D):
    """Grain segment with a conical port tapering between two diameters."""

    def __init__(
        self,
        length: float,
        outer_diameter: float,
        upper_core_diameter: float,
        lower_core_diameter: float,
        inhibited_surfaces: grain_base.InhibitedSurfaces | None = None,
        density_ratio: float = 1.0,
    ) -> None:
        """
        Initialize a conical grain segment.

        Args:
            length: Segment length [m].
            outer_diameter: Outer diameter [m].
            upper_core_diameter: Core diameter at the upper (bulkhead) end [m].
            lower_core_diameter: Core diameter at the lower (nozzle) end [m].
            inhibited_surfaces: Surfaces inhibited from burning.
            density_ratio: Ratio of real to ideal propellant density.
        """
        self.upper_core_diameter = upper_core_diameter
        self.lower_core_diameter = lower_core_diameter

        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            inhibited_surfaces=inhibited_surfaces,
            density_ratio=density_ratio,
        )

    def validate(self) -> None:
        """Validate conical segment geometry."""
        super().validate()

        if not self.upper_core_diameter > 0:
            raise grain.GrainGeometryError(
                f"Upper core diameter must be positive, got {self.upper_core_diameter}"
            )
        if not self.upper_core_diameter < self.outer_diameter:
            raise grain.GrainGeometryError(
                f"Upper core diameter ({self.upper_core_diameter}) must be less than "
                f"outer diameter ({self.outer_diameter})"
            )
        if not self.lower_core_diameter > 0:
            raise grain.GrainGeometryError(
                f"Lower core diameter must be positive, got {self.lower_core_diameter}"
            )
        if not self.lower_core_diameter < self.outer_diameter:
            raise grain.GrainGeometryError(
                f"Lower core diameter ({self.lower_core_diameter}) must be less than "
                f"outer diameter ({self.outer_diameter})"
            )

    def get_initial_face_map(self) -> np.typing.NDArray[np.int_]:
        """Return the initial face map for the conical port."""
        map_x, map_y, map_z = self.get_maps()
        core_map = self.get_empty_face_map()

        upper_core_norm = self.normalize(self.upper_core_diameter)
        lower_core_norm = self.normalize(self.lower_core_diameter)

        radius = np.sqrt(map_x**2 + map_y**2)
        core_diameter = map_z * (upper_core_norm - lower_core_norm) + lower_core_norm

        core_map[radius < core_diameter / 2] = 0
        core_map[0] = 0  # Inhibit the bottom end
        core_map[-1] = 0  # Inhibit the top end

        return core_map
