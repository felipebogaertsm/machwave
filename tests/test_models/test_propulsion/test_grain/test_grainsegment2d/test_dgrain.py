import pytest

from machwave.models.propulsion.grain.geometries import DGrainSegment
from machwave.models.propulsion.grain import GrainGeometryError


def test_dgrain_segment_geometry_validation():
    # Control group:
    _ = DGrainSegment(
        outer_diameter=100e-3,
        slot_offset=30e-3,
        length=120e-3,
        spacing=10e-3,
    )

    # Negative slot offset:
    with pytest.raises(GrainGeometryError):
        _ = DGrainSegment(
            outer_diameter=100e-3,
            slot_offset=-30e-3,
            length=120e-3,
            spacing=10e-3,
        )

    # Slot offset larget than segment radius:
    with pytest.raises(GrainGeometryError):
        _ = DGrainSegment(
            outer_diameter=100e-3,
            slot_offset=55e-3,
            length=120e-3,
            spacing=10e-3,
        )
