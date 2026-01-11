import pytest

from machwave.models.propulsion.grain import GrainGeometryError
from machwave.models.propulsion.grain.geometries import BatesSegment


def test_bates_segment_geometry_validation():
    # Control group:
    _ = BatesSegment(
        outer_diameter=100e-3,
        core_diameter=30e-3,
        length=120e-3,
    )

    # Larger core diameter than outer diameter:
    with pytest.raises(GrainGeometryError):
        _ = BatesSegment(
            outer_diameter=100e-3,
            core_diameter=300e-3,
            length=120e-3,
        )

    # Negative core diameter:
    with pytest.raises(GrainGeometryError):
        _ = BatesSegment(
            outer_diameter=100e-3,
            core_diameter=-30e-3,
            length=120e-3,
        )

    # Negative length:
    with pytest.raises(GrainGeometryError):
        _ = BatesSegment(
            outer_diameter=100e-3,
            core_diameter=30e-3,
            length=-120e-3,
        )


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
