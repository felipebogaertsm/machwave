"""Tests for the RocketPy solid motor adapter's grain homogeneity check."""

import pytest

from machwave.adapters.rocketpy.solid_motor import _segments_are_homogeneous
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


class TestSegmentsAreHomogeneous:
    def test_empty_segments(self):
        assert _segments_are_homogeneous([]) == []

    def test_single_segment(self):
        assert _segments_are_homogeneous([_bates()]) == []

    def test_identical_bates_segments(self):
        assert _segments_are_homogeneous([_bates(), _bates(), _bates()]) == []

    def test_olympus_style_mixed_lengths_flagged(self):
        """Replicates the Olympus 4×45mm + 3×60mm BATES stack from the issue."""
        segments = [_bates(length=0.045) for _ in range(4)] + [
            _bates(length=0.060) for _ in range(3)
        ]

        mismatches = _segments_are_homogeneous(segments)

        assert mismatches, "Heterogeneous lengths should be flagged"
        assert any("length" in m for m in mismatches)
        # All three 60mm segments should be reported (indices 4, 5, 6).
        assert sum("length" in m for m in mismatches) == 3

    def test_differing_outer_diameter_flagged(self):
        segments = [_bates(outer_diameter=0.090), _bates(outer_diameter=0.080)]
        mismatches = _segments_are_homogeneous(segments)
        assert any("outer_diameter" in m for m in mismatches)

    def test_differing_core_diameter_flagged(self):
        segments = [_bates(core_diameter=0.030), _bates(core_diameter=0.025)]
        mismatches = _segments_are_homogeneous(segments)
        assert any("core_diameter" in m for m in mismatches)

    def test_differing_density_ratio_flagged(self):
        segments = [_bates(density_ratio=1.0), _bates(density_ratio=0.95)]
        mismatches = _segments_are_homogeneous(segments)
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
        mismatches = _segments_are_homogeneous([bates, star])
        assert mismatches
        assert any("type=" in m for m in mismatches)

    def test_float_tolerance(self):
        """Tiny floating-point drift should not be flagged as a mismatch."""
        segments = [
            _bates(length=0.100),
            _bates(length=0.100 + 1e-15),
        ]
        assert _segments_are_homogeneous(segments) == []

    def test_inhibited_surfaces_compared_by_value(self):
        """InhibitedSurfaces is a frozen dataclass — identical configs match."""
        bates_a = _bates()
        bates_b = _bates()
        # Both BatesSegment instances share class-level INHIBITED_SURFACES; the
        # comparison must succeed regardless of identity.
        assert bates_a.inhibited_surfaces == bates_b.inhibited_surfaces
        assert _segments_are_homogeneous([bates_a, bates_b]) == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
