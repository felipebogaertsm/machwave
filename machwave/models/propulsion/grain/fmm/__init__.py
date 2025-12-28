"""
This module contains classes that model grain geometries using the Fast Marching
Method (FMM). Both 2D and 3D geometries are supported, along with STL files.

References:
https://math.berkeley.edu/~sethian/2006/Explanations/fast_marching_explain.html
"""

from machwave.models.propulsion.grain.fmm._2d import FMMGrainSegment2D
from machwave.models.propulsion.grain.fmm._3d import FMMGrainSegment3D
from machwave.models.propulsion.grain.fmm.base import FMMGrainSegment
from machwave.models.propulsion.grain.fmm.stl import FMMSTLGrainSegment

__all__ = [
    "FMMGrainSegment",
    "FMMGrainSegment2D",
    "FMMGrainSegment3D",
    "FMMSTLGrainSegment",
]
