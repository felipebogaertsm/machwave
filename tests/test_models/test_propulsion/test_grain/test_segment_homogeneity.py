"""Tests for Grain.get_segment_mismatches."""

import pytest

from machwave.models.grain import Grain
from machwave.models.grain.base import InhibitedSurfaces
from machwave.models.grain.geometries import BatesSegment, StarGrainSegment


def _bates(
    *,
    outer_diameter: float = 0.090,
    core_diameter: float = 0.030,
    length: float = 0.100,
    density_ratio: float = 1.0,
) -> BatesSegment:
    return BatesSegment(
        outer_diameter=outer_diameter,
        core_diameter=core_diameter,
        length=length,
        density_ratio=density_ratio,
    )


def _star(
    *,
    outer_diameter: float = 0.090,
    length: float = 0.100,
    number_of_points: int = 5,
    point_length: float = 0.020,
    point_width: float = 0.010,
    inhibited_surfaces: InhibitedSurfaces | None = None,
    density_ratio: float = 1.0,
) -> StarGrainSegment:
    return StarGrainSegment(
        outer_diameter=outer_diameter,
        length=length,
        number_of_points=number_of_points,
        point_length=point_length,
        point_width=point_width,
        inhibited_surfaces=inhibited_surfaces,
        density_ratio=density_ratio,
    )


def _grain(*segments) -> Grain:
    grain = Grain()
    for segment in segments:
        grain.add_segment(segment)
    return grain


class TestGrainGetSegmentMismatches:
    def test_empty_grain(self):
        assert Grain().get_segment_mismatches() == []

    def test_single_segment(self):
        assert _grain(_bates()).get_segment_mismatches() == []

    def test_identical_segments(self):
        assert _grain(_bates(), _bates(), _bates()).get_segment_mismatches() == []

    def test_differing_concrete_class_flagged(self):
        mismatches = _grain(_bates(), _star()).get_segment_mismatches()

        assert len(mismatches) == 1
        assert "type=" in mismatches[0]

    def test_differing_float_attribute_flagged(self):
        mismatches = _grain(
            _bates(length=0.100), _bates(length=0.110)
        ).get_segment_mismatches()

        assert len(mismatches) == 1
        assert "length" in mismatches[0]

    def test_differing_inhibited_surfaces_flagged(self):
        # InhibitedSurfaces is a frozen dataclass compared by value through
        # the non-float equality branch.
        mismatches = _grain(
            _star(),
            _star(inhibited_surfaces=InhibitedSurfaces(outer_surface=False)),
        ).get_segment_mismatches()

        assert len(mismatches) == 1
        assert "inhibited_surfaces" in mismatches[0]

    def test_sub_ulp_float_drift_does_not_flag(self):
        assert (
            _grain(
                _bates(length=0.100), _bates(length=0.100 + 1e-15)
            ).get_segment_mismatches()
            == []
        )

    def test_every_divergent_segment_is_reported(self):
        # Olympus-style stack: 4×45 mm + 3×60 mm BATES — every 60 mm segment
        # must be named, not just the first.
        grain = _grain(
            *[_bates(length=0.045) for _ in range(4)],
            *[_bates(length=0.060) for _ in range(3)],
        )

        mismatches = grain.get_segment_mismatches()

        assert len(mismatches) == 3
        for divergent_index in (4, 5, 6):
            assert any(f"segment[{divergent_index}]" in m for m in mismatches)

    def test_every_divergent_attribute_on_a_segment_is_reported(self):
        mismatches = _grain(
            _bates(length=0.100, density_ratio=1.00),
            _bates(length=0.110, density_ratio=0.95),
        ).get_segment_mismatches()

        assert len(mismatches) == 2
        assert any("length" in m for m in mismatches)
        assert any("density_ratio" in m for m in mismatches)

    def test_lazy_fmm_cache_state_does_not_trigger_mismatch(self):
        # FMM segments populate non-constructor attributes (regression_map,
        # masked_face, …) on first burn-area query. Those caches must not
        # leak into the comparison.
        star_a = _star()
        star_b = _star()
        star_a.get_burn_area(0.001)

        assert _grain(star_a, star_b).get_segment_mismatches() == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
