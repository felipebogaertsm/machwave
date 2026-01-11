import pytest

from machwave.models.propulsion.grain import GrainGeometryError, GrainSegment2D


def test_grain_segment_2d_geometry_validation():
    # Control group:
    _ = GrainSegment2D(
        outer_diameter=100e-3,
        length=120e-3,
    )

    # Negative outer diameter:
    with pytest.raises(GrainGeometryError):
        _ = GrainSegment2D(
            outer_diameter=-100e-3,
            length=120e-3,
        )

    # Negative length:
    with pytest.raises(GrainGeometryError):
        _ = GrainSegment2D(
            outer_diameter=100e-3,
            length=-120e-3,
        )
