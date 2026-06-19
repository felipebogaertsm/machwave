import pytest

import machwave.models.propellants.properties as propellant_properties
import machwave.models.thrust_chamber as thrust_chamber
import machwave.simulation.solid.states as solid_states


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
def timestep_conditions(nozzle, properties) -> solid_states.SolidTimestepConditions:
    return solid_states.SolidTimestepConditions(
        time=1.0,
        chamber_pressure=7e6,
        external_pressure=1e5,
        exit_pressure=1.2e5,
        effective_expansion_ratio=8.0,
        free_chamber_volume=1e-3,
        propellant_mass=2.0,
        propellant_mass_flow_rate=1.5,
        nozzle=nozzle,
        propellant_properties=properties,
        burn_area=0.05,
        burn_rate=0.006,
        propellant_volume=8e-4,
        web_distance=0.01,
        free_chamber_volume_rate=3e-4,
    )
