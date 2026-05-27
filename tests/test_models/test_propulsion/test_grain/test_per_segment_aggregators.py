"""Tests for Grain per-segment aggregation methods."""

import numpy as np
import pytest

import machwave.models.grain as grain_models

from tests.factories import BatesSegmentFactory


@pytest.fixture
def mixed_grain():
    grain = grain_models.Grain(spacing=0.0)
    grain.add_segment(
        BatesSegmentFactory.build(
            outer_diameter=0.10,
            core_diameter=0.04,
            length=0.20,
            density_ratio=1.0,
        )
    )
    grain.add_segment(
        BatesSegmentFactory.build(
            outer_diameter=0.10,
            core_diameter=0.05,
            length=0.18,
            density_ratio=0.95,
        )
    )
    grain.add_segment(
        BatesSegmentFactory.build(
            outer_diameter=0.10,
            core_diameter=0.06,
            length=0.16,
            density_ratio=0.90,
        )
    )
    return grain


class TestDensityRatioPerSegment:
    def test_returns_density_ratios_in_segment_order(self, mixed_grain):
        ratios = mixed_grain.get_density_ratio_per_segment()
        assert ratios.shape == (mixed_grain.segment_count,)
        assert ratios.dtype == np.float64
        np.testing.assert_allclose(ratios, [1.0, 0.95, 0.90])


class TestBurnAreaPerSegment:
    def test_shape(self, mixed_grain):
        burn_area = mixed_grain.get_burn_area_per_segment(web_distance=0.0)
        assert burn_area.shape == (mixed_grain.segment_count,)
        assert burn_area.dtype == np.float64

    def test_matches_segment_values(self, mixed_grain):
        web = 0.005
        per_segment = mixed_grain.get_burn_area_per_segment(web_distance=web)
        expected = np.asarray([seg.get_burn_area(web) for seg in mixed_grain.segments])
        np.testing.assert_allclose(per_segment, expected)

    def test_sum_matches_aggregator(self, mixed_grain):
        web = 0.003
        total = mixed_grain.get_burn_area(web)
        per_segment_sum = float(np.sum(mixed_grain.get_burn_area_per_segment(web)))
        assert total == pytest.approx(per_segment_sum)


class TestPropellantVolumePerSegment:
    def test_shape(self, mixed_grain):
        volume = mixed_grain.get_propellant_volume_per_segment(web_distance=0.0)
        assert volume.shape == (mixed_grain.segment_count,)
        assert volume.dtype == np.float64

    def test_matches_segment_values(self, mixed_grain):
        web = 0.002
        per_segment = mixed_grain.get_propellant_volume_per_segment(web_distance=web)
        expected = np.asarray([seg.get_volume(web) for seg in mixed_grain.segments])
        np.testing.assert_allclose(per_segment, expected)

    def test_sum_matches_aggregator(self, mixed_grain):
        web = 0.004
        total = mixed_grain.get_propellant_volume(web)
        per_segment_sum = float(
            np.sum(mixed_grain.get_propellant_volume_per_segment(web))
        )
        assert total == pytest.approx(per_segment_sum)


class TestPropellantMassPerSegment:
    def test_shape(self, mixed_grain):
        mass = mixed_grain.get_propellant_mass_per_segment(
            web_distance=0.0, ideal_density=1800.0
        )
        assert mass.shape == (mixed_grain.segment_count,)
        assert mass.dtype == np.float64

    def test_applies_density_ratio_and_density(self, mixed_grain):
        web = 0.001
        ideal_density = 1750.0
        per_segment = mixed_grain.get_propellant_mass_per_segment(
            web_distance=web, ideal_density=ideal_density
        )
        expected = np.asarray(
            [
                seg.get_mass(web_distance=web, ideal_density=ideal_density)
                for seg in mixed_grain.segments
            ]
        )
        np.testing.assert_allclose(per_segment, expected)

    def test_sum_matches_aggregator(self, mixed_grain):
        web = 0.005
        ideal_density = 1800.0
        total = mixed_grain.get_propellant_mass(
            web_distance=web, ideal_density=ideal_density
        )
        per_segment_sum = float(
            np.sum(
                mixed_grain.get_propellant_mass_per_segment(
                    web_distance=web, ideal_density=ideal_density
                )
            )
        )
        assert total == pytest.approx(per_segment_sum)

    def test_rejects_non_positive_density(self, mixed_grain):
        with pytest.raises(ValueError, match="ideal_density must be > 0"):
            mixed_grain.get_propellant_mass_per_segment(
                web_distance=0.0, ideal_density=0.0
            )
