"""The 3D FMM volume interpolator must reproduce the direct voxel count.

get_volume now reads a precomputed volume-vs-web interpolator instead of
counting solid voxels over the full grid on every call. These guard that the
interpolated volume matches the direct count across the burn and that the curve
stays monotonically non-increasing.
"""

import numpy as np
import pytest

from tests.factories import ConicalGrainSegmentFactory

OUTER_DIAMETER = 0.1
CORE_DIAMETER = 0.03


@pytest.fixture(scope="module")
def segment():
    return ConicalGrainSegmentFactory.build(
        length=0.3,
        outer_diameter=OUTER_DIAMETER,
        upper_core_diameter=CORE_DIAMETER,
        lower_core_diameter=CORE_DIAMETER,
    )


def _direct_voxel_volume(segment, web_distance):
    """Volume from a full-grid solid-voxel count, the pre-interpolator path."""
    regression_map = segment.get_regression_map()
    excluded = np.ma.getmaskarray(regression_map)
    solid = (
        np.ma.getdata(regression_map) > segment.normalize(web_distance)
    ) & ~excluded
    return int(np.count_nonzero(solid)) * segment.get_voxel_volume()


def test_interpolated_volume_matches_direct_count(segment):
    web_thickness = segment.get_web_thickness()
    full_volume = segment.get_volume(0.0)
    # Stop short of burnout: past ~95% web the volume is a handful of voxels, so
    # half-voxel interpolation reads as a large fraction of a tiny number.
    for web_distance in np.linspace(0.0, 0.9 * web_thickness, 25):
        interpolated = segment.get_volume(float(web_distance))
        direct = _direct_voxel_volume(segment, float(web_distance))
        assert interpolated == pytest.approx(direct, abs=0.005 * full_volume)


def test_volume_is_monotonically_non_increasing(segment):
    web_thickness = segment.get_web_thickness()
    volumes = [
        segment.get_volume(float(web_distance))
        for web_distance in np.linspace(0.0, web_thickness, 50)
    ]
    assert all(later <= earlier + 1e-12 for earlier, later in zip(volumes, volumes[1:]))
