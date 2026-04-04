import pytest

from machwave.models.grain import GrainGeometryError
from machwave.models.grain.geometries import DGrainSegment


def test_dgrain_segment_geometry_validation():
    # Control group:
    _ = DGrainSegment(
        outer_diameter=100e-3,
        slot_offset=30e-3,
        length=120e-3,
    )

    # Negative slot offset:
    with pytest.raises(GrainGeometryError):
        _ = DGrainSegment(
            outer_diameter=100e-3,
            slot_offset=-30e-3,
            length=120e-3,
        )

    # Slot offset larget than segment radius:
    with pytest.raises(GrainGeometryError):
        _ = DGrainSegment(
            outer_diameter=100e-3,
            slot_offset=55e-3,
            length=120e-3,
        )
