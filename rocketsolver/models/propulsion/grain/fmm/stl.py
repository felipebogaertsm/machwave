# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at me@felipebm.com.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from abc import ABC
from trimesh import load_mesh
from typing import Optional

import numpy as np

from ._3d import FMMGrainSegment3D


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
        map_dim: Optional[int] = 100,
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

    def get_voxel_size(self) -> float:
        """
        :return: the voxel edge size.
        :rtype: float
        """
        return self.outer_diameter / self.map_dim

    def get_initial_face_map(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Generate a map by voxelizing an STL file. Uses trimesh library.

        NOTE: Still needs to convert boolean matrix to masked array.
        """
        mesh = load_mesh(self.file_path)
        assert mesh.is_watertight
        volume = mesh.voxelized(pitch=self.get_voxel_size())
        map = volume.matrix * 1
        return map
