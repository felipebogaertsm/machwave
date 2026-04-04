"""
This example simulates a rocket with the Nero motor, developed at
Supernova Rocketry UFJF in 2019. It is a class J KNDX motor with a
maximum operating pressure of 7 MPa.
"""

from machwave.common.decorators import timing
from machwave.models import grain as grain_models
from machwave.models import motors
from machwave.models import thrust_chamber as thrust_chamber_models
from machwave.models.grain import geometries as grain_geometries
from machwave.models.propellants.formulations import (
    solid as solid_propellants,
)
from machwave.services.plots import internal_ballistics as internal_ballistics_plots
from machwave.simulations import internal_ballistics


@timing
def main():
    propellant = solid_propellants.KNDX

    grain = grain_models.Grain(spacing=10e-3)
    bates_segment = grain_geometries.BatesSegment(
        outer_diameter=41e-3,
        core_diameter=15e-3,
        length=67.5e-3,
    )

    grain.add_segment(bates_segment)
    grain.add_segment(bates_segment)
    grain.add_segment(bates_segment)
    grain.add_segment(bates_segment)

    nozzle = thrust_chamber_models.Nozzle(
        inlet_diameter=43e-3,
        throat_diameter=9.5e-3,
        divergent_angle=12,
        convergent_angle=40,
        expansion_ratio=8,
    )
    combustion_chamber = thrust_chamber_models.CombustionChamber(
        casing_inner_diameter=44.5e-3,
        casing_outer_diameter=50.8e-3,
        thermal_liner_thickness=1e-3,
        internal_length=grain.total_length + 10e-3,
    )

    thrust_chamber = thrust_chamber_models.SolidMotorThrustChamber(
        dry_mass=0.85,
        nozzle=nozzle,
        combustion_chamber=combustion_chamber,
        nozzle_exit_to_grain_port_distance=0.01,
        center_of_gravity_coordinate=(0.04, 0.0, 0.0),
    )

    motor = motors.SolidMotor(
        grain=grain, propellant=propellant, thrust_chamber=thrust_chamber
    )

    params = internal_ballistics.InternalBallisticsParams(
        d_t=0.01,
        igniter_pressure=1e6,
        external_pressure=1e5,
    )

    simulation = internal_ballistics.InternalBallistics(motor=motor, params=params)
    (time, ib_state) = simulation.run()

    internal_ballistics_plots.thrust_pressure_plot(
        time, ib_state.thrust, ib_state.P_0
    ).show()

    simulation.print_results()


if __name__ == "__main__":
    main()
