"""
Tests for FMM (Fast Marching Method) grain segment center of gravity calculations.

Tests cover:
- 2D FMM segment CoG calculation (using StarGrainSegment)
- 3D FMM segment CoG calculation (using ConicalGrainSegment)
- Coordinate system verification (port-origin)

Note: FMM coordinate system has origin at the PORT (aft end, closest to nozzle),
with positive x pointing forward toward the bulkhead.
"""

import numpy as np
import pytest

from machwave.models.propulsion.grain.base import GrainGeometryError
from machwave.models.propulsion.grain.geometries.conical import ConicalGrainSegment
from machwave.models.propulsion.grain.geometries.star import StarGrainSegment


class TestFMM2DSegmentCenterOfGravity:
    """Test suite for 2D FMM grain segment CoG calculation using StarGrainSegment."""

    def test_star_2d_segment_cog_at_ignition(self):
        """Test CoG of a star 2D segment at ignition (web_distance=0)."""
        outer_diameter = 0.1
        length = 0.2

        segment = StarGrainSegment(
            length=length,
            outer_diameter=outer_diameter,
            number_of_points=5,
            point_length=0.035,
            point_width=0.01,
        )

        cog = segment.get_center_of_gravity(web_distance=0.0)

        # For symmetric grain, CoG should be near center (allowing some tolerance for star shape)
        assert cog.shape == (3,)
        np.testing.assert_almost_equal(cog[0], length / 2, decimal=2)
        np.testing.assert_almost_equal(cog[1], 0.0, decimal=2)
        np.testing.assert_almost_equal(cog[2], 0.0, decimal=2)

    def test_2d_segment_cog_changes_with_burn(self):
        """Test that 2D segment CoG remains relatively stable during burn."""
        segment = StarGrainSegment(
            length=0.2,
            outer_diameter=0.1,
            number_of_points=6,
            point_length=0.03,
            point_width=0.008,
        )

        web_thickness = segment.get_web_thickness()

        # Test at different burn stages
        cog_initial = segment.get_center_of_gravity(web_distance=0.0)
        cog_half = segment.get_center_of_gravity(web_distance=web_thickness * 0.5)

        # For symmetric star grain, axial CoG should remain near center
        assert abs(cog_initial[0] - 0.1) < 0.03
        assert abs(cog_half[0] - 0.1) < 0.03

    def test_2d_segment_cog_coordinate_system(self):
        """Verify that 2D FMM uses port-origin coordinate system."""
        length = 0.3
        segment = StarGrainSegment(
            length=length,
            outer_diameter=0.12,
            number_of_points=7,
            point_length=0.04,
            point_width=0.01,
        )

        cog = segment.get_center_of_gravity(web_distance=0.0)

        # First coordinate (axial) should be between 0 (aft) and length (forward)
        assert 0 < cog[0] < length


