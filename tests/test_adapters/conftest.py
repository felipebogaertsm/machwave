"""Shared motor builders for the RocketPy adapter tests."""

import machwave.common.mass_properties as mass_properties
import machwave.models.grain as grain_models
import machwave.models.motors as motors_models
import machwave.models.propellants.formulations.solid as solid_propellants
import machwave.models.thrust_chamber as thrust_chamber_models
import machwave.simulation as machwave_simulation
from tests.test_simulations.conftest import run_simulation


def bates_segment(core_diameter: float = 0.035) -> grain_models.GrainSegment:
    return grain_models.geometries.BatesSegment(
        outer_diameter=0.085,
        core_diameter=core_diameter,
        length=0.150,
    )


def star_segment() -> grain_models.GrainSegment:
    return grain_models.geometries.StarGrainSegment(
        outer_diameter=0.085,
        length=0.150,
        number_of_points=5,
        point_length=0.03,
        point_width=0.01,
    )


def build_motor(
    segments: list[grain_models.GrainSegment],
    dry_center_of_gravity: float = 0.35,
) -> motors_models.SolidMotor:
    grain = grain_models.Grain(spacing=0.01)
    for segment in segments:
        grain.add_segment(segment)

    thrust_chamber = thrust_chamber_models.SolidMotorThrustChamber(
        nozzle=thrust_chamber_models.Nozzle(
            throat_diameter=0.022,
            divergent_angle=12,
            expansion_ratio=8,
        ),
        combustion_chamber=thrust_chamber_models.CombustionChamber(
            inner_diameter=89.25e-3,
            internal_length=grain.total_length + 0.01,
        ),
        nozzle_exit_to_grain_port_distance=0.01,
        dry_mass_properties=mass_properties.DryMassProperties(
            dry_mass=6.0,
            center_of_gravity_coordinate=(dry_center_of_gravity, 0.0, 0.0),
            moment_of_inertia=(0.19, 0.19, 0.008),
        ),
    )
    return motors_models.SolidMotor(
        grain=grain,
        propellant=solid_propellants.KNSB_NAKKA,
        thrust_chamber=thrust_chamber,
    )


def simulate(motor: motors_models.SolidMotor) -> machwave_simulation.SimulationResult:
    params = machwave_simulation.InternalBallisticsSimulationParams(
        d_t=0.01,
        igniter_pressure=1e6,
        external_pressure=1.013e5,
    )
    return run_simulation(motor, params)
