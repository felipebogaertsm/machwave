"""Pytest configuration for FMM grain moment-of-inertia tests.

Mirrors the fan-out used by the CoG suite — see test_cog/conftest.py.
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
