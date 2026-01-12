"""
Tests for Grain.get_center_of_gravity() method.

Tests cover:
- Segments with identical densities
- Segments with variable core diameters
- Segments with different density ratios

Note: Grain coordinate system has origin at the PORT (aft end, closest to nozzle),
with positive x pointing forward toward the bulkhead.
"""

from unittest.mock import Mock

import numpy as np
import pytest

from machwave.models.propulsion.grain import Grain, GrainSegment


class TestGrainCenterOfGravity:
    """Test suite for Grain.get_center_of_gravity() method."""

    def test_single_segment_cog(self):
        """Test CoG calculation with a single segment."""
        grain = Grain()

        # Mock a single segment with local CoG at 0.5m, length=1.0m
        segment = Mock(spec=GrainSegment)
        segment.get_center_of_gravity.return_value = np.array(
            [0.5, 0.0, 0.0]
        )  # local CoG
        segment.get_volume.return_value = 1.0
        segment.density_ratio = 1.0
        segment.length = 1.0

        grain.add_segment(segment)

        cog = grain.get_center_of_gravity(web_distance=0.0)

        # For single segment, global CoG = local CoG (no offset)
        np.testing.assert_array_almost_equal(cog, np.array([0.5, 0.0, 0.0]))

    def test_two_segments_same_density_same_volume(self):
        """Test CoG with two identical segments (same density, same volume)."""
        grain = Grain()

        # Mock two segments with same density and volume
        # With port-origin: segments are positioned from aft to forward
        segment1 = Mock(spec=GrainSegment)
        segment1.get_center_of_gravity.return_value = np.array([0.1, 0.0, 0.0])
        segment1.get_volume.return_value = 1.0
        segment1.density_ratio = 1.0
        segment1.length = 0.2

        segment2 = Mock(spec=GrainSegment)
        segment2.get_center_of_gravity.return_value = np.array([0.3, 0.0, 0.0])
        segment2.get_volume.return_value = 1.0
        segment2.density_ratio = 1.0
        segment2.length = 0.6

        grain.add_segment(segment1)
        grain.add_segment(segment2)

        cog = grain.get_center_of_gravity(web_distance=0.0)

        # With port-origin, grain.total_length = 0.2 + 0.6 = 0.8
        # Segment 1 (first added) is farthest from port
        # Segment 1 aft position from port = 0.8 - 0.2 = 0.6
        # Segment 1 global CoG = 0.6 + 0.1 = 0.7
        # Segment 2 (second added) is closest to port
        # Segment 2 aft position from port = 0.6 - 0.6 = 0.0
        # Segment 2 global CoG = 0.0 + 0.3 = 0.3
        # Average: (0.7 + 0.3)/2 = 0.5
        np.testing.assert_array_almost_equal(cog, np.array([0.5, 0.0, 0.0]))

    def test_two_segments_same_density_different_volumes(self):
        """Test CoG with two segments of same density but different volumes."""
        grain = Grain()

        # Segment 1: volume = 1.0, local CoG at x=0.1
        segment1 = Mock(spec=GrainSegment)
        segment1.get_center_of_gravity.return_value = np.array([0.1, 0.0, 0.0])
        segment1.get_volume.return_value = 1.0
        segment1.density_ratio = 1.0
        segment1.length = 0.2

        # Segment 2: volume = 3.0, local CoG at x=0.3
        segment2 = Mock(spec=GrainSegment)
        segment2.get_center_of_gravity.return_value = np.array([0.3, 0.0, 0.0])
        segment2.get_volume.return_value = 3.0
        segment2.density_ratio = 1.0
        segment2.length = 0.6

        grain.add_segment(segment1)
        grain.add_segment(segment2)

        cog = grain.get_center_of_gravity(web_distance=0.0)

        # With port-origin: total_length = 0.2 + 0.6 = 0.8
        # Seg1 aft from port = 0.8 - 0.2 = 0.6, global CoG = 0.6 + 0.1 = 0.7
        # Seg2 aft from port = 0.6 - 0.6 = 0.0, global CoG = 0.0 + 0.3 = 0.3
        # Weighted: (1.0*0.7 + 3.0*0.3) / 4.0 = (0.7 + 0.9) / 4.0 = 0.4
        expected_cog = (1.0 * 0.7 + 3.0 * 0.3) / 4.0
        np.testing.assert_array_almost_equal(cog, np.array([expected_cog, 0.0, 0.0]))

    def test_two_segments_different_densities_same_volume(self):
        """Test CoG with two segments of different densities but same volume."""
        grain = Grain()

        # Segment 1: volume = 1.0, density_ratio = 1.0, local CoG at x=0.1
        segment1 = Mock(spec=GrainSegment)
        segment1.get_center_of_gravity.return_value = np.array([0.1, 0.0, 0.0])
        segment1.get_volume.return_value = 1.0
        segment1.density_ratio = 1.0
        segment1.length = 0.2

        # Segment 2: volume = 1.0, density_ratio = 0.5, local CoG at x=0.3
        segment2 = Mock(spec=GrainSegment)
        segment2.get_center_of_gravity.return_value = np.array([0.3, 0.0, 0.0])
        segment2.get_volume.return_value = 1.0
        segment2.density_ratio = 0.5
        segment2.length = 0.6

        grain.add_segment(segment1)
        grain.add_segment(segment2)

        cog = grain.get_center_of_gravity(web_distance=0.0)

        # With port-origin: total_length = 0.8
        # Seg1 aft from port = 0.8 - 0.2 = 0.6, global CoG = 0.6 + 0.1 = 0.7 (mass=1.0)
        # Seg2 aft from port = 0.0, global CoG = 0.0 + 0.3 = 0.3 (mass=0.5)
        # Weighted: (1.0*0.7 + 0.5*0.3) / 1.5 = (0.7 + 0.15) / 1.5 = 0.85/1.5 ≈ 0.5667
        expected_cog = (1.0 * 0.7 + 0.5 * 0.3) / 1.5
        np.testing.assert_array_almost_equal(cog, np.array([expected_cog, 0.0, 0.0]))

    def test_three_segments_different_densities_and_volumes(self):
        """Test CoG with three segments varying in both density and volume."""
        grain = Grain()

        # Segment 1: volume = 2.0, density_ratio = 1.0, local CoG at x=0.1
        segment1 = Mock(spec=GrainSegment)
        segment1.get_center_of_gravity.return_value = np.array([0.1, 0.0, 0.0])
        segment1.get_volume.return_value = 2.0
        segment1.density_ratio = 1.0
        segment1.length = 0.2

        # Segment 2: volume = 1.0, density_ratio = 0.8, local CoG at x=0.3
        segment2 = Mock(spec=GrainSegment)
        segment2.get_center_of_gravity.return_value = np.array([0.3, 0.0, 0.0])
        segment2.get_volume.return_value = 1.0
        segment2.density_ratio = 0.8
        segment2.length = 0.6

        # Segment 3: volume = 3.0, density_ratio = 0.6, local CoG at x=0.5
        segment3 = Mock(spec=GrainSegment)
        segment3.get_center_of_gravity.return_value = np.array([0.5, 0.0, 0.0])
        segment3.get_volume.return_value = 3.0
        segment3.density_ratio = 0.6
        segment3.length = 1.0

        grain.add_segment(segment1)
        grain.add_segment(segment2)
        grain.add_segment(segment3)

        cog = grain.get_center_of_gravity(web_distance=0.0)

        # With port-origin: total_length = 0.2 + 0.6 + 1.0 = 1.8
        # Seg1 (first added, farthest from port) aft from port = 1.8 - 0.2 = 1.6
        # Seg1 global CoG = 1.6 + 0.1 = 1.7 (mass = 2.0)
        # Seg2 aft from port = 1.6 - 0.6 = 1.0
        # Seg2 global CoG = 1.0 + 0.3 = 1.3 (mass = 0.8)
        # Seg3 (last added, closest to port) aft from port = 1.0 - 1.0 = 0.0
        # Seg3 global CoG = 0.0 + 0.5 = 0.5 (mass = 1.8)
        mass1, mass2, mass3 = 2.0, 0.8, 1.8
        total_mass = 4.6
        expected_cog_x = (mass1 * 1.7 + mass2 * 1.3 + mass3 * 0.5) / total_mass
        # = (2.0*1.7 + 0.8*1.3 + 1.8*0.5) / 4.6 = (3.4 + 1.04 + 0.9) / 4.6

        np.testing.assert_array_almost_equal(cog, np.array([expected_cog_x, 0.0, 0.0]))

    def test_cog_with_web_distance(self):
        """Test that web_distance is passed correctly to segment methods."""
        grain = Grain()

        segment = Mock(spec=GrainSegment)
        segment.get_center_of_gravity.return_value = np.array([0.5, 0.0, 0.0])
        segment.get_volume.return_value = 1.0
        segment.density_ratio = 1.0
        segment.length = 1.0

        grain.add_segment(segment)

        web_distance = 0.01
        grain.get_center_of_gravity(web_distance=web_distance)

        # Verify that web_distance was passed correctly
        segment.get_center_of_gravity.assert_called_once_with(web_distance=web_distance)

    def test_cog_with_y_and_z_offsets(self):
        """Test CoG calculation preserves y and z coordinates."""
        grain = Grain()

        # Segment 1: local CoG with y and z offsets
        segment1 = Mock(spec=GrainSegment)
        segment1.get_center_of_gravity.return_value = np.array([0.1, 0.2, 0.0])  # local
        segment1.get_volume.return_value = 1.0
        segment1.density_ratio = 1.0
        segment1.length = 0.2

        # Segment 2: local CoG with different y and z offsets
        segment2 = Mock(spec=GrainSegment)
        segment2.get_center_of_gravity.return_value = np.array(
            [0.1, 0.0, 0.08]
        )  # local
        segment2.get_volume.return_value = 1.0
        segment2.density_ratio = 1.0
        segment2.length = 0.2

        grain.add_segment(segment1)
        grain.add_segment(segment2)

        cog = grain.get_center_of_gravity(web_distance=0.0)

        # With port-origin: total_length = 0.2 + 0.2 = 0.4 (only x is offset by stacking)
        # Segment 1 (first added, farthest from port) aft from port = 0.4 - 0.2 = 0.2
        # Segment 1 global: [0.2 + 0.1, 0.2, 0.0] = [0.3, 0.2, 0.0]
        # Segment 2 (closest to port) aft from port = 0.2 - 0.2 = 0.0
        # Segment 2 global: [0.0 + 0.1, 0.0, 0.08] = [0.1, 0.0, 0.08]
        # Average: [(0.3+0.1)/2, (0.2+0.0)/2, (0.0+0.08)/2] = [0.2, 0.1, 0.04]
        expected = np.array([0.2, 0.1, 0.04])
        np.testing.assert_array_almost_equal(cog, expected)

    def test_no_segments_raises_error(self):
        """Test that ValueError is raised when grain has no segments."""
        grain = Grain()

        with pytest.raises(ValueError, match="No segments found"):
            grain.get_center_of_gravity(web_distance=0.0)

    def test_variable_core_diameters_bates_segments(self):
        """Test CoG with actual BATES segments having variable core diameters."""
        from machwave.models.propulsion.grain.geometries.bates import BatesSegment

        grain = Grain()  # 10mm spacing between segments

        # Segment 1: 45mm core diameter
        segment1 = BatesSegment(
            outer_diameter=117e-3,
            core_diameter=45e-3,
            length=200e-3,
            density_ratio=1.0,
        )

        # Segment 2: 60mm core diameter (larger core = less propellant)
        segment2 = BatesSegment(
            outer_diameter=117e-3,
            core_diameter=60e-3,
            length=200e-3,
            density_ratio=1.0,
        )

        grain.add_segment(segment1)
        grain.add_segment(segment2)

        cog = grain.get_center_of_gravity(web_distance=0.0)

        # Get individual masses to verify weighting
        vol1 = segment1.get_volume(web_distance=0.0)
        vol2 = segment2.get_volume(web_distance=0.0)

        # Segment with smaller core has more propellant (higher volume)
        assert vol1 > vol2, "45mm core should have more propellant than 60mm core"

        # Manual calculation accounting for segment positions with port-origin:
        # Segment 1 local CoG (BATES is symmetric, CoG at center)
        cog1_local = segment1.get_center_of_gravity(web_distance=0.0)  # [0.1, 0, 0]
        # Total grain length = seg1.length + spacing + seg2.length = 0.2 + 0.01 + 0.2 = 0.41
        # Segment 1 (first added) aft position from port = 0.41 - 0.2 = 0.21
        # Segment 1 global CoG = 0.21 + 0.1 = 0.31
        total_length = segment1.length + grain.spacing + segment2.length
        seg1_aft_from_port = total_length - segment1.length
        cog1_global = cog1_local.copy()
        cog1_global[0] = seg1_aft_from_port + cog1_local[0]  # [0.31, 0, 0]

        # Segment 2 local CoG
        cog2_local = segment2.get_center_of_gravity(web_distance=0.0)  # [0.1, 0, 0]
        # Segment 2 (last added, closest to port) aft position = 0.21 - 0.2 - 0.01 = 0.0
        seg2_aft_from_port = seg1_aft_from_port - segment1.length - grain.spacing
        cog2_global = cog2_local.copy()
        cog2_global[0] = seg2_aft_from_port + cog2_local[0]  # [0.1, 0, 0]

        # Mass-weighted average
        expected_cog = (cog1_global * vol1 + cog2_global * vol2) / (vol1 + vol2)

        np.testing.assert_array_almost_equal(cog, expected_cog)

    def test_variable_densities_bates_segments(self):
        """Test CoG with BATES segments having different density ratios."""
        from machwave.models.propulsion.grain.geometries.bates import BatesSegment

        grain = Grain()  # 10mm spacing between segments

        # Segment 1: full density
        segment1 = BatesSegment(
            outer_diameter=117e-3,
            core_diameter=45e-3,
            length=200e-3,
            density_ratio=1.0,
        )

        # Segment 2: 70% density (e.g., foamed propellant or different formulation)
        segment2 = BatesSegment(
            outer_diameter=117e-3,
            core_diameter=45e-3,  # Same core diameter
            length=200e-3,
            density_ratio=0.7,
        )

        grain.add_segment(segment1)
        grain.add_segment(segment2)

        cog = grain.get_center_of_gravity(web_distance=0.0)

        # Get individual properties
        vol1 = segment1.get_volume(web_distance=0.0)
        vol2 = segment2.get_volume(web_distance=0.0)
        cog1_local = segment1.get_center_of_gravity(web_distance=0.0)
        cog2_local = segment2.get_center_of_gravity(web_distance=0.0)

        # Volumes should be equal (same geometry)
        np.testing.assert_almost_equal(vol1, vol2)

        # But masses are different due to density_ratio
        mass1 = vol1 * 1.0
        mass2 = vol2 * 0.7

        # Calculate global CoGs accounting for segment positions with port-origin:
        # Total length = 0.2 + 0.01 + 0.2 = 0.41
        total_length = segment1.length + grain.spacing + segment2.length
        # Segment 1 (first added, farthest from port) aft from port = 0.41 - 0.2 = 0.21
        seg1_aft_from_port = total_length - segment1.length
        cog1_global = cog1_local.copy()
        cog1_global[0] = (
            seg1_aft_from_port + cog1_local[0]
        )  # [0.21 + 0.1, 0, 0] = [0.31, 0, 0]

        # Segment 2 (last added, closest to port) aft from port = 0.21 - 0.2 - 0.01 = 0.0
        seg2_aft_from_port = seg1_aft_from_port - segment1.length - grain.spacing
        cog2_global = cog2_local.copy()
        cog2_global[0] = (
            seg2_aft_from_port + cog2_local[0]
        )  # [0.0 + 0.1, 0, 0] = [0.1, 0, 0]

        # CoG should be closer to segment 1 (more massive)
        expected_cog = (cog1_global * mass1 + cog2_global * mass2) / (mass1 + mass2)

        np.testing.assert_array_almost_equal(cog, expected_cog)

        # Since BATES segments with same geometry have identical CoG positions,
        # we can't use distance comparison. Just verify the calculation is correct.
        assert cog.shape == (3,)
