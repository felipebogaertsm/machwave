"""Combustion efficiency lives on the motor, not the propellant."""

import pytest

import machwave.models.propellants.formulations.solid as solid_propellants

from tests.factories import BiliquidEngineFactory, SolidMotorFactory


def test_solid_motor_defaults_to_0_95():
    """A solid motor built without an explicit value uses the 0.95 default."""
    motor = SolidMotorFactory.build()
    assert motor.combustion_efficiency == 0.95


def test_biliquid_engine_defaults_to_0_95():
    """A biliquid engine built without an explicit value uses the 0.95 default."""
    engine = BiliquidEngineFactory.build()
    assert engine.combustion_efficiency == 0.95


def test_solid_motor_accepts_explicit_value():
    """An explicit combustion efficiency overrides the default."""
    motor = SolidMotorFactory.build(combustion_efficiency=0.88)
    assert motor.combustion_efficiency == 0.88


def test_biliquid_engine_carries_combustion_efficiency():
    """The biliquid engine exposes combustion efficiency at the motor level."""
    engine = BiliquidEngineFactory.build(combustion_efficiency=0.97)
    assert engine.combustion_efficiency == 0.97


def test_unitary_efficiency_is_allowed():
    """An efficiency of 1.0 (ideal adiabatic limit) is a valid input."""
    motor = SolidMotorFactory.build(combustion_efficiency=1.0)
    assert motor.combustion_efficiency == 1.0


@pytest.mark.parametrize("value", [-0.1, 0.0, 1.01, 2.0])
def test_out_of_range_efficiency_raises(value):
    """Values outside (0, 1] are rejected at construction."""
    with pytest.raises(ValueError, match="combustion_efficiency"):
        SolidMotorFactory.build(combustion_efficiency=value)


def test_propellant_no_longer_carries_combustion_efficiency():
    """Combustion efficiency was moved off the propellant entirely."""
    assert not hasattr(solid_propellants.KNDX, "combustion_efficiency")
