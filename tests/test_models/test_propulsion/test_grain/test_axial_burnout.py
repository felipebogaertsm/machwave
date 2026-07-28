"""Axial burnout limit and length clamp shared by every grain segment."""

import math

import pytest

import machwave.models.grain as grain_models
import machwave.models.grain.geometries as grain_geometries

LENGTH = 100e-3

STAR_PARAMS = dict(
    length=LENGTH,
    outer_diameter=50e-3,
    number_of_points=5,
    point_length=15e-3,
    point_width=8e-3,
)


def _star(**inhibition):
    return grain_geometries.StarGrainSegment(
        **STAR_PARAMS,
        inhibited_surfaces=grain_models.InhibitedSurfaces(**inhibition),
    )


def test_two_exposed_ends_halve_the_axial_limit():
    segment = _star()

    assert segment.exposed_end_count == 2
    assert segment.get_axial_web_thickness() == pytest.approx(LENGTH / 2)


def test_one_exposed_end_takes_the_full_length():
    segment = _star(upper_end=True)

    assert segment.exposed_end_count == 1
    assert segment.get_axial_web_thickness() == pytest.approx(LENGTH)


def test_inhibited_ends_never_limit_the_burn():
    segment = _star(upper_end=True, lower_end=True)

    assert segment.exposed_end_count == 0
    assert segment.get_axial_web_thickness() == math.inf
    assert segment.get_length(LENGTH) == pytest.approx(LENGTH)


def test_length_is_clamped_at_zero():
    segment = _star()

    assert segment.get_length(LENGTH / 4) == pytest.approx(LENGTH / 2)
    assert segment.get_length(LENGTH / 2) == 0.0
    assert segment.get_length(LENGTH) == 0.0
