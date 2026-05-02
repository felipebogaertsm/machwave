"""Tests for Grain.get_segment_mismatches.

Consumers that treat the grain assembly as N copies of a single identical
segment (e.g. the RocketPy SolidMotor adapter) need a way to verify that
assumption. This test suite locks in the comparison rules.
"""

import pytest

from machwave.models.grain import Grain
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

    def test_identical_bates_segments(self):
        grain = _grain(_bates(), _bates(), _bates())
        assert grain.get_segment_mismatches() == []

    def test_olympus_style_mixed_lengths_flagged(self):
        """Replicates the Olympus 4×45mm + 3×60mm BATES stack from issue #175."""
        grain = _grain(
            *[_bates(length=0.045) for _ in range(4)],
            *[_bates(length=0.060) for _ in range(3)],
        )

        mismatches = grain.get_segment_mismatches()

        assert mismatches, "Heterogeneous lengths should be flagged"
        assert all("length" in m for m in mismatches)
        # All three 60mm segments should be reported (indices 4, 5, 6).
        assert len(mismatches) == 3

    def test_differing_outer_diameter_flagged(self):
        grain = _grain(_bates(outer_diameter=0.090), _bates(outer_diameter=0.080))
        mismatches = grain.get_segment_mismatches()
        assert any("outer_diameter" in m for m in mismatches)

    def test_differing_core_diameter_flagged(self):
        grain = _grain(_bates(core_diameter=0.030), _bates(core_diameter=0.025))
        mismatches = grain.get_segment_mismatches()
        assert any("core_diameter" in m for m in mismatches)

    def test_differing_density_ratio_flagged(self):
        grain = _grain(_bates(density_ratio=1.0), _bates(density_ratio=0.95))
        mismatches = grain.get_segment_mismatches()
        assert any("density_ratio" in m for m in mismatches)

    def test_differing_segment_class_flagged(self):
        bates = _bates()
        star = StarGrainSegment(
            outer_diameter=0.090,
            length=0.100,
            number_of_points=5,
            point_length=0.020,
            point_width=0.010,
        )
        mismatches = _grain(bates, star).get_segment_mismatches()
        assert mismatches
        assert any("type=" in m for m in mismatches)

    def test_float_tolerance(self):
        """Tiny floating-point drift should not be flagged as a mismatch."""
        grain = _grain(_bates(length=0.100), _bates(length=0.100 + 1e-15))
        assert grain.get_segment_mismatches() == []

    def test_inhibited_surfaces_compared_by_value(self):
        """InhibitedSurfaces is a frozen dataclass — identical configs match."""
        bates_a = _bates()
        bates_b = _bates()
        assert bates_a.inhibited_surfaces == bates_b.inhibited_surfaces
        assert _grain(bates_a, bates_b).get_segment_mismatches() == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
