"""
Fast Marching Method (FMM) grain geometry models.

Supports both 2D and 3D geometries, as well as STL meshes.

References:
    https://math.berkeley.edu/~sethian/2006/Explanations/fast_marching_explain.html
"""

from machwave.models.grain.fmm._2d import FMMGrainSegment2D
from machwave.models.grain.fmm._3d import FMMGrainSegment3D
from machwave.models.grain.fmm.base import (
    DEFAULT_GRID_RESOLUTION,
    MINIMUM_GRID_RESOLUTION,
    FMMGrainSegment,
)

# stl reads the 3D class and the default resolution from this package namespace, so
# it loads after them.
# isort: split
from machwave.models.grain.fmm.stl import FMMSTLGrainSegment

__all__ = [
    "DEFAULT_GRID_RESOLUTION",
    "MINIMUM_GRID_RESOLUTION",
    "FMMGrainSegment",
    "FMMGrainSegment2D",
    "FMMGrainSegment3D",
    "FMMSTLGrainSegment",
]
