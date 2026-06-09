import pytest

from tests.factories import (
    ConicalGrainSegmentFactory,
    DGrainSegmentFactory,
    FinocylGrainSegmentFactory,
    MultiPortGrainSegmentFactory,
    RodAndTubeGrainSegmentFactory,
    StarGrainSegmentFactory,
    WagonWheelGrainSegmentFactory,
)

fmm_factories = pytest.mark.parametrize(
    "factory",
    [
        StarGrainSegmentFactory,
        WagonWheelGrainSegmentFactory,
        RodAndTubeGrainSegmentFactory,
        MultiPortGrainSegmentFactory,
        DGrainSegmentFactory,
        ConicalGrainSegmentFactory,
        FinocylGrainSegmentFactory,
    ],
)


@fmm_factories
def test_grid_resolution_forwarded_to_segment(factory):
    """The constructor forwards grid_resolution to the FMM base instead of dropping it."""
    segment = factory.build(grid_resolution=120)
    assert segment.grid_resolution == 120


@fmm_factories
def test_grid_resolution_defaults_to_100(factory):
    """Omitting grid_resolution keeps the base default."""
    segment = factory.build()
    assert segment.grid_resolution == 100
