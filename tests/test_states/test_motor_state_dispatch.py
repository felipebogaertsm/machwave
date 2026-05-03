"""Unit tests for MotorState dispatch.

Each concrete MotorState subclass declares ``MOTOR_MODEL = SomeMotor``.
``InternalBallisticsSimulation.get_motor_state`` walks
``MotorState.__subclasses__()`` and picks the state whose ``MOTOR_MODEL``
matches the motor at hand. These tests verify the right state class is
returned for each motor type, that simulation parameters propagate into the
state, and that an unpaired motor type raises ``TypeError``.
"""

from __future__ import annotations

import pytest

from machwave.models import grain as grain_models
from machwave.models.feed_systems.pressure_fed import (
    StackedTankPressureFedFeedSystem,
)
from machwave.models.feed_systems.tanks import Tank
from machwave.models.grain import geometries as grain_geometries
from machwave.models.motors import LiquidEngine, Motor, SolidMotor
from machwave.models.propellants import (
    BiliquidPropellant,
    ComponentRole,
    PropellantComponent,
)
from machwave.models.propellants.formulations import solid as solid_propellants
from machwave.models.thrust_chamber import (
    CombustionChamber,
    LiquidEngineThrustChamber,
    Nozzle,
    SolidMotorThrustChamber,
)
from machwave.models.thrust_chamber.injector import BipropellantInjector
from machwave.simulation import (
    InternalBallisticsSimulation,
    InternalBallisticsSimulationParams,
)
from machwave.states import LiquidEngineState, SolidMotorState


@pytest.fixture
def params() -> InternalBallisticsSimulationParams:
    return InternalBallisticsSimulationParams(
        d_t=0.01,
        igniter_pressure=1.5e6,
        external_pressure=1e5,
        other_losses=12.0,
    )


@pytest.fixture
def solid_motor() -> SolidMotor:
    grain = grain_models.Grain()
    grain.add_segment(
        grain_geometries.BatesSegment(
            outer_diameter=41e-3,
            core_diameter=15e-3,
            length=67.5e-3,
        )
    )
    nozzle = Nozzle(
        inlet_diameter=43e-3,
        throat_diameter=9.5e-3,
        divergent_angle=12,
        convergent_angle=40,
        expansion_ratio=8,
    )
    combustion_chamber = CombustionChamber(
        casing_inner_diameter=44.5e-3,
        casing_outer_diameter=50.8e-3,
        thermal_liner_thickness=1e-3,
        internal_length=grain.total_length + 10e-3,
    )
    thrust_chamber = SolidMotorThrustChamber(
        dry_mass=0.85,
        nozzle=nozzle,
        combustion_chamber=combustion_chamber,
        nozzle_exit_to_grain_port_distance=0.01,
        center_of_gravity_coordinate=(0.04, 0.0, 0.0),
    )
    return SolidMotor(
        grain=grain,
        propellant=solid_propellants.KNDX,
        thrust_chamber=thrust_chamber,
    )


