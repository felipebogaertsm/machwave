import pytest

from machwave.models.grain import GrainGeometryError, InhibitedSurfaces
from machwave.models.grain.geometries.bates import BatesSegment


def test_inhibited_surfaces_valid_combinations():
    """Valid InhibitedSurfaces configurations should not raise."""
    # Default: outer_surface=True, rest False
    _ = InhibitedSurfaces()

    # All False
    _ = InhibitedSurfaces(
        outer_surface=False, inner_surface=False, upper_end=False, lower_end=False
    )

    # Only inner surface inhibited
    _ = InhibitedSurfaces(inner_surface=True)

    # Both ends inhibited
    _ = InhibitedSurfaces(upper_end=True, lower_end=True)

    # Three surfaces inhibited (still valid)
    _ = InhibitedSurfaces(
        outer_surface=True, inner_surface=True, upper_end=True, lower_end=False
    )


def test_inhibited_surfaces_all_true_raises():
    """All four surfaces inhibited at once is invalid."""
    with pytest.raises(GrainGeometryError):
        _ = InhibitedSurfaces(
            outer_surface=True, inner_surface=True, upper_end=True, lower_end=True
        )


def test_inhibited_surfaces_frozen():
    """InhibitedSurfaces should be immutable."""
    surfaces = InhibitedSurfaces()
    with pytest.raises(AttributeError):
        surfaces.outer_surface = False  # type: ignore[misc]


def test_grain_segment_accepts_inhibited_surfaces():
    """Concrete GrainSegment should accept InhibitedSurfaces."""
    surfaces = InhibitedSurfaces(
        outer_surface=True, inner_surface=False, upper_end=False, lower_end=False
    )
    segment = BatesSegment(
        outer_diameter=0.1,
        core_diameter=0.05,
        length=0.2,
    )
    assert segment.inhibited_surfaces == surfaces
