"""Tests for FMM 3D grain moment of inertia calculations."""

import numpy as np
import pytest

import machwave.models.grain as grain_models
from tests.test_models.test_propulsion.test_grain.test_moi.conftest import (
    fmm3d_geometries,
)


@fmm3d_geometries
class TestFMM3DSegmentMomentOfInertia:
    """Test suite for single 3D FMM grain segment MOI calculation (parametrized)."""

    def test_segment_moi_at_ignition(self, segment_factory, geometry_name):
        """Test MOI of a 3D segment at ignition (web_distance=0)."""
        outer_diameter = 0.1
        length = 0.02
        ideal_density = 1800.0

        segment = segment_factory(length=length, outer_diameter=outer_diameter)
        moi = segment.get_moment_of_inertia(
            web_distance=0.0, ideal_density=ideal_density
        )

        # Check tensor is 3x3
        assert moi.shape == (3, 3)

        # Check symmetry
        np.testing.assert_array_almost_equal(moi, moi.T, decimal=10)

        # All diagonal elements should be positive
        assert moi[0, 0] > 0  # Ixx > 0
        assert moi[1, 1] > 0  # Iyy > 0
        assert moi[2, 2] > 0  # Izz > 0

        # For cylindrical 3D grains, Iyy should be close to Izz
        ratio = moi[1, 1] / moi[2, 2] if moi[2, 2] > 0 else 0
        assert 0.9 < ratio < 1.1  # Within 10% for symmetric grains

    def test_segment_moi_tensor_structure(self, segment_factory, geometry_name):
        """Test that MOI tensor has expected structure."""
        segment = segment_factory(length=0.02, outer_diameter=0.1)
        ideal_density = 1800.0

        moi = segment.get_moment_of_inertia(
            web_distance=0.0, ideal_density=ideal_density
        )

        # Check it's a proper symmetric tensor
        assert moi.shape == (3, 3)
        np.testing.assert_array_almost_equal(moi, moi.T, decimal=10)

        # Diagonal elements should be positive
        assert np.all(np.diag(moi) > 0)

    def test_segment_moi_decreases_with_burn(self, segment_factory, geometry_name):
        """Test that MOI decreases as propellant burns (mass decreases)."""
        segment = segment_factory(length=0.02, outer_diameter=0.1)
        ideal_density = 1800.0
        web_thickness = segment.get_web_thickness()

        moi_initial = segment.get_moment_of_inertia(
            web_distance=0.0, ideal_density=ideal_density
        )
        moi_half = segment.get_moment_of_inertia(
            web_distance=web_thickness * 0.5, ideal_density=ideal_density
        )

        # All diagonal MOI values should decrease as mass burns away
        assert moi_initial[0, 0] > moi_half[0, 0]
        assert moi_initial[1, 1] > moi_half[1, 1]
        assert moi_initial[2, 2] > moi_half[2, 2]

    def test_segment_moi_scales_with_density(self, segment_factory, geometry_name):
        """Test that MOI scales linearly with density."""
        segment = segment_factory(length=0.02, outer_diameter=0.1)

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

    def test_segment_moi_scales_with_length(self, segment_factory, geometry_name):
        """Test that radial MOI increases with segment length."""
        outer_diameter = 0.1
        ideal_density = 1800.0

        segment_short = segment_factory(length=0.01, outer_diameter=outer_diameter)
        segment_long = segment_factory(length=0.03, outer_diameter=outer_diameter)

        moi_short = segment_short.get_moment_of_inertia(
            web_distance=0.0, ideal_density=ideal_density
        )
        moi_long = segment_long.get_moment_of_inertia(
            web_distance=0.0, ideal_density=ideal_density
        )

        # Longer segment should have higher radial MOI (Iyy, Izz)
        # because of both more mass and length^2 term
        assert moi_long[1, 1] > moi_short[1, 1]
        assert moi_long[2, 2] > moi_short[2, 2]

    def test_segment_moi_burnout_behavior(self, segment_factory, geometry_name):
        """Test MOI behavior as segment approaches burnout."""
        segment = segment_factory(length=0.02, outer_diameter=0.1)
        ideal_density = 1800.0
        web_thickness = segment.get_web_thickness()

        # Test near burnout (95% of web thickness)
        moi_near_burnout = segment.get_moment_of_inertia(
            web_distance=web_thickness * 0.95, ideal_density=ideal_density
        )

        # MOI should still be calculable (all values positive)
        assert np.all(np.diag(moi_near_burnout) > 0)
        assert not np.any(np.isnan(moi_near_burnout))

        # Values should be small (little mass remaining)
        assert moi_near_burnout[0, 0] < 0.01  # Should be very small
        assert moi_near_burnout[1, 1] < 0.01
        assert moi_near_burnout[2, 2] < 0.01


