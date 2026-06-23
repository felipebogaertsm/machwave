"""A motor validates and defaults its nozzle loss model at construction."""

import pytest

import machwave.models.motors.base as motors_base
import machwave.models.nozzle_losses as nozzle_losses
import machwave.models.propellants as propellants
import machwave.models.propellants.formulations.solid as solid_propellants

from tests.factories import BiliquidEngineFactory, SolidMotorFactory
from tests.factories.thrust_chamber import SolidMotorThrustChamberFactory

SOLID = propellants.MixtureType.SOLID
BILIQUID = propellants.MixtureType.BILIQUID


def test_solid_motor_defaults_to_spp1975_set():
    """A solid motor built without a model gets the Solid Performance Program set."""
    motor = SolidMotorFactory.build()
    assert (
        motor.nozzle_loss_model.component_names
        == nozzle_losses.presets.spp1975_solid_loss_model().component_names
    )
    assert motor.nozzle_loss_model.mixture_type is SOLID


def test_biliquid_engine_defaults_to_constant_efficiency_set():
    """A biliquid engine built without a model gets the constant-efficiency set."""
    engine = BiliquidEngineFactory.build()
    default = nozzle_losses.presets.constant_efficiency_loss_model(
        mixture_type=BILIQUID
    )
    assert engine.nozzle_loss_model.component_names == default.component_names
    assert engine.nozzle_loss_model.mixture_type is BILIQUID


def test_solid_motor_rejects_biliquid_loss_model():
    """A biliquid loss model cannot attach to a solid motor."""
    with pytest.raises(ValueError, match="mixture type"):
        SolidMotorFactory.build(
            nozzle_loss_model=nozzle_losses.presets.no_loss_model(mixture_type=BILIQUID)
        )


def test_biliquid_engine_rejects_solid_loss_model():
    """A solid loss model cannot attach to a biliquid engine."""
    with pytest.raises(ValueError, match="mixture type"):
        BiliquidEngineFactory.build(
            nozzle_loss_model=nozzle_losses.presets.spp1975_solid_loss_model()
        )


class _BareMotor(motors_base.Motor):
    """Minimal concrete motor to reach the base-class guards directly."""

    @property
    def initial_propellant_mass(self) -> float:
        return 0.0


def test_base_motor_requires_a_loss_model():
    """The base contract rejects a missing model; subclasses must supply a default."""
    with pytest.raises(ValueError, match="nozzle_loss_model"):
        _BareMotor(
            solid_propellants.KNDX,
            SolidMotorThrustChamberFactory.build(),
            nozzle_loss_model=None,
        )
