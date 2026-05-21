import pytest

import machwave.models.grain as grain_models
import machwave.models.grain.geometries.bates as bates_geometry


def test_inhibited_surfaces_valid_combinations():
    """Valid grain_models.InhibitedSurfaces configurations should not raise."""
    # Default: outer_surface=True, rest False
    _ = grain_models.InhibitedSurfaces()

    # All False
    _ = grain_models.InhibitedSurfaces(
        outer_surface=False, inner_surface=False, upper_end=False, lower_end=False
    )

    # Only inner surface inhibited
    _ = grain_models.InhibitedSurfaces(inner_surface=True)

    # Both ends inhibited
    _ = grain_models.InhibitedSurfaces(upper_end=True, lower_end=True)

    # Three surfaces inhibited (still valid)
    _ = grain_models.InhibitedSurfaces(
        outer_surface=True, inner_surface=True, upper_end=True, lower_end=False
    )


def test_inhibited_surfaces_all_true_raises():
    """All four surfaces inhibited at once is invalid."""
    with pytest.raises(grain_models.GrainGeometryError):
        _ = grain_models.InhibitedSurfaces(
            outer_surface=True, inner_surface=True, upper_end=True, lower_end=True
        )


def test_inhibited_surfaces_frozen():
    """grain_models.InhibitedSurfaces should be immutable."""
    surfaces = grain_models.InhibitedSurfaces()
    with pytest.raises(AttributeError):
        surfaces.outer_surface = False  # type: ignore[misc]


def test_grain_segment_accepts_inhibited_surfaces():
    """Concrete GrainSegment should accept grain_models.InhibitedSurfaces."""
    surfaces = grain_models.InhibitedSurfaces(
        outer_surface=True, inner_surface=False, upper_end=False, lower_end=False
    )
    segment = bates_geometry.BatesSegment(
        outer_diameter=0.1,
        core_diameter=0.05,
        length=0.2,
    )
    assert segment.inhibited_surfaces == surfaces
