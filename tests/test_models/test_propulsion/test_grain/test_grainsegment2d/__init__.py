import pytest

import machwave.models.grain as grain_models


def test_grain_segment_2d_geometry_validation():
    # Control group:
    _ = grain_models.GrainSegment2D(
        outer_diameter=100e-3,
        length=120e-3,
    )

    # Negative outer diameter:
    with pytest.raises(grain_models.GrainGeometryError):
        _ = grain_models.GrainSegment2D(
            outer_diameter=-100e-3,
            length=120e-3,
        )

    # Negative length:
    with pytest.raises(grain_models.GrainGeometryError):
        _ = grain_models.GrainSegment2D(
            outer_diameter=100e-3,
            length=-120e-3,
        )
