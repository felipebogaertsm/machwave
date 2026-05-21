import pytest

import machwave.models.grain as grain_models
import machwave.models.grain.geometries as grain_geometries


def test_dgrain_segment_geometry_validation():
    # Control group:
    _ = grain_geometries.DGrainSegment(
        outer_diameter=100e-3,
        slot_offset=30e-3,
        length=120e-3,
    )

    # Negative slot offset:
    with pytest.raises(grain_models.GrainGeometryError):
        _ = grain_geometries.DGrainSegment(
            outer_diameter=100e-3,
            slot_offset=-30e-3,
            length=120e-3,
        )

    # Slot offset larget than segment radius:
    with pytest.raises(grain_models.GrainGeometryError):
        _ = grain_geometries.DGrainSegment(
            outer_diameter=100e-3,
            slot_offset=55e-3,
            length=120e-3,
        )
