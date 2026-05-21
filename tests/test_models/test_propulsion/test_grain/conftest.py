"""Olympus fixtures are based on the 2022 version of the motor."""

import pytest

import machwave.models.grain as grain_models

from tests.factories import BatesSegmentFactory


@pytest.fixture
def bates_segment_olympus_45():
    return BatesSegmentFactory.build(
        outer_diameter=117e-3,
        core_diameter=45e-3,
        length=200e-3,
    )


@pytest.fixture
def bates_segment_olympus_60():
    return BatesSegmentFactory.build(
        outer_diameter=117e-3,
        core_diameter=60e-3,
        length=200e-3,
    )


@pytest.fixture
def bates_grain_olympus(bates_segment_olympus_45, bates_segment_olympus_60):
    grain = grain_models.Grain(spacing=10e-3)
    for _ in range(4):
        grain.add_segment(bates_segment_olympus_45)
    for _ in range(3):
        grain.add_segment(bates_segment_olympus_60)
    return grain
