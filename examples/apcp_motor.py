"""
This example simulates a rocket with an APCP solid motor, using
an InternalBallisticsCoupled simulation that includes both
internal ballistics and atmospheric flight.
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


@timing
def main():
    propellant = solid_propellants.MIT_CHERRY_LIMEADE

    grain = grain_models.Grain(spacing=0.01)
    bates_segment = grain_geometries.BatesSegment(
        outer_diameter=0.085,
        core_diameter=0.035,
        length=0.150,
    )

    grain.add_segment(bates_segment)
    grain.add_segment(bates_segment)
    grain.add_segment(bates_segment)
    grain.add_segment(bates_segment)
    grain.add_segment(bates_segment)

    nozzle = thrust_chamber_models.Nozzle(
        inlet_diameter=0.080,
        throat_diameter=0.022,
        divergent_angle=12,
        convergent_angle=45,
        expansion_ratio=8,
    )
    combustion_chamber = thrust_chamber_models.CombustionChamber(
        casing_inner_diameter=95.25e-3,
        casing_outer_diameter=101.6e-3,
        thermal_liner_thickness=3e-3,
        internal_length=grain.total_length + 0.01,
    )

    thrust_chamber = thrust_chamber_models.SolidMotorThrustChamber(
        dry_mass=6.0,
        nozzle=nozzle,
        combustion_chamber=combustion_chamber,
        nozzle_exit_to_grain_port_distance=0.01,
        center_of_gravity_coordinate=(0.35, 0.0, 0.0),
    )

    motor = motors.SolidMotor(
        grain=grain, propellant=propellant, thrust_chamber=thrust_chamber
    )

    params = simulation.InternalBallisticsSimulationParams(
        d_t=0.01,
        igniter_pressure=1e6,
        external_pressure=1e5,
    )

    sim = simulation.InternalBallisticsSimulation(motor=motor, params=params)
    (time, ib_state) = sim.run()

    internal_ballistics_plots.thrust_pressure_plot(
        time, ib_state.thrust, ib_state.P_0
    ).show()

    sim.print_results()


if __name__ == "__main__":
    main()
