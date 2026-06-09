"""
Fast Marching Method (FMM) grain geometry models.

Supports both 2D and 3D geometries, as well as STL meshes.

References:
    https://math.berkeley.edu/~sethian/2006/Explanations/fast_marching_explain.html
"""

# Import base (and its module-level constants) first so the constants are bound
# on the package namespace before the subclasses, which reference them as default
# argument values, are imported.
from machwave.models.grain.fmm.base import (
    DEFAULT_GRID_RESOLUTION,
    MINIMUM_GRID_RESOLUTION,
    FMMGrainSegment,
)
from machwave.models.grain.fmm._2d import FMMGrainSegment2D
from machwave.models.grain.fmm._3d import FMMGrainSegment3D
from machwave.models.grain.fmm.stl import FMMSTLGrainSegment

__all__ = [
    "DEFAULT_GRID_RESOLUTION",
    "MINIMUM_GRID_RESOLUTION",
    "FMMGrainSegment",
    "FMMGrainSegment2D",
    "FMMGrainSegment3D",
    "FMMSTLGrainSegment",
]
