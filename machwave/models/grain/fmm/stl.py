from abc import ABC

import numpy as np
import trimesh

import machwave.models.grain as grain
import machwave.models.grain.base as grain_base
import machwave.models.grain.fmm as grain_fmm


def _resample_nearest(
    volume: np.typing.NDArray[np.int_],
    target_shape: tuple[int, ...],
) -> np.typing.NDArray[np.int_]:
    """Nearest-neighbour resample a 3D array onto an exact target shape."""
    index = [
        np.minimum(np.arange(t) * s // t, s - 1)
        for t, s in zip(target_shape, volume.shape)
    ]
    return volume[np.ix_(*index)]


class FMMSTLGrainSegment(grain_fmm.FMMGrainSegment3D, ABC):
    """FMM grain segment loaded from an STL mesh."""

    def __init__(
        self,
        file_path: str,
        outer_diameter: float,
        length: float,
        inhibited_surfaces: grain_base.InhibitedSurfaces | None = None,
        map_dim: int = 50,
    ) -> None:
        """
        Initialize an STL-backed FMM grain segment.

        Args:
            file_path: Path to a watertight STL mesh of the grain.
            outer_diameter: Outer diameter [m].
            length: Segment length [m].
            inhibited_surfaces: Surfaces inhibited from burning.
            map_dim: Pixel resolution of the cross-section map.
        """
        self.file_path = file_path
        self.outer_diameter = outer_diameter
        self.length = length

        # "Cache" variables:
        self.face_area_interp_func = None

        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            inhibited_surfaces=inhibited_surfaces,
            map_dim=map_dim,
        )

    def validate(self) -> None:
        """Validate STL grain segment geometry."""
        grain.GrainSegment.validate(self)
        if not self.map_dim >= 20:
            raise grain.GrainGeometryError(
                f"Map dimension must be at least 20 for STL grains, got {self.map_dim}"
            )
        self._validate_normalized_length()

    def get_voxel_size(self) -> float:
        """Return the voxelization pitch [m]."""
        return self.outer_diameter / (self.map_dim - 1)

    def get_initial_face_map(self) -> np.typing.NDArray[np.int_]:
        """
        Generate the initial face map by voxelizing an STL mesh.

        The trimesh voxel grid does not line up with the FMM grid, so it is
        resampled onto the canonical `(normalized_length, map_dim, map_dim)`
        shape the rest of the 3D machinery expects.
        """
        mesh = trimesh.load_mesh(self.file_path)
        assert isinstance(mesh, trimesh.Trimesh), "Expected a single Trimesh"
        assert mesh.is_watertight, "Mesh must be watertight"

        voxels = mesh.voxelized(pitch=self.get_voxel_size())
        assert voxels is not None, "Voxelization failed"
        voxel_map = voxels.fill().matrix.view(np.ndarray).transpose().astype(np.int_)

        return _resample_nearest(voxel_map, self.get_maps()[0].shape)
