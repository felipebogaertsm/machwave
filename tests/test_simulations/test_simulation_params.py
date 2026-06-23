import pytest

import machwave.simulation as machwave_simulation
from machwave.simulation.base import MAX_TIME_STEP, SEA_LEVEL_PRESSURE


def _build(**overrides):
    kwargs = dict(d_t=0.001, igniter_pressure=1e6, external_pressure=1e5)
    kwargs.update(overrides)
    return machwave_simulation.InternalBallisticsSimulationParams(**kwargs)


class TestSimulationParamsValidation:
    def test_accepts_max_time_step(self):
        assert _build(d_t=MAX_TIME_STEP).d_t == MAX_TIME_STEP

    @pytest.mark.parametrize("d_t", [0.0, -0.001, MAX_TIME_STEP * 2])
    def test_time_step_out_of_range(self, d_t):
        with pytest.raises(ValueError, match="d_t"):
            _build(d_t=d_t)

    def test_accepts_sea_level_igniter_pressure(self):
        assert _build(igniter_pressure=SEA_LEVEL_PRESSURE).igniter_pressure == (
            SEA_LEVEL_PRESSURE
        )

    @pytest.mark.parametrize("igniter_pressure", [SEA_LEVEL_PRESSURE - 1.0, 0.0, -1.0])
    def test_igniter_pressure_below_sea_level(self, igniter_pressure):
        with pytest.raises(ValueError, match="igniter_pressure"):
            _build(igniter_pressure=igniter_pressure)

    @pytest.mark.parametrize("external_pressure", [-1.0, -1e5])
    def test_negative_external_pressure(self, external_pressure):
        with pytest.raises(ValueError, match="external_pressure"):
            _build(external_pressure=external_pressure)

    def test_accepts_vacuum_external_pressure(self):
        assert _build(external_pressure=0.0).external_pressure == 0.0
