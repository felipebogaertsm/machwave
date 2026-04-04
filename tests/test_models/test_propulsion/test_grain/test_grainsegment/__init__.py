import pytest

from machwave.models.grain import GrainGeometryError, GrainSegment


def test_grain_segment_geometry_validation():
    # Control group:
    _ = GrainSegment(
        inhibited_ends=0,
    )

    _ = GrainSegment(
        inhibited_ends=1,
    )

    _ = GrainSegment(
        inhibited_ends=2,
    )

    # Invalid inhibited ends:
    with pytest.raises(GrainGeometryError):
        _ = GrainSegment(
            inhibited_ends=3,
        )
