"""
This example simulates a rocket with an APCP solid motor, using
an InternalBallisticsCoupled simulation that includes both
internal ballistics and atmospheric flight.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from machwave.services.decorators import timing
from machwave.models import materials
from machwave.models.propulsion import motors
from machwave.models.propulsion import grain as grain_models
from machwave.models.propulsion.grain import geometries as grain_geometries
from machwave.models.propulsion.propellants import solid as solid_propellants
from machwave.models.propulsion import thrust_chamber as thrust_chamber_models
from machwave.services.plots import internal_ballistics as internal_ballistics_plots
from machwave.simulations import internal_ballistics


@timing
def main():
    propellant = solid_propellants.MIT_CHERRY_LIMEADE

    grain = grain_models.Grain()
    bates_segment = grain_geometries.BatesSegment(
        outer_diameter=0.085,
        core_diameter=0.035,
        length=0.150,
        spacing=0.01,
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
        material=materials.Steel(),
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
    (time, ib_operation) = simulation.run()

    internal_ballistics_plots.thrust_pressure_plot(
        time, ib_operation.thrust, ib_operation.P_0
    ).show()

    simulation.print_results()


if __name__ == "__main__":
    main()
