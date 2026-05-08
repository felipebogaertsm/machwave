"""Pytest configuration for FMM grain CoG tests.

Defines parametrize markers that fan tests out across all FMM2D and FMM3D
geometry factories. Each entry is the factory's ``build`` classmethod, which
the test calls with whatever overrides it cares about (length, outer_diameter,
density_ratio, ...).
"""

import pytest

from tests.factories import (
    ConicalGrainSegmentFactory,
    DGrainSegmentFactory,
    MultiPortGrainSegmentFactory,
    RodAndTubeGrainSegmentFactory,
    StarGrainSegmentFactory,
    WagonWheelGrainSegmentFactory,
)

fmm2d_geometries = pytest.mark.parametrize(
    "segment_factory,geometry_name",
    [
        (StarGrainSegmentFactory.build, "Star"),
        (WagonWheelGrainSegmentFactory.build, "WagonWheel"),
        (RodAndTubeGrainSegmentFactory.build, "RodAndTube"),
        (MultiPortGrainSegmentFactory.build, "MultiPort"),
        (DGrainSegmentFactory.build, "DGrain"),
    ],
    ids=["Star", "WagonWheel", "RodAndTube", "MultiPort", "DGrain"],
)

fmm3d_geometries = pytest.mark.parametrize(
    "segment_factory,geometry_name",
    [
        (ConicalGrainSegmentFactory.build, "Conical"),
    ],
    ids=["Conical"],
)
