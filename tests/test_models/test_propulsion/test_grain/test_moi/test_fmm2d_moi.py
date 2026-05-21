"""Tests for FMM 2D grain moment of inertia calculations."""

import numpy as np
import pytest

import machwave.models.grain as grain_models
from tests.test_models.test_propulsion.test_grain.test_moi.conftest import (
    fmm2d_geometries,
)


@fmm2d_geometries
class TestFMM2DSegmentMomentOfInertia:
    """Test suite for single 2D FMM grain segment MOI calculation (parametrized)."""

    def test_segment_moi_at_ignition(self, segment_factory, geometry_name):
        """Test MOI of a 2D segment at ignition (web_distance=0)."""
        outer_diameter = 0.1
        length = 0.2
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

        # For roughly symmetric 2D grains, Iyy should be close to Izz
        # (though some geometries like D-grain may have slight asymmetry)
        ratio = moi[1, 1] / moi[2, 2] if moi[2, 2] > 0 else 0
        assert 0.5 < ratio < 2.0  # Allow for some asymmetry

    def test_segment_moi_tensor_structure(self, segment_factory, geometry_name):
        """Test that MOI tensor has expected structure."""
        segment = segment_factory(length=0.2, outer_diameter=0.1)
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
        segment = segment_factory(length=0.2, outer_diameter=0.1)
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
        segment = segment_factory(length=0.2, outer_diameter=0.1)

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

        segment_short = segment_factory(length=0.1, outer_diameter=outer_diameter)
        segment_long = segment_factory(length=0.3, outer_diameter=outer_diameter)

        moi_short = segment_short.get_moment_of_inertia(
            web_distance=0.0, ideal_density=ideal_density
        )
        moi_long = segment_long.get_moment_of_inertia(
            web_distance=0.0, ideal_density=ideal_density
        )

        # Longer segment should have higher radial MOI (Iyy, Izz)
        # because of both more mass and length^2 term in parallel axis theorem
        assert moi_long[1, 1] > moi_short[1, 1]
        assert moi_long[2, 2] > moi_short[2, 2]


@fmm2d_geometries
class TestFMM2DGrainMultiSegmentMomentOfInertia:
    """Test MOI calculations for multi-segment 2D FMM grains (parametrized)."""

    def test_single_segment_grain_moi(self, segment_factory, geometry_name):
        """Test MOI for a grain with a single 2D segment."""
        grain = grain_models.Grain(spacing=0.0)
        segment = segment_factory(length=0.2, outer_diameter=0.1)
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
        """Test MOI for two identical 2D segments."""
        grain = grain_models.Grain(spacing=0.0)
        segment1 = segment_factory(length=0.2, outer_diameter=0.1)
        segment2 = segment_factory(length=0.2, outer_diameter=0.1)

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

        # For roughly symmetric configuration, Iyy ≈ Izz
        ratio = moi[1, 1] / moi[2, 2] if moi[2, 2] > 0 else 0
        assert 0.8 < ratio < 1.2  # Within 20% for symmetric grains

    def test_three_segments_with_spacing(self, segment_factory, geometry_name):
        """Test MOI for three 2D segments with spacing."""
        grain = grain_models.Grain(spacing=0.05)  # 50mm spacing

        for _ in range(3):
            segment = segment_factory(length=0.2, outer_diameter=0.1)
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
            segment = segment_factory(length=0.2, outer_diameter=0.1)
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
        segment1 = segment_factory(length=0.2, outer_diameter=0.1)
        segment2 = segment_factory(length=0.2, outer_diameter=0.1)
        grain_no_spacing.add_segment(segment1)
        grain_no_spacing.add_segment(segment2)

        # Grain with spacing
        grain_with_spacing = grain_models.Grain(spacing=0.1)
        segment3 = segment_factory(length=0.2, outer_diameter=0.1)
        segment4 = segment_factory(length=0.2, outer_diameter=0.1)
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