@fmm3d_geometries
class TestFMM3DGrainMultiSegmentMomentOfInertia:
    """Test MOI calculations for multi-segment 3D FMM grains (parametrized)."""

    def test_single_segment_grain_moi(self, segment_factory, geometry_name):
        """Test MOI for a grain with a single 3D segment."""
        grain = grain_models.Grain(spacing=0.0)
        segment = segment_factory(length=0.02, outer_diameter=0.1)
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

    def test_two_segments_equal_moi(self, segment_factory, geometry_name):
        """Test MOI for two identical 3D segments."""
        grain = grain_models.Grain(spacing=0.0)
        segment1 = segment_factory(length=0.02, outer_diameter=0.1)
        segment2 = segment_factory(length=0.02, outer_diameter=0.1)

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
        ratio = moi[1, 1] / moi[2, 2] if moi[2, 2] > 0 else 0
        assert 0.95 < ratio < 1.05  # Within 5% for symmetric grains

    def test_three_segments_with_spacing(self, segment_factory, geometry_name):
        """Test MOI for three 3D segments with spacing."""
        grain = grain_models.Grain(spacing=0.005)  # 5mm spacing

        for _ in range(3):
            segment = segment_factory(length=0.02, outer_diameter=0.1)
            grain.add_segment(segment)

        ideal_density = 1800.0
        moi = grain.get_moment_of_inertia(web_distance=0.0, ideal_density=ideal_density)

        # Basic validations
        assert moi.shape == (3, 3)
        np.testing.assert_array_almost_equal(moi, moi.T, decimal=10)
        assert np.all(np.diag(moi) > 0)

    def test_moi_decreases_during_burn_multisegment(
        self, segment_factory, geometry_name
    ):
        """Test that total MOI decreases as multi-segment grain burns."""
        grain = grain_models.Grain(spacing=0.0)

        for _ in range(2):
            segment = segment_factory(length=0.02, outer_diameter=0.1)
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

    def test_spacing_affects_moi(self, segment_factory, geometry_name):
        """Test that spacing increases radial MOI due to parallel axis theorem."""
        ideal_density = 1800.0

        # Grain with no spacing
        grain_no_spacing = grain_models.Grain(spacing=0.0)
        segment1 = segment_factory(length=0.02, outer_diameter=0.1)
        segment2 = segment_factory(length=0.02, outer_diameter=0.1)
        grain_no_spacing.add_segment(segment1)
        grain_no_spacing.add_segment(segment2)

        # Grain with spacing
        grain_with_spacing = grain_models.Grain(spacing=0.01)
        segment3 = segment_factory(length=0.02, outer_diameter=0.1)
        segment4 = segment_factory(length=0.02, outer_diameter=0.1)
        grain_with_spacing.add_segment(segment3)
        grain_with_spacing.add_segment(segment4)

        moi_no_spacing = grain_no_spacing.get_moment_of_inertia(
            web_distance=0.0, ideal_density=ideal_density
        )
        moi_with_spacing = grain_with_spacing.get_moment_of_inertia(
            web_distance=0.0, ideal_density=ideal_density
        )

        # Spacing increases radial MOI (Iyy, Izz) due to parallel axis theorem
        assert moi_with_spacing[1, 1] > moi_no_spacing[1, 1]
        assert moi_with_spacing[2, 2] > moi_no_spacing[2, 2]

        # Axial MOI (Ixx) should be the same (spacing doesn't affect radial distribution)
        np.testing.assert_almost_equal(
            moi_with_spacing[0, 0], moi_no_spacing[0, 0], decimal=6
        )

    def test_parallel_axis_theorem_validation(self, segment_factory, geometry_name):
        """Validate that parallel axis theorem is correctly applied in multi-segment grain."""
        grain = grain_models.Grain(spacing=0.01)

        # Create two segments
        segment1 = segment_factory(length=0.02, outer_diameter=0.1)
        segment2 = segment_factory(length=0.02, outer_diameter=0.1)

        grain.add_segment(segment1)
        grain.add_segment(segment2)

        ideal_density = 1800.0
        grain_moi = grain.get_moment_of_inertia(
            web_distance=0.0, ideal_density=ideal_density
        )

        # The grain MOI should be larger than the sum of individual segment MOIs
        # due to parallel axis theorem (segments are offset from grain CoG)
        seg1_moi = segment1.get_moment_of_inertia(
            web_distance=0.0, ideal_density=ideal_density
        )
        seg2_moi = segment2.get_moment_of_inertia(
            web_distance=0.0, ideal_density=ideal_density
        )

        # Due to parallel axis theorem, grain radial MOI > simple sum
        assert grain_moi[1, 1] > (seg1_moi[1, 1] + seg2_moi[1, 1])
        assert grain_moi[2, 2] > (seg1_moi[2, 2] + seg2_moi[2, 2])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
