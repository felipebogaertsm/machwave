import numpy as np

from machwave.models.grain import Grain
from machwave.models.grain.geometries import BatesSegment


class TestBatesGrainCenterOfGravity:
    """Test suite for Grain.get_center_of_gravity() method."""

    def test_single_segment_cog_position(self):
        """Test CoG with a single BATES segment of length 1.0m."""

        grain = Grain(spacing=0.1)  # Spacing doesn't matter with 1 segment

        segment = BatesSegment(
            outer_diameter=117e-3,
            core_diameter=45e-3,
            length=1.0,
            density_ratio=1.0,
        )

        grain.add_segment(segment)

        cog = grain.get_center_of_gravity(web_distance=0.0)

        expected_cog = np.array([0.5, 0.0, 0.0])
        np.testing.assert_array_almost_equal(cog, expected_cog)

    def test_two_segments_equal_length_with_spacing(self):
        """
        Test CoG with 2 BATES segments of length 1.0m each with 0.1m spacing.
        """

        grain = Grain(spacing=0.1)

        segment_1 = BatesSegment(
            outer_diameter=117e-3,
            core_diameter=45e-3,
            length=1.0,
            density_ratio=1.0,
        )

        segment_2 = BatesSegment(
            outer_diameter=117e-3,
            core_diameter=45e-3,
            length=1.0,
            density_ratio=1.0,
        )

        grain.add_segment(segment_1)
        grain.add_segment(segment_2)

        cog = grain.get_center_of_gravity(web_distance=0.0)

        expected_cog = np.array([1.05, 0.0, 0.0])
        np.testing.assert_array_almost_equal(cog, expected_cog)

    def test_three_segments_equal_length_with_spacing(self):
        """
        Test CoG with 3 BATES segments of length 1.0m each with 0.2m spacing.
        """
        grain = Grain(spacing=0.2)

        segment1 = BatesSegment(
            outer_diameter=117e-3,
            core_diameter=45e-3,
            length=1.0,
            density_ratio=1.0,
        )

        segment2 = BatesSegment(
            outer_diameter=117e-3,
            core_diameter=45e-3,
            length=1.0,
            density_ratio=1.0,
        )

        segment3 = BatesSegment(
            outer_diameter=117e-3,
            core_diameter=45e-3,
            length=1.0,
            density_ratio=1.0,
        )

        grain.add_segment(segment1)
        grain.add_segment(segment2)
        grain.add_segment(segment3)

        cog = grain.get_center_of_gravity(web_distance=0.0)

        expected_cog = np.array([1.7, 0.0, 0.0])
        np.testing.assert_array_almost_equal(cog, expected_cog)

    def test_three_segments_variable_length_with_spacing(self):
        """
        Test CoG with 3 BATES segments of different lengths with 0.2m spacing.
        """
        grain = Grain(spacing=0.2)

        # L1 = 1.0m
        segment1 = BatesSegment(
            outer_diameter=117e-3,
            core_diameter=45e-3,
            length=1.0,
            density_ratio=1.0,
        )

        # L2 = 2.0m
        segment2 = BatesSegment(
            outer_diameter=117e-3,
            core_diameter=45e-3,
            length=2.0,
            density_ratio=1.0,
        )

        # L3 = 3.0m
        segment3 = BatesSegment(
            outer_diameter=117e-3,
            core_diameter=45e-3,
            length=3.0,
            density_ratio=1.0,
        )

        grain.add_segment(segment1)
        grain.add_segment(segment2)
        grain.add_segment(segment3)

        cog = grain.get_center_of_gravity(web_distance=0.0)

        vol1 = segment1.get_volume(web_distance=0.0)
        vol2 = segment2.get_volume(web_distance=0.0)
        vol3 = segment3.get_volume(web_distance=0.0)

        cog1 = 5.9
        cog2 = 4.2
        cog3 = 1.5

        expected_cog_x = (vol1 * cog1 + vol2 * cog2 + vol3 * cog3) / (
            vol1 + vol2 + vol3
        )
        expected_cog = np.array([expected_cog_x, 0.0, 0.0])

        np.testing.assert_array_almost_equal(cog, expected_cog)

    def test_two_segments_different_cores_with_spacing(self):
        """
        Test CoG with 2 BATES segments of same length but different core
        diameters.
        """
        grain = Grain(spacing=0.1)

        # Segment 1: 45mm core diameter
        segment1 = BatesSegment(
            outer_diameter=117e-3,
            core_diameter=45e-3,
            length=1.0,
            density_ratio=1.0,
        )

        # Segment 2: 60mm core diameter (larger core = less propellant mass)
        segment2 = BatesSegment(
            outer_diameter=117e-3,
            core_diameter=60e-3,
            length=1.0,
            density_ratio=1.0,
        )

        grain.add_segment(segment1)
        grain.add_segment(segment2)

        cog = grain.get_center_of_gravity(web_distance=0.0)

        # Verify segment 1 has more mass than segment 2
        vol1 = segment1.get_volume(web_distance=0.0)
        vol2 = segment2.get_volume(web_distance=0.0)
        assert vol1 > vol2, "Smaller core should have more propellant"

        expected_cog_x = (vol1 * 1.6 + vol2 * 0.5) / (vol1 + vol2)
        expected_cog = np.array([expected_cog_x, 0.0, 0.0])

        np.testing.assert_array_almost_equal(cog, expected_cog)

        # CoG should be closer to segment 1 (more massive)
        assert cog[0] > 1.05, "CoG should be pulled toward the heavier segment"

    def test_two_segments_different_densities_with_spacing(self):
        """
        Test CoG with 2 BATES segments of same geometry but different
        densities.
        """
        grain = Grain(spacing=0.1)

        # Segment 1: full density
        segment1 = BatesSegment(
            outer_diameter=117e-3,
            core_diameter=45e-3,
            length=1.0,
            density_ratio=1.0,
        )

        # Segment 2: 70% density (e.g., foamed propellant)
        segment2 = BatesSegment(
            outer_diameter=117e-3,
            core_diameter=45e-3,
            length=1.0,
            density_ratio=0.7,
        )

        grain.add_segment(segment1)
        grain.add_segment(segment2)

        cog = grain.get_center_of_gravity(web_distance=0.0)

        # Get volumes and calculate masses
        vol1 = segment1.get_volume(web_distance=0.0)
        vol2 = segment2.get_volume(web_distance=0.0)

        # Volumes should be equal (same geometry)
        np.testing.assert_almost_equal(vol1, vol2)

        mass1 = vol1 * 1.0
        mass2 = vol2 * 0.7

        expected_cog_x = (mass1 * 1.6 + mass2 * 0.5) / (mass1 + mass2)
        expected_cog = np.array([expected_cog_x, 0.0, 0.0])

        np.testing.assert_array_almost_equal(cog, expected_cog)

        # CoG should be closer to segment 1 (more massive)
        assert cog[0] > 1.05, "CoG should be pulled toward the denser segment"

    def test_two_segments_zero_spacing(self):
        """Test CoG with 2 BATES segments with zero spacing (touching)."""
        grain = Grain(spacing=0.0)

        segment1 = BatesSegment(
            outer_diameter=117e-3,
            core_diameter=45e-3,
            length=1.0,
            density_ratio=1.0,
        )

        segment2 = BatesSegment(
            outer_diameter=117e-3,
            core_diameter=45e-3,
            length=1.0,
            density_ratio=1.0,
        )

        grain.add_segment(segment1)
        grain.add_segment(segment2)

        cog = grain.get_center_of_gravity(web_distance=0.0)

        expected_cog = np.array([1.0, 0.0, 0.0])
        np.testing.assert_array_almost_equal(cog, expected_cog)

    def test_three_segments_burn_progression_constant_cog(self):
        """
        Test that CoG remains constant during burn for 3 identical BATES segments.
        BATES grains are symmetric, so CoG should not change as they burn.
        """
        grain = Grain(spacing=0.1)

        segment1 = BatesSegment(
            outer_diameter=117e-3,
            core_diameter=45e-3,
            length=1.0,
            density_ratio=1.0,
        )

        segment2 = BatesSegment(
            outer_diameter=117e-3,
            core_diameter=45e-3,
            length=1.0,
            density_ratio=1.0,
        )

        segment3 = BatesSegment(
            outer_diameter=117e-3,
            core_diameter=45e-3,
            length=1.0,
            density_ratio=1.0,
        )

        grain.add_segment(segment1)
        grain.add_segment(segment2)
        grain.add_segment(segment3)

        # Get web thickness to test throughout burn
        web_thickness = segment1.get_web_thickness()

        # Test CoG at different burn stages
        cog_initial = grain.get_center_of_gravity(web_distance=0.0)
        cog_quarter = grain.get_center_of_gravity(web_distance=web_thickness * 0.25)
        cog_half = grain.get_center_of_gravity(web_distance=web_thickness * 0.5)
        cog_three_quarters = grain.get_center_of_gravity(
            web_distance=web_thickness * 0.75
        )

        # For symmetric BATES grains, CoG should remain constant during burn
        np.testing.assert_array_almost_equal(cog_initial, cog_quarter, decimal=5)
        np.testing.assert_array_almost_equal(cog_initial, cog_half, decimal=5)
        np.testing.assert_array_almost_equal(cog_initial, cog_three_quarters, decimal=5)

        expected_cog = np.array([1.6, 0.0, 0.0])
        np.testing.assert_array_almost_equal(cog_initial, expected_cog)

    def test_two_segments_burn_progression_different_web_thickness(self):
        """
        Test CoG shift during burn with 2 segments of different web thickness.
        When the thinner segment burns out, CoG should be at center of remaining segment.
        """
        grain = Grain(spacing=0.1)

        # Segment 1: smaller web thickness (30mm core, wt ≈ 21.75mm)
        segment1 = BatesSegment(
            outer_diameter=73.5e-3,
            core_diameter=30e-3,
            length=1.0,
            density_ratio=1.0,
        )

        # Segment 2: larger web thickness (15mm core, wt ≈ 29.25mm)
        segment2 = BatesSegment(
            outer_diameter=73.5e-3,
            core_diameter=15e-3,
            length=1.0,
            density_ratio=1.0,
        )

        grain.add_segment(segment1)
        grain.add_segment(segment2)

        # Get web thickness for each segment
        wt1 = segment1.get_web_thickness()
        wt2 = segment2.get_web_thickness()

        # Verify segment 1 has smaller web thickness
        assert wt1 < wt2, "Segment 1 should have smaller web thickness"

        # Initial CoG (both segments have propellant)
        cog_initial = grain.get_center_of_gravity(web_distance=0.0)

        # CoG when web_distance equals smaller web thickness
        # At this point, segment 1 is burned out, only segment 2 contributes
        cog_at_small_wt = grain.get_center_of_gravity(web_distance=wt1)

        # When segment 1 is burned out, CoG should be at segment 2's center (0.5m)
        expected_cog_at_burnout = np.array([0.5, 0.0, 0.0])
        np.testing.assert_array_almost_equal(
            cog_at_small_wt, expected_cog_at_burnout, decimal=4
        )

        # Initial CoG should be different (influenced by both segments)
        assert not np.allclose(cog_initial, cog_at_small_wt), (
            "CoG should shift during burn"
        )

        # Initial CoG should be between the two segment centers
        assert cog_initial[0] > 0.5, "Initial CoG should be pulled toward segment 1"
        assert cog_initial[0] < 1.6, "Initial CoG should be between segment centers"
