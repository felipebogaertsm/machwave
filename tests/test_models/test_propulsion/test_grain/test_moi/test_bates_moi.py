"""Tests for BATES grain moment of inertia calculations."""

import numpy as np
import pytest

from machwave.models.grain import Grain
from machwave.models.grain.geometries import BatesSegment


class TestBatesSegmentMomentOfInertia:
    """Test suite for single BATES segment MOI calculation."""

    def test_segment_moi_at_ignition(self):
        """Test MOI of a BATES segment at ignition (web_distance=0)."""
        outer_diameter = 0.117  # 117 mm
        core_diameter = 0.045  # 45 mm
        length = 0.2  # 200 mm
        ideal_density = 1800.0  # kg/m³

        segment = BatesSegment(
            outer_diameter=outer_diameter,
            core_diameter=core_diameter,
            length=length,
            density_ratio=1.0,
        )

        moi = segment.get_moment_of_inertia(
            web_distance=0.0, ideal_density=ideal_density
        )

        # Check tensor is 3x3
        assert moi.shape == (3, 3)

        # Check symmetry
        np.testing.assert_array_almost_equal(moi, moi.T, decimal=10)

        # For a hollow cylinder:
        # Ixx (axial) should be less than Iyy, Izz (radial)
        # because radial moments include length contribution
        assert moi[0, 0] > 0  # Ixx > 0
        assert moi[1, 1] > 0  # Iyy > 0
        assert moi[2, 2] > 0  # Izz > 0

        # For symmetric BATES, Iyy should equal Izz
        np.testing.assert_almost_equal(moi[1, 1], moi[2, 2], decimal=10)

        # Off-diagonal terms should be zero for axisymmetric grain
        assert abs(moi[0, 1]) < 1e-10
        assert abs(moi[0, 2]) < 1e-10
        assert abs(moi[1, 2]) < 1e-10

    def test_segment_moi_increases_with_length(self):
        """Test that MOI increases with segment length."""
        outer_diameter = 0.117
        core_diameter = 0.045
        ideal_density = 1800.0

        segment_short = BatesSegment(
            outer_diameter=outer_diameter,
            core_diameter=core_diameter,
            length=0.1,
            density_ratio=1.0,
        )

        segment_long = BatesSegment(
            outer_diameter=outer_diameter,
            core_diameter=core_diameter,
            length=0.3,
            density_ratio=1.0,
        )

        moi_short = segment_short.get_moment_of_inertia(
            web_distance=0.0, ideal_density=ideal_density
        )
        moi_long = segment_long.get_moment_of_inertia(
            web_distance=0.0, ideal_density=ideal_density
        )

        # Longer segment should have higher radial MOI (Iyy, Izz)
        assert moi_long[1, 1] > moi_short[1, 1]
        assert moi_long[2, 2] > moi_short[2, 2]

        # Axial MOI depends on radius, should also increase with mass
        assert moi_long[0, 0] > moi_short[0, 0]

    def test_segment_moi_decreases_with_burn(self):
        """Test that MOI decreases as propellant burns (mass decreases)."""
        segment = BatesSegment(
            outer_diameter=0.117,
            core_diameter=0.045,
            length=0.2,
            density_ratio=1.0,
        )

        ideal_density = 1800.0
        web_thickness = segment.get_web_thickness()

        moi_initial = segment.get_moment_of_inertia(
            web_distance=0.0, ideal_density=ideal_density
        )
        moi_half = segment.get_moment_of_inertia(
            web_distance=web_thickness * 0.5, ideal_density=ideal_density
        )
        moi_near_burnout = segment.get_moment_of_inertia(
            web_distance=web_thickness * 0.95, ideal_density=ideal_density
        )

        # MOI should decrease as mass burns away
        assert moi_initial[0, 0] > moi_half[0, 0] > moi_near_burnout[0, 0]
        assert moi_initial[1, 1] > moi_half[1, 1] > moi_near_burnout[1, 1]

    def test_segment_moi_scales_with_density(self):
        """Test that MOI scales linearly with density."""
        segment = BatesSegment(
            outer_diameter=0.117,
            core_diameter=0.045,
            length=0.2,
            density_ratio=1.0,
        )

        density_low = 1500.0
        density_high = 2100.0

        moi_low = segment.get_moment_of_inertia(
            web_distance=0.0, ideal_density=density_low
        )
        moi_high = segment.get_moment_of_inertia(
            web_distance=0.0, ideal_density=density_high
        )

        # MOI should scale linearly with density
        ratio = density_high / density_low
        np.testing.assert_array_almost_equal(moi_high, moi_low * ratio, decimal=6)

    def test_segment_moi_analytical_validation(self):
        """Validate MOI against analytical formulas for hollow cylinder."""
        outer_diameter = 0.1  # 100 mm
        core_diameter = 0.04  # 40 mm
        length = 0.3  # 300 mm
        ideal_density = 1800.0

        segment = BatesSegment(
            outer_diameter=outer_diameter,
            core_diameter=core_diameter,
            length=length,
            density_ratio=1.0,
        )

        moi = segment.get_moment_of_inertia(
            web_distance=0.0, ideal_density=ideal_density
        )

        # Calculate expected values
        r_outer = outer_diameter / 2
        r_inner = core_diameter / 2
        volume = segment.get_volume(web_distance=0.0)
        mass = volume * ideal_density * segment.density_ratio

        # Expected formulas for hollow cylinder
        r_sum_sq = r_inner**2 + r_outer**2
        expected_Ixx = mass * r_sum_sq / 2
        expected_Iyy = mass * (r_sum_sq / 4 + length**2 / 12)

        # Validate
        np.testing.assert_almost_equal(moi[0, 0], expected_Ixx, decimal=8)
        np.testing.assert_almost_equal(moi[1, 1], expected_Iyy, decimal=8)
        np.testing.assert_almost_equal(moi[2, 2], expected_Iyy, decimal=8)


