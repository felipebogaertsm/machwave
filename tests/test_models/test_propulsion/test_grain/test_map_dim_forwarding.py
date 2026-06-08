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
def test_map_dim_forwarded_to_segment(factory):
    """The constructor forwards map_dim to the FMM base instead of dropping it."""
    segment = factory.build(map_dim=120)
    assert segment.map_dim == 120


@fmm_factories
def test_map_dim_defaults_to_100(factory):
    """Omitting map_dim keeps the base default."""
    segment = factory.build()
    assert segment.map_dim == 100
