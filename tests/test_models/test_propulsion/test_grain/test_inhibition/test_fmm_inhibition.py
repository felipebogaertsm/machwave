"""Tests that FMM face-map inhibition is applied correctly for 2D and 3D grains."""

import numpy as np
import pytest

from machwave.models.grain import InhibitedSurfaces
from machwave.models.grain.geometries import ConicalGrainSegment, StarGrainSegment

# ── shared geometry params ────────────────────────────────────────────────────

STAR_PARAMS = dict(
    length=100e-3,
    outer_diameter=50e-3,
    number_of_points=5,
    point_length=15e-3,
    point_width=8e-3,
)

CONICAL_PARAMS = dict(
    length=100e-3,
    outer_diameter=50e-3,
    upper_core_diameter=15e-3,
    lower_core_diameter=10e-3,
)


# ── helpers ───────────────────────────────────────────────────────────────────


def _burning_cells(masked_face) -> int:
    """Count unmasked zero-valued (burning) pixels in a masked array."""
    unmasked = ~np.ma.getmaskarray(masked_face)
    return int(np.sum((masked_face.data == 0) & unmasked))


def _boundary_ring_cells(masked_face) -> int:
    """
    Count pixels that sit on the outermost ring of the unmasked region.
    Used to verify that the outer surface is exposed (non-zero count) or
    inhibited (zero count outside the bore).
    """
    from scipy.ndimage import binary_erosion

    # Work on a single 2-D slice for 2-D grains or the first interior slice for 3-D
    if masked_face.ndim == 2:
        data = masked_face
    else:
        data = masked_face[masked_face.shape[0] // 2]

    inside = ~np.ma.getmaskarray(data)
    boundary = inside & ~binary_erosion(inside)
    return int(np.sum(boundary))


def _end_burning_cells(masked_face_3d, idx: int) -> int:
    """Count burning propellant cells on an end slice, excluding the bore opening.

    The bore opening is identified as the burning (0-valued) cells in the
    adjacent interior slice — this matches how the FMM code defines bore_mask.
    """
    sl = masked_face_3d[idx]
    unmasked = ~np.ma.getmaskarray(sl)

    # Bore opening = cells that are burning in the first interior slice
    interior_idx = 1 if idx == 0 else -2
    interior_sl = masked_face_3d[interior_idx]
    interior_unmasked = ~np.ma.getmaskarray(interior_sl)
    bore_at_end = (interior_sl.data == 0) & interior_unmasked

    return int(np.sum((sl.data == 0) & unmasked & ~bore_at_end))


# ── 2D: outer surface ─────────────────────────────────────────────────────────


def test_2d_outer_surface_inhibited_by_default():
    """Default config: outer surface IS inhibited → boundary ring = all propellant (1s)."""
    seg = StarGrainSegment(**STAR_PARAMS)  # outer_surface=True by default
    mf = seg.get_masked_face()

    from scipy.ndimage import binary_erosion

    inside = ~np.ma.getmaskarray(mf)
    boundary = inside & ~binary_erosion(inside)
    # No burning cell (0) should sit on the outer boundary
    assert not np.any((mf.data == 0) & boundary), (
        "Outer surface should be inhibited but has burning cells on the boundary ring."
    )


def test_2d_outer_surface_exposed():
    """OD=F → outer boundary ring must contain burning cells."""
    seg = StarGrainSegment(
        **STAR_PARAMS, inhibited_surfaces=InhibitedSurfaces(outer_surface=False)
    )
    mf = seg.get_masked_face()

    from scipy.ndimage import binary_erosion

    inside = ~np.ma.getmaskarray(mf)
    boundary = inside & ~binary_erosion(inside)
    assert np.any((mf.data == 0) & boundary), (
        "Outer surface should be exposed but has no burning cells on the boundary ring."
    )


# ── 2D: inner surface ─────────────────────────────────────────────────────────


def test_2d_inner_surface_exposed_by_default():
    """Default config: inner surface NOT inhibited → bore pixels are burning (0)."""
    seg = StarGrainSegment(**STAR_PARAMS)
    mf = seg.get_masked_face()
    assert _burning_cells(mf) > 0, "Bore should be burning by default."


def test_2d_inner_surface_inhibited():
    """ID=T → bore pixels are masked out, not burning."""
    seg = StarGrainSegment(
        **STAR_PARAMS,
        inhibited_surfaces=InhibitedSurfaces(inner_surface=True),
    )
    mf = seg.get_masked_face()
    # All unmasked region should be propellant (1), not bore
    assert _burning_cells(mf) == 0, (
        "Inner surface inhibited but bore pixels are still marked as burning."
    )


# ── 2D: OD=F + ID=T interaction ──────────────────────────────────────────────


def test_2d_outer_exposed_inner_inhibited():
    """OD=F, ID=T → outer boundary burns, bore is masked; they must not cancel each other."""
    seg = StarGrainSegment(
        **STAR_PARAMS,
        inhibited_surfaces=InhibitedSurfaces(outer_surface=False, inner_surface=True),
    )
    mf = seg.get_masked_face()

    from scipy.ndimage import binary_erosion

    inside = ~np.ma.getmaskarray(mf)
    boundary = inside & ~binary_erosion(inside)

    # Outer boundary must be burning
    assert np.any((mf.data == 0) & boundary), "OD=F: outer boundary should be burning."
    # No masked cell should appear inside the boundary (bore masked → outside mask)
    # Bore is masked, so all unmasked burning cells come from the outer ring, not the bore
    assert _burning_cells(mf) > 0, "There should be burning cells on the outer ring."


# ── 3D: end faces ─────────────────────────────────────────────────────────────


def test_3d_upper_end_exposed_by_default():
    """Default: UE=F → upper end slice has burning cells beyond the bore."""
    seg = ConicalGrainSegment(
        **CONICAL_PARAMS,
        inhibited_surfaces=InhibitedSurfaces(outer_surface=False),
    )
    mf = seg.get_masked_face()
    assert _end_burning_cells(mf, -1) > 0, "Upper end should be burning by default."


def test_3d_upper_end_inhibited():
    """UE=T → upper end slice has no burning cells beyond the bore."""
    seg = ConicalGrainSegment(
        **CONICAL_PARAMS,
        inhibited_surfaces=InhibitedSurfaces(outer_surface=False, upper_end=True),
    )
    mf = seg.get_masked_face()
    assert _end_burning_cells(mf, -1) == 0, (
        "Upper end inhibited but still has burning cells."
    )


def test_3d_lower_end_exposed_by_default():
    """Default: LE=F → lower end slice has burning cells beyond the bore."""
    seg = ConicalGrainSegment(
        **CONICAL_PARAMS,
        inhibited_surfaces=InhibitedSurfaces(outer_surface=False),
    )
    mf = seg.get_masked_face()
    assert _end_burning_cells(mf, 0) > 0, "Lower end should be burning by default."


def test_3d_lower_end_inhibited():
    """LE=T → lower end slice has no burning cells beyond the bore."""
    seg = ConicalGrainSegment(
        **CONICAL_PARAMS,
        inhibited_surfaces=InhibitedSurfaces(outer_surface=False, lower_end=True),
    )
    mf = seg.get_masked_face()
    assert _end_burning_cells(mf, 0) == 0, (
        "Lower end inhibited but still has burning cells."
    )


def test_3d_both_ends_inhibited():
    """UE=T, LE=T → neither end slice has burning cells beyond the bore."""
    seg = ConicalGrainSegment(
        **CONICAL_PARAMS,
        inhibited_surfaces=InhibitedSurfaces(
            outer_surface=False, upper_end=True, lower_end=True
        ),
    )
    mf = seg.get_masked_face()
    assert _end_burning_cells(mf, -1) == 0, "Upper end inhibited but still burning."
    assert _end_burning_cells(mf, 0) == 0, "Lower end inhibited but still burning."


# ── 3D: OD=F + end inhibition interaction ────────────────────────────────────


def test_3d_outer_exposed_upper_end_inhibited():
    """OD=F, UE=T → outer surface burns along the body; upper face does not."""
    seg = ConicalGrainSegment(
        **CONICAL_PARAMS,
        inhibited_surfaces=InhibitedSurfaces(outer_surface=False, upper_end=True),
    )
    mf = seg.get_masked_face()

    from scipy.ndimage import binary_erosion

    mid = mf.shape[0] // 2
    sl = mf[mid]
    inside = ~np.ma.getmaskarray(sl)
    boundary = inside & ~binary_erosion(inside)

    assert np.any((sl.data == 0) & boundary), (
        "OD=F: outer boundary at mid-slice should be burning."
    )
    assert _end_burning_cells(mf, -1) == 0, "UE=T: upper end should not be burning."


def test_3d_outer_exposed_lower_end_inhibited():
    """OD=F, LE=T → outer surface burns along the body; lower face does not."""
    seg = ConicalGrainSegment(
        **CONICAL_PARAMS,
        inhibited_surfaces=InhibitedSurfaces(outer_surface=False, lower_end=True),
    )
    mf = seg.get_masked_face()

    from scipy.ndimage import binary_erosion

    mid = mf.shape[0] // 2
    sl = mf[mid]
    inside = ~np.ma.getmaskarray(sl)
    boundary = inside & ~binary_erosion(inside)

    assert np.any((sl.data == 0) & boundary), (
        "OD=F: outer boundary at mid-slice should be burning."
    )
    assert _end_burning_cells(mf, 0) == 0, "LE=T: lower end should not be burning."
