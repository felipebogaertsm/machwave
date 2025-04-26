"""
This example simulates a rocket with an APCP solid motor, using
an InternalBallisticsCoupled simulation that includes both
internal ballistics and atmospheric flight.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from machwave.models.propulsion.grain import Grain
from machwave.models.propulsion.grain.geometries import BatesSegment
from machwave.models.propulsion.thrust_chamber.nozzle import Nozzle
from machwave.models.propulsion.thrust_chamber.combustion_chamber import (
    BoltedCombustionChamber,
)
from machwave.models.propulsion.propellants.solid import MIT_CHERRY_LIMEADE
from machwave.models.materials import Steel, Al6061T6
from machwave.models.materials import EPDM
from machwave.models.propulsion.thermals import ThermalLiner
from machwave.models.propulsion.motors import SolidMotor
from machwave.models.propulsion.thrust_chamber import ThrustChamber
from machwave.models.rocket import Rocket
from machwave.models.rocket.fuselage import Fuselage
from machwave.models.recovery import Recovery
from machwave.models.recovery.events import ApogeeBasedEvent, AltitudeBasedEvent
from machwave.models.recovery.parachutes import HemisphericalParachute
from machwave.models.atmosphere import Atmosphere1976
from machwave.services.decorators import timing
from machwave.simulations.internal_balistics_coupled import (
    InternalBallisticsCoupled,
    InternalBallisticsCoupledParams,
)
from machwave.services.plots.ballistics import ballistics_plots


@timing
def main():
    # 1) Define the propellant and grain geometry
    propellant = MIT_CHERRY_LIMEADE

    grain = Grain()
    bates_segment = BatesSegment(
        outer_diameter=0.085,
        core_diameter=0.035,
        length=0.150,
        spacing=0.01,
    )

    # Add multiple segments
    grain.add_segment(bates_segment)
    grain.add_segment(bates_segment)
    grain.add_segment(bates_segment)
    grain.add_segment(bates_segment)
    grain.add_segment(bates_segment)

    # 2) Define nozzle and combustion chamber (instead of MotorStructure)
    nozzle = Nozzle(
        inlet_diameter=0.080,
        throat_diameter=0.022,
        divergent_angle=12,
        convergent_angle=45,
        expansion_ratio=8,
        material=Steel(),
    )

    liner = ThermalLiner(thickness=0.003, material=EPDM())

    chamber = BoltedCombustionChamber(
        inner_diameter=0.09525,
        outer_diameter=0.1016,
        liner=liner,
        length=grain.total_length + 0.01,
        casing_material=Al6061T6(),
        bulkhead_material=Al6061T6(),
        screw_material=Steel(),
        max_screw_count=30,
        screw_clearance_diameter=0.0065,
        screw_diameter=0.005,
    )

    # Build a ThrustChamber for this solid motor
    # (We assume some dry mass for the chamber assembly)
    thrust_chamber = ThrustChamber(
        dry_mass=6.0,  # adapt as needed
        nozzle=nozzle,
        combustion_chamber=chamber,
    )

    # 3) Create the SolidMotor using the newly formed thrust chamber
    motor = SolidMotor(
        grain=grain, propellant=propellant, thrust_chamber=thrust_chamber
    )

    # 4) Recovery system (if desired)
    #    Add events for apogee and a secondary chute at altitude
    recovery = Recovery()
    recovery.add_event(
        ApogeeBasedEvent(
            trigger_value=1,  # seconds after apogee
            parachute=HemisphericalParachute(diameter=1.25),
        )
    )
    recovery.add_event(
        AltitudeBasedEvent(
            trigger_value=300,
            parachute=HemisphericalParachute(diameter=2.0),
        )
    )

    # 5) Define the rocket: fuselage + motor + recovery
    fuselage = Fuselage(length=2.0, drag_coefficient=0.75, outer_diameter=0.12)
    rocket = Rocket(
        propulsion=motor,
        recovery=recovery,
        fuselage=fuselage,
        mass_without_motor=10.0,  # structure, avionics, payload, etc.
    )

    # 6) Set up the InternalBallisticsCoupled simulation parameters
    params = InternalBallisticsCoupledParams(
        atmosphere=Atmosphere1976(),
        d_t=0.01,  # time step for flight & internal ballistics
        dd_t=10,  # iteration sub-steps for solver
        initial_elevation_amsl=0,  # your launch site altitude
        igniter_pressure=1e6,  # ignition pressure guess
        rail_length=3.0,  # launch rail length [m]
    )

    # 7) Run the combined internal-ballistics + flight simulation
    simulation = InternalBallisticsCoupled(rocket=rocket, params=params)
    ib_operation, ballistic_operation = simulation.run()

    # 8) Plot flight results
    ballistics_plots(
        ballistic_operation.t,
        ballistic_operation.acceleration,
        ballistic_operation.v,
        ballistic_operation.y,
    ).show()

    # 9) Print summary results
    simulation.print_results()


if __name__ == "__main__":
    main()