@pytest.fixture
def liquid_engine() -> LiquidEngine:
    ox_tank = Tank(
        fluid_name="N2O",
        volume=0.01,
        temperature=298.0,
        initial_fluid_mass=5.0,
    )
    fuel_tank = Tank(
        fluid_name="Ethanol",
        volume=0.008,
        temperature=298.0,
        initial_fluid_mass=3.0,
    )
    feed_system = StackedTankPressureFedFeedSystem(
        fuel_tank=fuel_tank,
        oxidizer_tank=ox_tank,
        oxidizer_line_diameter=0.01,
        oxidizer_line_length=0.5,
        fuel_line_diameter=0.008,
        fuel_line_length=0.5,
    )
    nozzle = Nozzle(
        inlet_diameter=0.04,
        throat_diameter=0.015,
        divergent_angle=15,
        convergent_angle=45,
        expansion_ratio=10,
    )
    injector = BipropellantInjector(
        area_ox=1e-5,
        area_fuel=5e-6,
        discharge_coefficient_oxidizer=0.7,
        discharge_coefficient_fuel=0.7,
    )
    combustion_chamber = CombustionChamber(
        casing_inner_diameter=0.05,
        casing_outer_diameter=0.06,
        thermal_liner_thickness=2e-3,
        internal_length=0.3,
    )
    thrust_chamber = LiquidEngineThrustChamber(
        dry_mass=5.0,
        nozzle=nozzle,
        injector=injector,
        combustion_chamber=combustion_chamber,
        center_of_gravity_coordinate=(0.15, 0.0, 0.0),
    )
    oxidizer = PropellantComponent(
        name="N2O",
        role=ComponentRole.OXIDIZER,
        density=745.0,
        chemical_formula={"N": 2, "O": 1},
        enthalpy=0.0,
        initial_temperature=298.0,
    )
    fuel = PropellantComponent(
        name="Ethanol",
        role=ComponentRole.FUEL,
        density=789.0,
        chemical_formula={"C": 2, "H": 6, "O": 1},
        enthalpy=0.0,
        initial_temperature=298.0,
    )
    propellant = BiliquidPropellant(
        name="N2O/Ethanol",
        components=[oxidizer, fuel],
        combustion_efficiency=0.98,
        of_ratio=2.0,
    )
    return LiquidEngine(
        propellant=propellant,
        thrust_chamber=thrust_chamber,
        feed_system=feed_system,
        oxidizer_tank_cog=0.5,
        fuel_tank_cog=0.6,
    )


class TestSolidMotorDispatch:
    def test_returns_solid_motor_state(
        self,
        solid_motor: SolidMotor,
        params: InternalBallisticsSimulationParams,
    ) -> None:
        state = InternalBallisticsSimulation(
            motor=solid_motor, params=params
        ).get_motor_state()

        assert isinstance(state, SolidMotorState)
        assert state.motor is solid_motor

    def test_propagates_simulation_parameters(
        self,
        solid_motor: SolidMotor,
        params: InternalBallisticsSimulationParams,
    ) -> None:
        state = InternalBallisticsSimulation(
            motor=solid_motor, params=params
        ).get_motor_state()

        assert state.chamber_pressure[0] == params.igniter_pressure
        assert state.exit_pressure[0] == params.external_pressure
        assert state.other_losses == params.other_losses


class TestLiquidEngineDispatch:
    def test_returns_liquid_engine_state(
        self,
        liquid_engine: LiquidEngine,
        params: InternalBallisticsSimulationParams,
    ) -> None:
        state = InternalBallisticsSimulation(
            motor=liquid_engine, params=params
        ).get_motor_state()

        assert isinstance(state, LiquidEngineState)
        assert state.motor is liquid_engine

    def test_propagates_simulation_parameters(
        self,
        liquid_engine: LiquidEngine,
        params: InternalBallisticsSimulationParams,
    ) -> None:
        state = InternalBallisticsSimulation(
            motor=liquid_engine, params=params
        ).get_motor_state()

        assert state.chamber_pressure[0] == params.igniter_pressure
        assert state.exit_pressure[0] == params.external_pressure
        assert state.other_losses == params.other_losses


class TestUnpairedMotor:
    def test_motor_without_paired_state_raises_type_error(
        self, params: InternalBallisticsSimulationParams
    ) -> None:
        class MysteryMotor(Motor):
            def __init__(self) -> None:
                pass

            def get_launch_mass(self) -> float:
                return 0.0

            def get_dry_mass(self) -> float:
                return 0.0

            def get_center_of_gravity(self, *args, **kwargs):  # type: ignore[override]
                raise NotImplementedError

            def get_thrust_coefficient(self, *args, **kwargs) -> float:
                return 0.0

            @property
            def initial_propellant_mass(self) -> float:
                return 0.0

        sim = InternalBallisticsSimulation(motor=MysteryMotor(), params=params)
        with pytest.raises(TypeError, match="No MotorState registered"):
            sim.get_motor_state()
