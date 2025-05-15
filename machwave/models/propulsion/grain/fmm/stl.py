from abc import ABC

import numpy as np
import trimesh

from machwave.models.propulsion.grain import GrainGeometryError
from machwave.models.propulsion.grain.fmm import FMMGrainSegment3D
from machwave.services.decorators import validate_assertions


class FMMSTLGrainSegment(FMMGrainSegment3D, ABC):
    """
    Fast Marching Method (FMM) implementation for a grain segment obtained
    from an STL file.
    """

    def __init__(
        self,
        file_path: str,
        outer_diameter: float,
        length: float,
        spacing: float,
        inhibited_ends: int = 0,
        map_dim: int = 50,
    ) -> None:
        self.file_path = file_path
        self.outer_diameter = outer_diameter
        self.length = length

        # "Cache" variables:
        self.face_area_interp_func = None

        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            spacing=spacing,
            inhibited_ends=inhibited_ends,
            map_dim=map_dim,
        )

    @validate_assertions(exception=GrainGeometryError)
    def validate(self) -> None:
        assert self.map_dim >= 20

    def get_voxel_size(self) -> float:
        """
        NOTE: Only returns correct voxel size if map_dim is an odd number.

        :return: the voxel edge size.
        :rtype: float
        """
        return self.outer_diameter / int(self.map_dim - 1)

    def get_initial_face_map(self) -> np.typing.NDArray[np.int_]:
        """
        Generate a map by voxelizing an STL file. Uses trimesh library.

        NOTE: Still needs to convert boolean matrix to masked array.
        """
        mesh: trimesh.Trimesh = trimesh.load_mesh(self.file_path)
        assert mesh.is_watertight, "Mesh must be watertight"

        volume = mesh.voxelized(pitch=self.get_voxel_size()).fill()
        voxel_map: np.typing.NDArray[np.int_] = (
            volume.matrix.view(np.ndarray).transpose().astype(np.int_)
        )

        assert voxel_map.shape == self.get_maps()[0].shape, (
            "Generated map shape mismatch"
        )

        return voxel_map
