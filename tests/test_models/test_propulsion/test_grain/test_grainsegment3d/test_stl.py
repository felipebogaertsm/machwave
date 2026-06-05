"""
Tests for the STL-backed 3D FMM grain segment.

The mesh is generated at test time (a watertight hollow cylinder) and written to
a temporary STL file, so no binary fixture is committed.
"""

import numpy as np
import pytest
import trimesh

import machwave.models.grain as grain_models
from machwave.models.grain.fmm import FMMSTLGrainSegment

OUTER_DIAMETER = 41e-3
LENGTH = 68e-3
BORE_DIAMETER = 15e-3


@pytest.fixture(scope="module")
def tube_stl_path(tmp_path_factory):
    """A watertight tube (hollow cylinder) grain mesh written to a temp STL."""
    mesh = trimesh.creation.annulus(
        r_min=BORE_DIAMETER / 2, r_max=OUTER_DIAMETER / 2, height=LENGTH
    )
    path = tmp_path_factory.mktemp("stl") / "tube.stl"
    mesh.export(path)
    return str(path)


@pytest.fixture(scope="module")
def tube_segment(tube_stl_path):
    return FMMSTLGrainSegment(
        file_path=tube_stl_path, outer_diameter=OUTER_DIAMETER, length=LENGTH
    )


def test_face_map_matches_the_fmm_grid_shape(tube_segment):
    """The voxelized mesh is resampled onto the canonical FMM grid shape.

    Before the fix the raw voxel grid was off by a voxel on every axis, so the
    shape assertion hard-failed even for a correctly sized mesh.
    """
    face_map = tube_segment.get_initial_face_map()
    assert face_map.shape == tube_segment.get_maps()[0].shape


def test_volume_matches_the_analytical_tube(tube_segment):
    """Propellant volume is within voxelization error of the analytical tube."""
    analytical_volume = np.pi / 4 * (OUTER_DIAMETER**2 - BORE_DIAMETER**2) * LENGTH
    assert tube_segment.get_volume(web_distance=0.0) == pytest.approx(
        analytical_volume, rel=0.1
    )


@pytest.mark.parametrize(
    "overrides",
    [
        dict(outer_diameter=0.0),
        dict(outer_diameter=-1e-3),
        dict(length=0.0),
        dict(map_dim=10),  # below the STL map-dimension floor of 20
        dict(length=2e-3),  # axial map collapses below three slices
    ],
)
def test_invalid_geometry_raises(tube_stl_path, overrides):
    params = dict(file_path=tube_stl_path, outer_diameter=OUTER_DIAMETER, length=LENGTH)
    params.update(overrides)
    with pytest.raises(grain_models.GrainGeometryError):
        FMMSTLGrainSegment(**params)
