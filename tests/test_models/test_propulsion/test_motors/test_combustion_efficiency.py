"""Combustion efficiency lives on the motor, not the propellant."""

import pytest

import machwave.models.propellants.formulations.solid as solid_propellants

from tests.factories import (
    BiliquidEngineFactory,
    BiliquidPropellantFactory,
    SolidMotorFactory,
)


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


@pytest.mark.parametrize("value", [1e-9, 1.0])
def test_boundary_values_are_allowed(value):
    """The open-lower/closed-upper range (0, 1] accepts near-zero and unity."""
    motor = SolidMotorFactory.build(combustion_efficiency=value)
    assert motor.combustion_efficiency == value


@pytest.mark.parametrize("factory", [SolidMotorFactory, BiliquidEngineFactory])
@pytest.mark.parametrize("value", [-0.1, 0.0, 1.01, 2.0])
def test_out_of_range_efficiency_raises(factory, value):
    """Values outside (0, 1] are rejected at construction, for every motor type."""
    with pytest.raises(ValueError, match="combustion_efficiency"):
        factory.build(combustion_efficiency=value)


def test_propellant_no_longer_carries_combustion_efficiency():
    """Combustion efficiency was moved off both propellant categories."""
    assert not hasattr(solid_propellants.KNDX, "combustion_efficiency")
    assert not hasattr(BiliquidPropellantFactory.build(), "combustion_efficiency")
