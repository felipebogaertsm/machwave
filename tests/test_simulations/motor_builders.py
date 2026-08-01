"""
Shared motor + simulation-params builders for end-to-end simulation tests
and benchmarks.

These configurations mirror the example scripts under examples/ (apcp_motor,
kappa_rnakka, nero_motor, 1kn_biliquid_engine) but are duplicated here so tests
stay independent of the example layer.
"""

from __future__ import annotations

import machwave.models.grain as grain_models
import machwave.models.motors as motors_models
import machwave.models.nozzle_losses as nozzle_losses
import machwave.models.propellants as propellants
import machwave.models.propellants.formulations.solid as solid_propellants
import machwave.simulation as machwave_simulation
from tests.factories import (
    BatesSegmentFactory,
    BiliquidEngineFactory,
    BiliquidEngineThrustChamberFactory,
    BiliquidPropellantFactory,
    BipropellantInjectorFactory,
    CombustionChamberFactory,
    FinocylGrainSegmentFactory,
    FuelComponentFactory,
    NozzleFactory,
    OxidizerComponentFactory,
    SolidMotorFactory,
    SolidMotorThrustChamberFactory,
    StackedTankPressureFedFeedSystemFactory,
    TankFactory,
)


def build_apcp_motor() -> tuple[
    motors_models.SolidMotor, machwave_simulation.InternalBallisticsSimulationParams
]:
    """MIT Cherry Limeade APCP motor with five identical BATES segments."""
    grain = grain_models.Grain(spacing=0.01)
    bates_segment = BatesSegmentFactory.build(
        outer_diameter=0.085, core_diameter=0.035, length=0.150
    )
    for _ in range(5):
        grain.add_segment(bates_segment)

    thrust_chamber = SolidMotorThrustChamberFactory.build(
        nozzle=NozzleFactory.build(
            inlet_diameter=0.080,
            throat_diameter=0.022,
            divergent_angle=12,
            convergent_angle=45,
            expansion_ratio=8,
        ),
        combustion_chamber=CombustionChamberFactory.build(
            casing_inner_diameter=95.25e-3,
            casing_outer_diameter=101.6e-3,
            thermal_liner_thickness=3e-3,
            internal_length=grain.total_length + 0.01,
        ),
        dry_mass=6.0,
        center_of_gravity_coordinate=(0.35, 0.0, 0.0),
    )
    motor = SolidMotorFactory.build(
        grain=grain,
        propellant=solid_propellants.MIT_CHERRY_LIMEADE,
        thrust_chamber=thrust_chamber,
        nozzle_loss_model=nozzle_losses.presets.spp1975_solid_loss_model(
            other_losses=0.12
        ),
    )
    params = machwave_simulation.InternalBallisticsSimulationParams(
        d_t=0.01,
        igniter_pressure=1e6,
        external_pressure=1e5,
    )
    return motor, params


def build_kappa_rnakka_motor() -> tuple[
    motors_models.SolidMotor, machwave_simulation.InternalBallisticsSimulationParams
]:
    """Richard Nakka's Kappa motor (KNDX, four BATES segments)."""
    grain = grain_models.Grain(spacing=5e-3)
    bates_segment = BatesSegmentFactory.build(
        outer_diameter=55e-3, core_diameter=19e-3, length=101.6e-3
    )
    for _ in range(4):
        grain.add_segment(bates_segment)

    thrust_chamber = SolidMotorThrustChamberFactory.build(
        nozzle=NozzleFactory.build(
            inlet_diameter=40e-3,
            throat_diameter=12.8e-3,
            divergent_angle=12,
            convergent_angle=25,
            expansion_ratio=11,
        ),
        combustion_chamber=CombustionChamberFactory.build(
            casing_inner_diameter=60e-3,
            casing_outer_diameter=64e-3,
            thermal_liner_thickness=1e-3,
            internal_length=grain.total_length + 5e-3,
        ),
        center_of_gravity_coordinate=(0.035, 0.0, 0.0),
    )
    motor = SolidMotorFactory.build(
        grain=grain,
        propellant=solid_propellants.KNDX,
        thrust_chamber=thrust_chamber,
        nozzle_loss_model=nozzle_losses.presets.spp1975_solid_loss_model(
            other_losses=0.12
        ),
    )
    params = machwave_simulation.InternalBallisticsSimulationParams(
        d_t=0.001,
        igniter_pressure=1e6,
        external_pressure=1e5,
    )
    return motor, params


