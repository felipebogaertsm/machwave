from abc import ABC

import numpy as np
import trimesh

from machwave.models.grain import GrainGeometryError
from machwave.models.grain.base import InhibitedSurfaces
from machwave.models.grain.fmm import FMMGrainSegment3D


class FMMSTLGrainSegment(FMMGrainSegment3D, ABC):
    """FMM grain segment loaded from an STL mesh."""

    def __init__(
        self,
        file_path: str,
        outer_diameter: float,
        length: float,
        inhibited_surfaces: InhibitedSurfaces | None = None,
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
        if not self.map_dim >= 20:
            raise GrainGeometryError(
                f"Map dimension must be at least 20 for STL grains, got {self.map_dim}"
            )

    def get_voxel_size(self) -> float:
        """
        Return the voxel edge size [m].

        Note:
            Only returns correct voxel size if `map_dim` is an odd number.
        """
        return self.outer_diameter / int(self.map_dim - 1)

    def get_initial_face_map(self) -> np.typing.NDArray[np.int_]:
        """
        Generate the initial face map by voxelizing an STL file.

        Uses the `trimesh` library. Still needs to convert the boolean matrix
        to a masked array.
        """
        mesh = trimesh.load_mesh(self.file_path)
        assert isinstance(mesh, trimesh.Trimesh), "Expected a single Trimesh"
        assert mesh.is_watertight, "Mesh must be watertight"

        voxels = mesh.voxelized(pitch=self.get_voxel_size())
        assert voxels is not None, "Voxelization failed"
        volume = voxels.fill()
        voxel_map: np.typing.NDArray[np.int_] = (
            volume.matrix.view(np.ndarray).transpose().astype(np.int_)
        )

        assert voxel_map.shape == self.get_maps()[0].shape, (
            "Generated map shape mismatch"
        )

        return voxel_map
