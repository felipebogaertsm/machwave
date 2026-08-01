"""Passing already-computed volumes into the Grain mass properties.

The assembly layer used to recompute per-segment volumes several times for one
web distance: once in the center of gravity loop, once more for the mass
normalization, and again for every segment mass in the inertia tensor. Callers
that already hold the volumes can now hand them over. Results must not move,
and the redundant calls must be gone.
"""

import numpy as np
import pytest

import machwave.models.grain as grain_models
from tests.factories import BatesSegmentFactory, FinocylGrainSegmentFactory

IDEAL_DENSITY = 1750.0
WEB_DISTANCE = 0.004


@pytest.fixture
def bates_grain():
    grain = grain_models.Grain(spacing=0.01)
    for core_diameter, length, density_ratio in (
        (0.04, 0.20, 1.0),
        (0.05, 0.18, 0.95),
        (0.06, 0.16, 0.90),
    ):
        grain.add_segment(
            BatesSegmentFactory.build(
                outer_diameter=0.10,
                core_diameter=core_diameter,
                length=length,
                density_ratio=density_ratio,
            )
        )
    return grain


@pytest.fixture
def finocyl_grain():
    grain = grain_models.Grain(spacing=0.005)
    grain.add_segment(FinocylGrainSegmentFactory.build())
    grain.add_segment(FinocylGrainSegmentFactory.build(density_ratio=0.92))
    return grain


def count_volume_calls(grain, monkeypatch):
    """Count `get_volume` calls across every segment of the grain."""
    calls = []
    for segment in grain.segments:
        original = segment.get_volume

        def counting_get_volume(web_distance, _original=original):
            calls.append(web_distance)
            return _original(web_distance)

        monkeypatch.setattr(segment, "get_volume", counting_get_volume)
    return calls


class TestResultsAreUnchanged:
    def test_center_of_gravity_matches(self, bates_grain):
        volumes = bates_grain.get_propellant_volume_per_segment(WEB_DISTANCE)

        np.testing.assert_array_equal(
            bates_grain.get_center_of_gravity(WEB_DISTANCE, volume_per_segment=volumes),
            bates_grain.get_center_of_gravity(WEB_DISTANCE),
        )

    def test_moment_of_inertia_matches(self, bates_grain):
        volumes = bates_grain.get_propellant_volume_per_segment(WEB_DISTANCE)
        center_of_gravity = bates_grain.get_center_of_gravity(WEB_DISTANCE)

        np.testing.assert_array_equal(
            bates_grain.get_moment_of_inertia(
                ideal_density=IDEAL_DENSITY,
                web_distance=WEB_DISTANCE,
                volume_per_segment=volumes,
                center_of_gravity=center_of_gravity,
            ),
            bates_grain.get_moment_of_inertia(
                ideal_density=IDEAL_DENSITY, web_distance=WEB_DISTANCE
            ),
        )

    def test_fmm_center_of_gravity_matches(self, finocyl_grain):
        volumes = finocyl_grain.get_propellant_volume_per_segment(WEB_DISTANCE)

        np.testing.assert_array_equal(
            finocyl_grain.get_center_of_gravity(
                WEB_DISTANCE, volume_per_segment=volumes
            ),
            finocyl_grain.get_center_of_gravity(WEB_DISTANCE),
        )

    def test_fmm_moment_of_inertia_matches(self, finocyl_grain):
        volumes = finocyl_grain.get_propellant_volume_per_segment(WEB_DISTANCE)
        center_of_gravity = finocyl_grain.get_center_of_gravity(WEB_DISTANCE)

        np.testing.assert_array_equal(
            finocyl_grain.get_moment_of_inertia(
                ideal_density=IDEAL_DENSITY,
                web_distance=WEB_DISTANCE,
                volume_per_segment=volumes,
                center_of_gravity=center_of_gravity,
            ),
            finocyl_grain.get_moment_of_inertia(
                ideal_density=IDEAL_DENSITY, web_distance=WEB_DISTANCE
            ),
        )

    def test_segment_mass_matches(self, bates_grain):
        segment = bates_grain.segments[0]
        volume = segment.get_volume(WEB_DISTANCE)

        assert segment.get_mass(
            web_distance=WEB_DISTANCE, ideal_density=IDEAL_DENSITY, volume=volume
        ) == segment.get_mass(web_distance=WEB_DISTANCE, ideal_density=IDEAL_DENSITY)

    def test_segment_mass_still_rejects_non_positive_density(self, bates_grain):
        segment = bates_grain.segments[0]

        with pytest.raises(ValueError, match="ideal_density must be > 0"):
            segment.get_mass(web_distance=WEB_DISTANCE, ideal_density=0.0, volume=1.0)


class TestVolumeIsComputedOncePerSegment:
    def test_center_of_gravity_without_volumes(self, bates_grain, monkeypatch):
        calls = count_volume_calls(bates_grain, monkeypatch)

        bates_grain.get_center_of_gravity(WEB_DISTANCE)

        assert len(calls) == bates_grain.segment_count

    def test_center_of_gravity_with_volumes(self, bates_grain, monkeypatch):
        volumes = bates_grain.get_propellant_volume_per_segment(WEB_DISTANCE)
        calls = count_volume_calls(bates_grain, monkeypatch)

        bates_grain.get_center_of_gravity(WEB_DISTANCE, volume_per_segment=volumes)

        assert calls == []

    def test_moment_of_inertia_without_volumes(self, bates_grain, monkeypatch):
        calls = count_volume_calls(bates_grain, monkeypatch)

        bates_grain.get_moment_of_inertia(
            ideal_density=IDEAL_DENSITY, web_distance=WEB_DISTANCE
        )

        # One for the assembly layer, one inside each segment's own tensor.
        assert len(calls) == 2 * bates_grain.segment_count

    def test_moment_of_inertia_with_volumes_and_center_of_gravity(
        self, bates_grain, monkeypatch
    ):
        volumes = bates_grain.get_propellant_volume_per_segment(WEB_DISTANCE)
        center_of_gravity = bates_grain.get_center_of_gravity(
            WEB_DISTANCE, volume_per_segment=volumes
        )
        calls = count_volume_calls(bates_grain, monkeypatch)

        bates_grain.get_moment_of_inertia(
            ideal_density=IDEAL_DENSITY,
            web_distance=WEB_DISTANCE,
            volume_per_segment=volumes,
            center_of_gravity=center_of_gravity,
        )

        # Only the segments' own tensors are left computing a volume.
        assert len(calls) == bates_grain.segment_count
