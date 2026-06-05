"""
End / axial burner: cross-section fully inhibited, only the ends burn.

With no burning front in the cross-section the FMM has nothing to propagate, so
the regression map is built statically. It must encode the axial web (the grain
burns along its length), not a single cell, or the grain burns out instantly.
"""

import pytest

import machwave.models.grain as grain_models
import machwave.models.grain.geometries as grain_geometries

LENGTH = 100e-3
OUTER_DIAMETER = 50e-3

STAR_PARAMS = dict(
    length=LENGTH,
    outer_diameter=OUTER_DIAMETER,
    number_of_points=5,
    point_length=15e-3,
    point_width=8e-3,
)


def _end_burner(**inhibition):
    """Star grain with inner + outer surfaces inhibited, leaving only the ends."""
    return grain_geometries.StarGrainSegment(
        **STAR_PARAMS,
        inhibited_surfaces=grain_models.InhibitedSurfaces(
            inner_surface=True, outer_surface=True, **inhibition
        ),
    )


def test_cross_section_has_no_burning_surface():
    """Both radial surfaces inhibited -> no front for the FMM."""
    assert _end_burner().has_cross_section_regression is False


def test_double_ended_web_is_half_the_length():
    """Two ends meet in the middle -> web = length / 2."""
    assert _end_burner().get_web_thickness() == pytest.approx(LENGTH / 2)


def test_single_ended_web_is_the_full_length():
    """One end must travel the whole length -> web = length."""
    assert _end_burner(upper_end=True).get_web_thickness() == pytest.approx(LENGTH)


def test_burn_area_is_constant_over_the_burn():
    """Fixed face area -> burn area holds steady (was instantaneous before)."""
    segment = _end_burner()
    web_thickness = segment.get_web_thickness()

    initial = segment.get_burn_area(0.0)
    assert initial > 0.0
    for fraction in (0.25, 0.5, 0.75):
        assert segment.get_burn_area(web_thickness * fraction) == pytest.approx(
            initial, rel=0.05
        )


def test_no_phantom_core_burning():
    """Masked bore must not be traced as a burning contour."""
    assert _end_burner().get_core_area(0.0) == pytest.approx(0.0, abs=1e-9)


def test_burn_area_scales_with_exposed_ends():
    """Two ends burn twice the face area of one."""
    double = _end_burner().get_burn_area(0.0)
    single = _end_burner(upper_end=True).get_burn_area(0.0)
    assert double == pytest.approx(2.0 * single)


def test_burn_area_is_zero_past_burnout():
    """Beyond the web the grain is gone."""
    segment = _end_burner()
    assert segment.get_burn_area(segment.get_web_thickness() * 1.1) == 0.0


def test_volume_and_burn_area_agree_on_burnout():
    """Volume hits zero at the web thickness, matching the burn area."""
    segment = _end_burner()
    web_thickness = segment.get_web_thickness()

    assert segment.get_volume(0.0) > 0.0
    assert segment.get_volume(web_thickness) == pytest.approx(0.0, abs=1e-9)
