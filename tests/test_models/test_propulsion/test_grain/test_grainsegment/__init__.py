import pytest

from machwave.models.propulsion.grain import GrainGeometryError
from machwave.models.propulsion.grain import GrainSegment


def test_grain_segment_geometry_validation():
    # Control group:
    _ = GrainSegment(
        spacing=10e-3,
        inhibited_ends=0,
    )

    _ = GrainSegment(
        spacing=10e-3,
        inhibited_ends=1,
    )

    _ = GrainSegment(
        spacing=10e-3,
        inhibited_ends=2,
    )

    # Invalid inhibited ends:
    with pytest.raises(GrainGeometryError):
        _ = GrainSegment(
            spacing=10e-3,
            inhibited_ends=3,
        )

    # Negative spacing:
    with pytest.raises(GrainGeometryError):
        _ = GrainSegment(
            spacing=-10e-3,
            inhibited_ends=0,
        )
