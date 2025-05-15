"""
This example simulates a rocket with a solid motor that reaches an altitude
of 3 km.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from machwave.models import atmosphere, materials
from machwave.models import recovery as recovery_models
from machwave.models import rocket as rocket_models
from machwave.models.propulsion import grain as grain_models
from machwave.models.propulsion import motors
from machwave.models.propulsion import thrust_chamber as thrust_chamber_models
from machwave.models.propulsion.grain import geometries as grain_geometries
from machwave.models.propulsion.propellants import solid as solid_propellants
from machwave.models.recovery import events, parachutes
from machwave.services.decorators import timing
from machwave.services.plots import ballistics as ballistics_plots
from machwave.simulations import internal_balistics_coupled


@timing
def main():
    # Motor:
    propellant = solid_propellants.KNSB_NAKKA

    grain = grain_models.Grain()

    bates_segment_1 = grain_geometries.BatesSegment(
        outer_diameter=0.086,
        core_diameter=0.032,
        length=0.150,
        spacing=0.01,
    )

    bates_segment_2 = grain_geometries.BatesSegment(
        outer_diameter=0.086,
        core_diameter=0.046,
        length=0.150,
        spacing=0.01,
    )

    grain.add_segment(bates_segment_1)
    grain.add_segment(bates_segment_1)
    grain.add_segment(bates_segment_1)
    grain.add_segment(bates_segment_1)
    grain.add_segment(bates_segment_2)
    grain.add_segment(bates_segment_2)
    grain.add_segment(bates_segment_2)

    nozzle = thrust_chamber_models.Nozzle(
        inlet_diameter=0.086,
        throat_diameter=0.0327,
        divergent_angle=12,
        convergent_angle=40,
        expansion_ratio=5,
        material=materials.Steel(),
    )

    combustion_chamber = thrust_chamber_models.CombustionChamber(
        casing_inner_diameter=95.25e-3,
        casing_outer_diameter=101.6e-3,
        thermal_liner_thickness=3e-3,
        internal_length=grain.total_length + 0.01,
    )

    thrust_chamber = thrust_chamber_models.SolidMotorThrustChamber(
        dry_mass=6.404,
        nozzle=nozzle,
        combustion_chamber=combustion_chamber,
    )

    motor = motors.SolidMotor(
        grain=grain, propellant=propellant, thrust_chamber=thrust_chamber
    )

    # Recovery:
    recovery = recovery_models.Recovery()
    recovery.add_event(
        events.ApogeeBasedEvent(
            trigger_value=1,
            parachute=parachutes.HemisphericalParachute(diameter=1.25),
        )
    )
    recovery.add_event(
        events.AltitudeBasedEvent(
            trigger_value=450,
            parachute=parachutes.HemisphericalParachute(diameter=2.66),
        )
    )

    # Rocket:
    fuselage = rocket_models.Fuselage(
        length=2900, drag_coefficient=0.75, outer_diameter=0.12
    )

    rocket = rocket_models.Rocket(
        propulsion=motor,
        recovery=recovery,
        fuselage=fuselage,
        mass_without_motor=12.7,
    )

    # IB coupled simulation:
    params = internal_balistics_coupled.InternalBallisticsCoupledParams(
        atmosphere=atmosphere.Atmosphere1976(),
        d_t=0.01,
        dd_t=10,
        initial_elevation_amsl=645,
        igniter_pressure=1.5e6,
        rail_length=5,
    )
    simulation = internal_balistics_coupled.InternalBallisticsCoupled(
        rocket=rocket, params=params
    )

    (ib_operation, ballistic_operation) = simulation.run()

    ballistics_plots.ballistics_plots(
        ballistic_operation.t,
        ballistic_operation.acceleration,
        ballistic_operation.v,
        ballistic_operation.y,
    ).show()

    simulation.print_results()


if __name__ == "__main__":
    main()
