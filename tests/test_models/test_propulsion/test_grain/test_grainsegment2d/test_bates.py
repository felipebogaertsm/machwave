import numpy as np
import pytest

import machwave.models.grain as grain_models
import machwave.models.grain.geometries as grain_geometries

IDEAL_DENSITY = 1700.0


def _radially_limited_segment():
    """Long segment: the radial wall runs out before the ends meet."""
    return grain_geometries.BatesSegment(
        outer_diameter=40e-3,
        core_diameter=15e-3,
        length=120e-3,
    )


def _axially_limited_segment():
    """Short segment: the ends meet before the radial wall runs out."""
    return grain_geometries.BatesSegment(
        outer_diameter=40e-3,
        core_diameter=15e-3,
        length=10e-3,
    )


def test_bates_segment_geometry_validation():
    # Control group:
    _ = grain_geometries.BatesSegment(
        outer_diameter=100e-3,
        core_diameter=30e-3,
        length=120e-3,
    )

    # Larger core diameter than outer diameter:
    with pytest.raises(grain_models.GrainGeometryError):
        _ = grain_geometries.BatesSegment(
            outer_diameter=100e-3,
            core_diameter=300e-3,
            length=120e-3,
        )

    # Negative core diameter:
    with pytest.raises(grain_models.GrainGeometryError):
        _ = grain_geometries.BatesSegment(
            outer_diameter=100e-3,
            core_diameter=-30e-3,
            length=120e-3,
        )

    # Negative length:
    with pytest.raises(grain_models.GrainGeometryError):
        _ = grain_geometries.BatesSegment(
            outer_diameter=100e-3,
            core_diameter=30e-3,
            length=-120e-3,
        )


def test_web_thickness_is_the_radial_wall_when_it_is_exhausted_first():
    assert _radially_limited_segment().get_web_thickness() == pytest.approx(12.5e-3)


def test_web_thickness_is_the_axial_limit_when_the_ends_meet_first():
    """Both ends burn, so a 10 mm segment is consumed after 5 mm of web."""
    assert _axially_limited_segment().get_web_thickness() == pytest.approx(5e-3)


def test_length_is_clamped_at_zero_past_burnout():
    segment = _axially_limited_segment()

    assert segment.get_length(2e-3) == pytest.approx(6e-3)
    for web_distance in (5e-3, 6e-3, 12.5e-3):
        assert segment.get_length(web_distance) == 0.0


def test_volume_is_zero_at_axial_burnout():
    segment = _axially_limited_segment()

    assert segment.get_volume(0.0) > 0.0
    assert segment.get_volume(segment.get_web_thickness()) == pytest.approx(0.0)


def test_volume_mass_and_burn_area_stay_non_negative_past_burnout():
    """Axial consumption used to outrun the radial web and go negative."""
    segment = _axially_limited_segment()

    for web_distance in np.linspace(0.0, 15e-3, 61):
        assert segment.get_volume(web_distance) >= 0.0
        assert segment.get_mass(web_distance, ideal_density=IDEAL_DENSITY) >= 0.0
        assert segment.get_burn_area(web_distance) >= 0.0


def test_burn_area_is_zero_past_burnout():
    segment = _axially_limited_segment()

    assert segment.get_burn_area(segment.get_web_thickness() * 1.1) == 0.0


def test_olympus_grain_total_length_property(bates_grain_olympus):
    grain = bates_grain_olympus
    total_length = (
        sum(s.length for s in grain.segments)
        + (grain.segment_count - 1) * grain.spacing
    )

    assert grain.total_length == pytest.approx(total_length)
    # 7 segments * 200mm + 6 gaps * 10mm = 1400mm + 60mm = 1460mm
    assert grain.total_length == pytest.approx(1460e-3)


def test_olympus_grain_segment_count(bates_grain_olympus):
    assert bates_grain_olympus.segment_count == 7
    assert bates_grain_olympus.segment_count == len(bates_grain_olympus.segments)
