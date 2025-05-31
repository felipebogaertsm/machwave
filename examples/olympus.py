"""
Olympus is an O-class solid rocket motor designed during the LASC Costate
Program (2020-2022). It was originally intended for a 5km-apogee rocket but
never used in flight. The motor was successfully tested on July 2, 2022, and
at the time, it was the largest experimental motor ever built in Latin America.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from machwave.common.decorators import timing
from machwave.models import atmosphere, materials
from machwave.models import recovery as recovery_models
from machwave.models import rocket as rocket_models
from machwave.models.propulsion import grain as grain_models
from machwave.models.propulsion import motors
from machwave.models.propulsion import thrust_chamber as thrust_chamber_models
from machwave.models.propulsion.grain import geometries as grain_geometries
from machwave.models.propulsion.propellants import solid as solid_propellants
from machwave.models.recovery import events, parachutes
from machwave.services.plots import ballistics as ballistics_plots
from machwave.services.plots import internal_ballistics as internal_ballistics_plots
from machwave.simulations import internal_balistics_coupled


@timing
def main():
    propellant = solid_propellants.KNSB_NAKKA

    grain = grain_models.Grain()
    bates_segment_45 = grain_geometries.BatesSegment(
        outer_diameter=0.117,
        core_diameter=0.045,
        length=0.200,
        spacing=0.01,
    )
    bates_segment_60 = grain_geometries.BatesSegment(
        outer_diameter=0.117,
        core_diameter=0.060,
        length=0.200,
        spacing=0.01,
    )

    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_60)
    grain.add_segment(bates_segment_60)
    grain.add_segment(bates_segment_60)

    # 2) Nozzle + combustion chamber => ThrustChamber
    nozzle = thrust_chamber_models.Nozzle(
        inlet_diameter=0.080,
        throat_diameter=0.037,
        divergent_angle=12,
        convergent_angle=45,
        expansion_ratio=8,
        material=materials.Steel(),
    )

    combustion_chamber = thrust_chamber_models.CombustionChamber(
        casing_inner_diameter=0.1282,
        casing_outer_diameter=0.1413,
        thermal_liner_thickness=0.003,
        internal_length=grain.total_length + 0.01,
    )

    thrust_chamber = thrust_chamber_models.SolidMotorThrustChamber(
        dry_mass=19.0,
        nozzle=nozzle,
        combustion_chamber=combustion_chamber,
    )

    # 3) SolidMotor using the new thrust chamber
    motor = motors.SolidMotor(
        grain=grain,
        propellant=propellant,
        thrust_chamber=thrust_chamber,
    )

    # 4) (Optional) Recovery system - if you want to see flight with parachutes
    recovery = recovery_models.Recovery()
    recovery.add_event(
        events.ApogeeBasedEvent(
            trigger_value=1.0,
            parachute=parachutes.HemisphericalParachute(diameter=1.5),
        )
    )
    recovery.add_event(
        events.AltitudeBasedEvent(
            trigger_value=400.0,
            parachute=parachutes.HemisphericalParachute(diameter=3.0),
        )
    )

    fuselage = rocket_models.Fuselage(
        length=3.0, drag_coefficient=0.6, outer_diameter=0.15
    )

    rocket = rocket_models.Rocket(
        propulsion=motor,
        recovery=recovery,
        fuselage=fuselage,
        mass_without_motor=30,
    )

    params = internal_balistics_coupled.InternalBallisticsCoupledParams(
        atmosphere=atmosphere.Atmosphere1976(),
        d_t=0.01,
        dd_t=10,
        initial_elevation_amsl=0,
        igniter_pressure=1e6,
        rail_length=5.0,
    )

    simulation = internal_balistics_coupled.InternalBallisticsCoupled(
        rocket=rocket, params=params
    )
    ib_state, ballistic_state = simulation.run()

    simulation.print_results()

    ).show()

    ballistics_plots.ballistics_plots(
        ballistic_state.t,
        ballistic_state.acceleration,
        ballistic_state.v,
        ballistic_state.y,
    ).show()


if __name__ == "__main__":
    main()