class TestBatesGrainMomentOfInertia:
    """Test suite for multi-segment BATES grain MOI calculation."""

    def test_single_segment_grain_moi(self):
        """Test MOI for a grain with a single BATES segment."""
        grain = Grain(spacing=0.0)
        segment = BatesSegment(
            outer_diameter=0.117,
            core_diameter=0.045,
            length=0.2,
            density_ratio=1.0,
        )
        grain.add_segment(segment)

        ideal_density = 1800.0
        grain_moi = grain.get_moment_of_inertia(
            web_distance=0.0, ideal_density=ideal_density
        )
        segment_moi = segment.get_moment_of_inertia(
            web_distance=0.0, ideal_density=ideal_density
        )

        # For single segment, grain MOI should equal segment MOI
        # (both referenced to same CoG)
        np.testing.assert_array_almost_equal(grain_moi, segment_moi, decimal=6)

    def test_two_segments_equal_moi(self):
        """Test MOI for two identical BATES segments."""
        grain = Grain(spacing=0.0)
        segment1 = BatesSegment(
            outer_diameter=0.117,
            core_diameter=0.045,
            length=0.2,
            density_ratio=1.0,
        )
        segment2 = BatesSegment(
            outer_diameter=0.117,
            core_diameter=0.045,
            length=0.2,
            density_ratio=1.0,
        )

        grain.add_segment(segment1)
        grain.add_segment(segment2)

        ideal_density = 1800.0
        moi = grain.get_moment_of_inertia(web_distance=0.0, ideal_density=ideal_density)

        # Check tensor is symmetric
        np.testing.assert_array_almost_equal(moi, moi.T, decimal=10)

        # Check diagonal values are positive
        assert moi[0, 0] > 0
        assert moi[1, 1] > 0
        assert moi[2, 2] > 0

        # For symmetric configuration, Iyy ≈ Izz
        np.testing.assert_almost_equal(moi[1, 1], moi[2, 2], decimal=8)

    def test_three_segments_with_spacing(self):
        """Test MOI for three BATES segments with spacing."""
        grain = Grain(spacing=0.05)  # 50mm spacing

        for _ in range(3):
            segment = BatesSegment(
                outer_diameter=0.117,
                core_diameter=0.045,
                length=0.2,
                density_ratio=1.0,
            )
            grain.add_segment(segment)

        ideal_density = 1800.0
        moi = grain.get_moment_of_inertia(web_distance=0.0, ideal_density=ideal_density)

        # Basic validations
        assert moi.shape == (3, 3)
        np.testing.assert_array_almost_equal(moi, moi.T, decimal=10)
        assert np.all(np.diag(moi) > 0)

        # For symmetric grain, Iyy ≈ Izz
        np.testing.assert_almost_equal(moi[1, 1], moi[2, 2], decimal=6)

    def test_moi_decreases_during_burn_multisegment(self):
        """Test that total MOI decreases as multi-segment grain burns."""
        grain = Grain(spacing=0.0)

        for _ in range(2):
            segment = BatesSegment(
                outer_diameter=0.117,
                core_diameter=0.045,
                length=0.2,
                density_ratio=1.0,
            )
            grain.add_segment(segment)

        ideal_density = 1800.0
        web_thickness = grain.segments[0].get_web_thickness()

        moi_initial = grain.get_moment_of_inertia(
            web_distance=0.0, ideal_density=ideal_density
        )
        moi_half = grain.get_moment_of_inertia(
            web_distance=web_thickness * 0.5, ideal_density=ideal_density
        )

        # All diagonal elements should decrease
        assert moi_initial[0, 0] > moi_half[0, 0]
        assert moi_initial[1, 1] > moi_half[1, 1]
        assert moi_initial[2, 2] > moi_half[2, 2]

    def test_different_density_ratios(self):
        """Test MOI calculation with segments of different density ratios."""
        grain = Grain(spacing=0.0)

        segment1 = BatesSegment(
            outer_diameter=0.117,
            core_diameter=0.045,
            length=0.2,
            density_ratio=1.0,
        )

        segment2 = BatesSegment(
            outer_diameter=0.117,
            core_diameter=0.045,
            length=0.2,
            density_ratio=0.8,  # Different density ratio
        )

        grain.add_segment(segment1)
        grain.add_segment(segment2)

        ideal_density = 1800.0
        moi = grain.get_moment_of_inertia(web_distance=0.0, ideal_density=ideal_density)

        # Basic checks
        assert moi.shape == (3, 3)
        assert np.all(np.diag(moi) > 0)
        np.testing.assert_array_almost_equal(moi, moi.T, decimal=10)

    def test_parallel_axis_theorem_validation(self):
        """Validate that parallel axis theorem is correctly applied."""
        grain = Grain(spacing=0.1)

        # Create two different segments
        segment1 = BatesSegment(
            outer_diameter=0.117,
            core_diameter=0.045,
            length=0.15,
            density_ratio=1.0,
        )

        segment2 = BatesSegment(
            outer_diameter=0.117,
            core_diameter=0.045,
            length=0.25,
            density_ratio=1.0,
        )

        grain.add_segment(segment1)
        grain.add_segment(segment2)

        ideal_density = 1800.0
        grain_moi = grain.get_moment_of_inertia(
            web_distance=0.0, ideal_density=ideal_density
        )

        # MOI should account for offset of segments from grain CoG
        # The radial MOI (Iyy, Izz) should be larger than sum of individual
        # segment MOIs due to parallel axis theorem

        seg1_moi = segment1.get_moment_of_inertia(
            web_distance=0.0, ideal_density=ideal_density
        )
        seg2_moi = segment2.get_moment_of_inertia(
            web_distance=0.0, ideal_density=ideal_density
        )

        # Due to parallel axis theorem, grain MOI > simple sum
        assert grain_moi[1, 1] > (seg1_moi[1, 1] + seg2_moi[1, 1])
        assert grain_moi[2, 2] > (seg1_moi[2, 2] + seg2_moi[2, 2])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
