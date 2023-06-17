from abc import ABC
from typing import Optional

import numpy as np
import trimesh
from trimesh import load_mesh
from trimesh.voxel import creation

from ._3d import FMMGrainSegment3D
from .. import GrainGeometryError
from rocketsolver.services.decorators import validate_assertions


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
        inhibited_ends: Optional[int] = 0,
        map_dim: Optional[int] = 50,
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

    def get_initial_face_map(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Generate a map by voxelizing an STL file. Uses trimesh library.

        NOTE: Still needs to convert boolean matrix to masked array.
        """
        mesh = load_mesh(self.file_path)
        assert mesh.is_watertight

        volume = mesh.voxelized(pitch=self.get_voxel_size()).fill()
        map = volume.matrix.view(np.ndarray).transpose() * 1

        assert map.shape == self.get_maps()[0].shape
        return map
