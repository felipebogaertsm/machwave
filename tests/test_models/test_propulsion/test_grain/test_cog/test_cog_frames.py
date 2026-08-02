"""Center of gravity origin conventions at the segment and grain levels."""

import pytest

import machwave.models.grain as grain_models
from tests.factories import (
    BatesSegmentFactory,
    ConicalGrainSegmentFactory,
    DGrainSegmentFactory,
    FinocylGrainSegmentFactory,
    MultiPortGrainSegmentFactory,
    RodAndTubeGrainSegmentFactory,
    StarGrainSegmentFactory,
    WagonWheelGrainSegmentFactory,
)

SEGMENT_FACTORIES = [
    BatesSegmentFactory,
    StarGrainSegmentFactory,
    WagonWheelGrainSegmentFactory,
    RodAndTubeGrainSegmentFactory,
    MultiPortGrainSegmentFactory,
    DGrainSegmentFactory,
    ConicalGrainSegmentFactory,
    FinocylGrainSegmentFactory,
]

all_geometries = pytest.mark.parametrize(
    "segment_factory",
    SEGMENT_FACTORIES,
    ids=[factory.__name__ for factory in SEGMENT_FACTORIES],
)


@all_geometries
def test_segment_origin_is_its_own_port_face(segment_factory) -> None:
    segment = segment_factory.build()
    cog = segment.get_center_of_gravity(web_distance=0.0)

    assert cog.shape == (3,)
    assert 0.0 < cog[0] < segment.length


@all_geometries
def test_grain_origin_matches_the_single_segment_it_holds(segment_factory) -> None:
    segment = segment_factory.build()
    grain = grain_models.Grain()
    grain.add_segment(segment)

    assert grain.get_center_of_gravity(web_distance=0.0)[0] == pytest.approx(
        segment.get_center_of_gravity(web_distance=0.0)[0]
    )


@all_geometries
def test_grain_origin_is_the_port_of_the_last_added_segment(segment_factory) -> None:
    spacing = 7e-3
    segment = segment_factory.build()
    grain = grain_models.Grain(spacing=spacing)
    for _ in range(2):
        grain.add_segment(segment)

    segment_cog = segment.get_center_of_gravity(web_distance=0.0)[0]
    forward_segment_cog = segment.length + spacing + segment_cog

    assert grain.get_center_of_gravity(web_distance=0.0)[0] == pytest.approx(
        (segment_cog + forward_segment_cog) / 2
    )
