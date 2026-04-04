"""
Tests for Grain spacing attribute.

This test suite verifies that spacing is properly implemented as a Grain-level
attribute and not as a GrainSegment attribute.
"""

import pytest

from machwave.models.grain import Grain
from machwave.models.grain.geometries.bates import BatesSegment


class TestGrainSpacing:
    """Test suite for Grain spacing attribute."""

    def test_grain_default_spacing(self):
        """Test that Grain has default spacing of 0.0."""
        grain = Grain()
        assert grain.spacing == 0.0

    def test_grain_custom_spacing(self):
        """Test that Grain accepts custom spacing value."""
        spacing = 0.01
        grain = Grain(spacing=spacing)
        assert grain.spacing == spacing

    def test_grain_negative_spacing(self):
        """Test that Grain can have negative spacing (overlapping segments)."""
        # Negative spacing might be used for overlapping segments
        spacing = -0.005
        grain = Grain(spacing=spacing)
        assert grain.spacing == spacing

    def test_segment_no_spacing_attribute(self):
        """Test that GrainSegment does not have a spacing attribute."""
        segment = BatesSegment(
            outer_diameter=0.086,
            core_diameter=0.032,
            length=0.150,
        )
        assert not hasattr(segment, "spacing"), (
            "GrainSegment should not have spacing attribute"
        )

    def test_segment_init_rejects_spacing(self):
        """Test that passing spacing to a segment raises TypeError."""
        with pytest.raises(TypeError, match="unexpected keyword argument"):
            BatesSegment(
                outer_diameter=0.086,
                core_diameter=0.032,
                length=0.150,
                spacing=0.01,  # This should raise TypeError
            )

    def test_total_length_with_no_spacing(self):
        """Test total_length calculation with zero spacing."""
        grain = Grain(spacing=0.0)

        segment = BatesSegment(
            outer_diameter=0.086,
            core_diameter=0.032,
            length=0.150,
        )

        grain.add_segment(segment)
        grain.add_segment(segment)
        grain.add_segment(segment)

        # Total length = 3 * 0.150 = 0.450
        expected_length = 3 * 0.150
        assert grain.total_length == pytest.approx(expected_length)

    def test_total_length_with_spacing(self):
        """Test total_length calculation with positive spacing."""
        spacing = 0.01
        grain = Grain(spacing=spacing)

        segment = BatesSegment(
            outer_diameter=0.086,
            core_diameter=0.032,
            length=0.150,
        )

        grain.add_segment(segment)
        grain.add_segment(segment)
        grain.add_segment(segment)

        # Total length = 3 * 0.150 + 2 * 0.01 = 0.450 + 0.02 = 0.470
        expected_length = 3 * 0.150 + 2 * spacing
        assert grain.total_length == pytest.approx(expected_length)

    def test_total_length_single_segment_ignores_spacing(self):
        """Test that spacing is ignored for single segment."""
        spacing = 0.01
        grain = Grain(spacing=spacing)

        segment = BatesSegment(
            outer_diameter=0.086,
            core_diameter=0.032,
            length=0.150,
        )

        grain.add_segment(segment)

        # Total length = 1 * 0.150 (spacing not added for single segment)
        expected_length = 0.150
        assert grain.total_length == pytest.approx(expected_length)

    def test_total_length_with_negative_spacing(self):
        """Test total_length calculation with negative spacing (overlapping)."""
        spacing = -0.005  # 5mm overlap
        grain = Grain(spacing=spacing)

        segment = BatesSegment(
            outer_diameter=0.086,
            core_diameter=0.032,
            length=0.150,
        )

        grain.add_segment(segment)
        grain.add_segment(segment)

        # Total length = 2 * 0.150 + 1 * (-0.005) = 0.300 - 0.005 = 0.295
        expected_length = 2 * 0.150 + 1 * spacing
        assert grain.total_length == pytest.approx(expected_length)

    def test_spacing_affects_cog_calculation(self):
        """Test that spacing is properly used in center of gravity calculations."""
        from machwave.models.grain.geometries.bates import BatesSegment

        spacing = 0.01
        grain = Grain(spacing=spacing)

        segment1 = BatesSegment(
            outer_diameter=117e-3,
            core_diameter=45e-3,
            length=200e-3,
            density_ratio=1.0,
        )

        segment2 = BatesSegment(
            outer_diameter=117e-3,
            core_diameter=45e-3,
            length=200e-3,
            density_ratio=1.0,
        )

        grain.add_segment(segment1)
        grain.add_segment(segment2)

        cog = grain.get_center_of_gravity(web_distance=0.0)

        # For two identical BATES segments:
        # Segment 1 local CoG: [0.1, 0, 0]
        # Segment 2 local CoG: [0.1, 0, 0], offset by (0.2 + 0.01) = [0.31, 0, 0]
        # Average: (0.1 + 0.31) / 2 = 0.205
        expected_x = (0.1 + (0.2 + spacing + 0.1)) / 2
        assert cog[0] == pytest.approx(expected_x)

    def test_spacing_multiple_segments_different_spacing_values(self):
        """Test that changing spacing value affects different grain instances."""
        segment1 = BatesSegment(
            outer_diameter=0.086,
            core_diameter=0.032,
            length=0.150,
        )

        segment2 = BatesSegment(
            outer_diameter=0.086,
            core_diameter=0.032,
            length=0.150,
        )

        segment3 = BatesSegment(
            outer_diameter=0.086,
            core_diameter=0.032,
            length=0.150,
        )

        segment4 = BatesSegment(
            outer_diameter=0.086,
            core_diameter=0.032,
            length=0.150,
        )

        # Grain with 1mm spacing
        grain1 = Grain(spacing=0.001)
        grain1.add_segment(segment1)
        grain1.add_segment(segment2)

        # Grain with 10mm spacing
        grain2 = Grain(spacing=0.010)
        grain2.add_segment(segment3)
        grain2.add_segment(segment4)

        # Verify different total lengths
        assert grain1.total_length < grain2.total_length
        assert grain2.total_length - grain1.total_length == pytest.approx(0.009)