def build_nero_motor() -> tuple[
    motors_models.SolidMotor, machwave_simulation.InternalBallisticsSimulationParams
]:
    """Supernova Rocketry Nero motor (KNDX, four BATES segments)."""
    grain = grain_models.Grain(spacing=10e-3)
    bates_segment = BatesSegmentFactory.build(
        outer_diameter=41e-3, core_diameter=15e-3, length=67.5e-3
    )
    for _ in range(4):
        grain.add_segment(bates_segment)

    thrust_chamber = SolidMotorThrustChamberFactory.build(
        nozzle=NozzleFactory.build(
            inlet_diameter=43e-3,
            throat_diameter=9.5e-3,
            divergent_angle=12,
            convergent_angle=40,
            expansion_ratio=8,
        ),
        combustion_chamber=CombustionChamberFactory.build(
            casing_inner_diameter=44.5e-3,
            casing_outer_diameter=50.8e-3,
            thermal_liner_thickness=1e-3,
            internal_length=grain.total_length + 10e-3,
        ),
        center_of_gravity_coordinate=(0.04, 0.0, 0.0),
    )
    motor = SolidMotorFactory.build(
        grain=grain,
        propellant=solid_propellants.KNDX,
        thrust_chamber=thrust_chamber,
        nozzle_loss_model=nozzle_losses.presets.spp1975_solid_loss_model(
            other_losses=0.12
        ),
    )
    params = machwave_simulation.InternalBallisticsSimulationParams(
        d_t=0.01,
        igniter_pressure=1e6,
        external_pressure=1e5,
    )
    return motor, params


def build_finocyl_motor() -> tuple[
    motors_models.SolidMotor, machwave_simulation.InternalBallisticsSimulationParams
]:
    """Small single-segment finocyl (3D fast marching method) motor.

    Short grain so the fast marching method grid and per-step cost stay small,
    for exercising the 3D solid path (including tail-off past burnout).
    """
    grain = grain_models.Grain()
    grain.add_segment(
        FinocylGrainSegmentFactory.build(
            length=0.05,
            outer_diameter=0.05,
            core_diameter=0.02,
            number_of_fins=4,
            fin_length=0.008,
            fin_width=0.003,
        )
    )

    thrust_chamber = SolidMotorThrustChamberFactory.build(
        nozzle=NozzleFactory.build(
            inlet_diameter=0.045,
            throat_diameter=0.012,
            divergent_angle=12,
            convergent_angle=45,
            expansion_ratio=8,
        ),
        combustion_chamber=CombustionChamberFactory.build(
            casing_inner_diameter=0.052,
            casing_outer_diameter=0.06,
            thermal_liner_thickness=0.002,
            internal_length=grain.total_length + 0.01,
        ),
    )
    motor = SolidMotorFactory.build(
        grain=grain,
        propellant=solid_propellants.KNDX,
        thrust_chamber=thrust_chamber,
        nozzle_loss_model=nozzle_losses.presets.spp1975_solid_loss_model(
            other_losses=0.12
        ),
    )
    params = machwave_simulation.InternalBallisticsSimulationParams(
        d_t=0.005,
        igniter_pressure=1e6,
        external_pressure=1e5,
    )
    return motor, params


def build_1kn_biliquid_engine() -> tuple[
    motors_models.BiliquidEngine, machwave_simulation.InternalBallisticsSimulationParams
]:
    """1 kN-class N2O / Ethanol biliquid engine (HalfCat Sphinx-like)."""
    oxidizer = OxidizerComponentFactory.build(initial_temperature=300.0)
    fuel = FuelComponentFactory.build(initial_temperature=300.0)
    propellant = BiliquidPropellantFactory.build(
        components=[oxidizer, fuel],
        oxidizer_to_fuel_ratio=1.9495,
    )

    feed_system = StackedTankPressureFedFeedSystemFactory.build(
        oxidizer_tank=TankFactory.build(
            fluid_name="N2O",
            volume=3.80e-3,
            temperature=300,
            initial_fluid_mass=2.78,
        ),
        fuel_tank=TankFactory.build(
            fluid_name="ETHANOL",
            volume=2.0e-3,
            temperature=300,
            initial_fluid_mass=1.55,
        ),
        piston_loss=1e5,
        oxidizer_line_loss=2e5,
        fuel_line_loss=2e5,
    )

    thrust_chamber = BiliquidEngineThrustChamberFactory.build(
        nozzle=NozzleFactory.build(
            inlet_diameter=55e-3,
            throat_diameter=25.4e-3,
            divergent_angle=12,
            convergent_angle=45,
            expansion_ratio=4,
        ),
        injector=BipropellantInjectorFactory.build(),
        combustion_chamber=CombustionChamberFactory.build(
            casing_inner_diameter=70e-3,
            casing_outer_diameter=76e-3,
            internal_length=13e-3,
            thermal_liner_thickness=2e-3,
        ),
    )

    motor = BiliquidEngineFactory.build(
        propellant=propellant,
        feed_system=feed_system,
        thrust_chamber=thrust_chamber,
        combustion_efficiency=0.98,
        nozzle_loss_model=nozzle_losses.presets.constant_efficiency_loss_model(
            efficiency=0.88, mixture_type=propellants.MixtureType.BILIQUID
        ),
    )
    params = machwave_simulation.InternalBallisticsSimulationParams(
        d_t=1e-4,
        igniter_pressure=1e6,
        external_pressure=1e5,
    )
    return motor, params
