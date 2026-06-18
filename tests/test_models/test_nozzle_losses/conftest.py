import pytest

import machwave.models.nozzle_losses as nozzle_losses
import machwave.models.propellants.properties as propellant_properties
import machwave.models.thrust_chamber as thrust_chamber


@pytest.fixture
def nozzle() -> thrust_chamber.Nozzle:
    return thrust_chamber.Nozzle(
        inlet_diameter=0.05,
        throat_diameter=0.02,
        divergent_angle=15.0,
        convergent_angle=30.0,
        expansion_ratio=8.0,
        c_1=0.00365,
        c_2=0.000937,
    )


@pytest.fixture
def properties() -> propellant_properties.ThermochemicalProperties:
    return propellant_properties.ThermochemicalProperties(
        k_chamber=1.2,
        k_exhaust=1.2,
        adiabatic_flame_temperature=3000.0,
        molecular_weight_chamber=0.025,
        molecular_weight_exhaust=0.025,
        i_sp_frozen=240.0,
        i_sp_shifting=250.0,
        qsi_chamber=0.3,
        qsi_exhaust=0.3,
    )


@pytest.fixture
def loss_context(nozzle, properties) -> nozzle_losses.NozzleLossEvaluationContext:
    return nozzle_losses.NozzleLossEvaluationContext(
        time=1.0,
        chamber_pressure=7e6,
        nozzle=nozzle,
        properties=properties,
        free_chamber_volume=1e-3,
    )
