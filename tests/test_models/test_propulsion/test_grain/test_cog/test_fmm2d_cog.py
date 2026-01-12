import numpy as np

from machwave.models.propulsion.grain import Grain
from tests.test_models.test_propulsion.test_grain.test_cog.conftest import (
    fmm2d_geometries,
)


@fmm2d_geometries
class TestFMM2DSegmentCoG:
    """Test suite for single 2D FMM grain segment CoG calculation (parametrized)."""

    def test_segment_cog_at_ignition(self, segment_factory, geometry_name):
        """Test CoG of a 2D segment at ignition (web_distance=0)."""
        outer_diameter = 0.1
        length = 0.2

        segment = segment_factory(length=length, outer_diameter=outer_diameter)
        cog = segment.get_center_of_gravity(web_distance=0.0)

        # For symmetric grain, CoG should be near center
        assert cog.shape == (3,)
        np.testing.assert_almost_equal(cog[0], length / 2, decimal=2)
        np.testing.assert_almost_equal(cog[1], 0.0, decimal=2)
        np.testing.assert_almost_equal(cog[2], 0.0, decimal=2)

    def test_segment_cog_during_burn(self, segment_factory, geometry_name):
        """Test that 2D segment CoG remains relatively stable during burn."""
        segment = segment_factory(length=0.2, outer_diameter=0.1)
        web_thickness = segment.get_web_thickness()

        # Test at different burn stages
        cog_initial = segment.get_center_of_gravity(web_distance=0.0)
        cog_half = segment.get_center_of_gravity(web_distance=web_thickness * 0.5)

        # For symmetric grains, axial CoG should remain near center
        assert abs(cog_initial[0] - 0.1) < 0.03
        assert abs(cog_half[0] - 0.1) < 0.03

    def test_segment_cog_coordinate_system(self, segment_factory, geometry_name):
        """Verify that 2D FMM uses port-origin coordinate system."""
        length = 0.3
        segment = segment_factory(length=length, outer_diameter=0.12)
        cog = segment.get_center_of_gravity(web_distance=0.0)

        # First coordinate (axial) should be between 0 (aft) and length (forward)
        assert 0 < cog[0] < length


@fmm2d_geometries
class TestFMM2DGrainMultiSegmentCoG:
    """Test CoG calculations for multi-segment 2D FMM grains (parametrized)."""

    def test_single_segment_cog_position(self, segment_factory, geometry_name):
        """Test CoG with a single 2D segment of length 1.0m."""
        grain = Grain(spacing=0.1)
        segment = segment_factory(length=1.0, outer_diameter=0.1)
        grain.add_segment(segment)

        cog = grain.get_center_of_gravity(web_distance=0.0)

        # Single segment: CoG should be at its center (0.5m from port)
        expected_cog = np.array([0.5, 0.0, 0.0])
        np.testing.assert_array_almost_equal(cog, expected_cog, decimal=2)

    def test_two_segments_equal_length_with_spacing(
        self, segment_factory, geometry_name
    ):
        """Test CoG with 2 2D segments of length 1.0m each with 0.1m spacing."""
        grain = Grain(spacing=0.1)

        segment1 = segment_factory(length=1.0, outer_diameter=0.1)
        segment2 = segment_factory(length=1.0, outer_diameter=0.1)

        grain.add_segment(segment1)
        grain.add_segment(segment2)

        cog = grain.get_center_of_gravity(web_distance=0.0)

        # Total length: 1.0 + 0.1 + 1.0 = 2.1m
        # Expected CoG at center: 1.05m
        expected_cog = np.array([1.05, 0.0, 0.0])
        np.testing.assert_array_almost_equal(cog, expected_cog, decimal=2)

    def test_two_segments_zero_spacing(self, segment_factory, geometry_name):
        """Test CoG with 2 2D segments with zero spacing (touching)."""
        grain = Grain(spacing=0.0)

        segment1 = segment_factory(length=1.0, outer_diameter=0.1)
        segment2 = segment_factory(length=1.0, outer_diameter=0.1)

        grain.add_segment(segment1)
        grain.add_segment(segment2)

        cog = grain.get_center_of_gravity(web_distance=0.0)

        # Total length: 2.0m, CoG at center: 1.0m
        expected_cog = np.array([1.0, 0.0, 0.0])
        np.testing.assert_array_almost_equal(cog, expected_cog, decimal=2)

    def test_three_segments_burn_progression_constant_cog(
        self, segment_factory, geometry_name
    ):
        """Test that CoG remains relatively constant during burn for 3 identical 2D segments."""
        grain = Grain(spacing=0.1)

        segment1 = segment_factory(length=1.0, outer_diameter=0.1)
        segment2 = segment_factory(length=1.0, outer_diameter=0.1)
        segment3 = segment_factory(length=1.0, outer_diameter=0.1)

        grain.add_segment(segment1)
        grain.add_segment(segment2)
        grain.add_segment(segment3)

        web_thickness = segment1.get_web_thickness()

        # Test CoG at different burn stages
        cog_initial = grain.get_center_of_gravity(web_distance=0.0)
        cog_quarter = grain.get_center_of_gravity(web_distance=web_thickness * 0.25)
        cog_half = grain.get_center_of_gravity(web_distance=web_thickness * 0.5)

        # For symmetric grains, CoG should remain relatively constant
        # Note: Asymmetric grains (e.g., D-grain) may have small radial shifts
        np.testing.assert_array_almost_equal(cog_initial, cog_quarter, decimal=1)
        np.testing.assert_array_almost_equal(cog_initial, cog_half, decimal=1)

        # Expected CoG near center: 3.2m / 2 = 1.6m
        expected_cog = np.array([1.6, 0.0, 0.0])
        np.testing.assert_array_almost_equal(cog_initial, expected_cog, decimal=2)

    def test_two_segments_different_densities(self, segment_factory, geometry_name):
        """Test CoG with 2 2D segments of same geometry but different densities."""
        grain = Grain(spacing=0.1)

        segment1 = segment_factory(length=1.0, outer_diameter=0.1, density_ratio=1.0)
        segment2 = segment_factory(length=1.0, outer_diameter=0.1, density_ratio=0.7)

        grain.add_segment(segment1)
        grain.add_segment(segment2)

        cog = grain.get_center_of_gravity(web_distance=0.0)

        vol1 = segment1.get_volume(web_distance=0.0)
        vol2 = segment2.get_volume(web_distance=0.0)

        # Volumes should be equal
        np.testing.assert_almost_equal(vol1, vol2, decimal=5)

        # CoG should be closer to segment 1 (denser)
        assert cog[0] > 1.05, "CoG should be pulled toward the denser segment"
