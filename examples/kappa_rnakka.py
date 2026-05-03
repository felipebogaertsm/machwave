"""
Example for the Kappa motor, developed by Richard Nakka.
https://www.nakka-rocketry.net/kappa.html
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
from machwave import simulation


def build() -> tuple[motors.SolidMotor, simulation.InternalBallisticsSimulationParams]:
    propellant = solid_propellants.KNDX

    grain = grain_models.Grain(spacing=5e-3)
    bates_segment = grain_geometries.BatesSegment(
        outer_diameter=55e-3,
        core_diameter=19e-3,
        length=101.6e-3,
    )

    grain.add_segment(bates_segment)
    grain.add_segment(bates_segment)
    grain.add_segment(bates_segment)
    grain.add_segment(bates_segment)

    nozzle = thrust_chamber_models.Nozzle(
        inlet_diameter=40e-3,
        throat_diameter=12.8e-3,
        divergent_angle=12,
        convergent_angle=25,
        expansion_ratio=11,
    )
    combustion_chamber = thrust_chamber_models.CombustionChamber(
        casing_inner_diameter=60e-3,
        casing_outer_diameter=64e-3,
        thermal_liner_thickness=1e-3,
        internal_length=grain.total_length + 5e-3,
    )

    thrust_chamber = thrust_chamber_models.SolidMotorThrustChamber(
        dry_mass=0.85,
        nozzle=nozzle,
        combustion_chamber=combustion_chamber,
        nozzle_exit_to_grain_port_distance=0.01,
        center_of_gravity_coordinate=(0.035, 0.0, 0.0),
    )

    motor = motors.SolidMotor(
        grain=grain, propellant=propellant, thrust_chamber=thrust_chamber
    )

    params = simulation.InternalBallisticsSimulationParams(
        d_t=0.001,
        igniter_pressure=1e6,
        external_pressure=1e5,
        other_losses=12.0,
    )

    return motor, params


@timing
def main():
    motor, params = build()

    sim = simulation.InternalBallisticsSimulation(motor=motor, params=params)
    (time, ib_state) = sim.run()

    internal_ballistics_plots.thrust_pressure_plot(
        time, ib_state.thrust, ib_state.P_0
    ).show()

    sim.print_results()


if __name__ == "__main__":
    main()