class TestFMM3DSegmentCenterOfGravity:
    """Test suite for 3D FMM grain segment CoG calculation using ConicalGrainSegment."""

    def test_conical_3d_segment_cog_at_ignition(self):
        """Test CoG of a conical 3D segment at ignition (web_distance=0)."""
        outer_diameter = 0.1
        upper_core_diameter = 0.045
        lower_core_diameter = 0.045  # Same as upper = cylindrical
        length = 0.2

        segment = ConicalGrainSegment(
            length=length,
            outer_diameter=outer_diameter,
            upper_core_diameter=upper_core_diameter,
            lower_core_diameter=lower_core_diameter,
        )

        cog = segment.get_center_of_gravity(web_distance=0.0)

        # For a cylindrical annulus, CoG should be near geometric center
        assert cog.shape == (3,)
        np.testing.assert_almost_equal(cog[0], length / 2, decimal=2)
        np.testing.assert_almost_equal(cog[1], 0.0, decimal=2)
        np.testing.assert_almost_equal(cog[2], 0.0, decimal=2)

    def test_3d_segment_cog_conical_geometry(self):
        """Test CoG of a truly conical segment (different diameters)."""
        outer_diameter = 0.1
        upper_core_diameter = 0.05  # 50mm at top (forward)
        lower_core_diameter = 0.03  # 30mm at bottom (aft, port)
        length = 0.2

        segment = ConicalGrainSegment(
            length=length,
            outer_diameter=outer_diameter,
            upper_core_diameter=upper_core_diameter,
            lower_core_diameter=lower_core_diameter,
        )

        cog = segment.get_center_of_gravity(web_distance=0.0)

        # For conical grain, CoG should shift toward larger diameter end
        # Since upper diameter is larger, CoG should be > length/2
        assert cog.shape == (3,)
        assert cog[0] > length / 2, (
            "CoG should shift toward larger diameter (forward) end"
        )

        # Radial should still be near zero for symmetric grain
        np.testing.assert_almost_equal(cog[1], 0.0, decimal=2)
        np.testing.assert_almost_equal(cog[2], 0.0, decimal=2)

    def test_3d_segment_cog_error_on_burnout(self):
        """Test that error is raised when all propellant is consumed."""
        segment = ConicalGrainSegment(
            length=0.2,
            outer_diameter=0.1,
            upper_core_diameter=0.04,
            lower_core_diameter=0.04,
        )

        web_thickness = segment.get_web_thickness()

        # At exactly web thickness, grain should be burned out
        with pytest.raises(GrainGeometryError, match="No active material"):
            segment.get_center_of_gravity(web_distance=web_thickness)

    def test_3d_segment_cog_coordinate_system(self):
        """Verify that 3D FMM uses port-origin coordinate system."""
        length = 0.25
        segment = ConicalGrainSegment(
            length=length,
            outer_diameter=0.11,
            upper_core_diameter=0.045,
            lower_core_diameter=0.045,
        )

        cog = segment.get_center_of_gravity(web_distance=0.0)

        # First coordinate (axial) should be between 0 (aft) and length (forward)
        assert 0 < cog[0] < length

    def test_3d_segment_returns_float64_array(self):
        """Verify that CoG is returned as float64 numpy array."""
        segment = ConicalGrainSegment(
            length=0.2,
            outer_diameter=0.1,
            upper_core_diameter=0.04,
            lower_core_diameter=0.04,
        )

        cog = segment.get_center_of_gravity(web_distance=0.0)

        assert isinstance(cog, np.ndarray)
        assert cog.dtype == np.float64
        assert cog.shape == (3,)


class TestFMMCoGComparison:
    """Test consistency between 2D and 3D FMM CoG calculations."""

    def test_2d_vs_3d_cog_both_near_center(self):
        """Test that 2D star and 3D cylindrical conical both give reasonable CoG near center."""
        outer_diameter = 0.1
        length = 0.2

        # Create star grain (2D FMM)
        segment_2d = StarGrainSegment(
            length=length,
            outer_diameter=outer_diameter,
            number_of_points=5,
            point_length=0.03,
            point_width=0.008,
        )

        # Create cylindrical conical grain (3D FMM with equal diameters)
        segment_3d = ConicalGrainSegment(
            length=length,
            outer_diameter=outer_diameter,
            upper_core_diameter=0.04,
            lower_core_diameter=0.04,
        )

        cog_2d = segment_2d.get_center_of_gravity(web_distance=0.0)
        cog_3d = segment_3d.get_center_of_gravity(web_distance=0.0)

        # Both should have axial CoG near center
        assert abs(cog_2d[0] - length / 2) < 0.05
        assert abs(cog_3d[0] - length / 2) < 0.05

        # Radial positions should both be near zero for symmetric grains
        np.testing.assert_almost_equal(cog_2d[1], 0.0, decimal=2)
        np.testing.assert_almost_equal(cog_2d[2], 0.0, decimal=2)
        np.testing.assert_almost_equal(cog_3d[1], 0.0, decimal=2)
        np.testing.assert_almost_equal(cog_3d[2], 0.0, decimal=2)
