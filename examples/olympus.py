"""
Olympus is an O-class solid rocket motor designed during the LASC Cooperation
Program (2020-2022). It was originally intended for a 5km-apogee rocket but
never used in flight. The motor was successfully tested on July 2, 2022, and
at the time, it was the largest experimental motor ever built in Latin America.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from machwave.models.propulsion.grain import Grain
from machwave.models.propulsion.grain.geometries import BatesSegment
from machwave.models.propulsion.structure import Nozzle
from machwave.models.propulsion.structure.chamber import BoltedCombustionChamber
from machwave.models.propulsion.propellants.solid import KNSB_NAKKA
from machwave.models.materials.metals import Steel, Al6063T5
from machwave.models.materials.polymers import EPDM
from machwave.models.propulsion.thermals import ThermalLiner
from machwave.models.propulsion.motors import SolidMotor
from machwave.models.propulsion.thrust_chamber import ThrustChamber

from machwave.models.rocket import Rocket
from machwave.models.rocket.fuselage import Fuselage
from machwave.models.recovery import Recovery
from machwave.models.recovery.events import ApogeeBasedEvent, AltitudeBasedEvent
from machwave.models.recovery.parachutes import HemisphericalParachute
from machwave.models.atmosphere.atm_1976 import Atmosphere1976

from machwave.services.decorators import timing
from machwave.simulations.internal_balistics_coupled import (
    InternalBallisticsCoupled,
    InternalBallisticsCoupledParams,
)
from machwave.services.plots.ballistics import ballistics_plots


@timing
def main():
    # 1) Motor geometry / propellant:
    propellant = KNSB_NAKKA

    grain = Grain()
    bates_segment_45 = BatesSegment(
        outer_diameter=0.117,
        core_diameter=0.045,
        length=0.200,
        spacing=0.01,
    )
    bates_segment_60 = BatesSegment(
        outer_diameter=0.117,
        core_diameter=0.060,
        length=0.200,
        spacing=0.01,
    )

    # Add multiple segments
    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_60)
    grain.add_segment(bates_segment_60)
    grain.add_segment(bates_segment_60)

    # 2) Nozzle + combustion chamber => ThrustChamber
    nozzle = Nozzle(
        throat_diameter=0.037,
        divergent_angle=12,
        convergent_angle=45,
        expansion_ratio=8,
        material=Steel(),
    )

    liner = ThermalLiner(thickness=0.003, material=EPDM())

    chamber = BoltedCombustionChamber(
        casing_inner_diameter=0.1282,
        outer_diameter=0.1413,
        liner=liner,
        length=grain.total_length + 0.01,
        casing_material=Al6063T5(),
        bulkhead_material=Al6063T5(),
        screw_material=Steel(),
        max_screw_count=30,
        screw_clearance_diameter=0.0085,
        screw_diameter=0.00675,
    )

    # We can treat the old "dry_mass=19" from MotorStructure as the chamber's total mass
    thrust_chamber = ThrustChamber(
        dry_mass=19.0,
        nozzle=nozzle,
        combustion_chamber=chamber,
    )

    # 3) SolidMotor using the new thrust chamber
    motor = SolidMotor(
        grain=grain,
        propellant=propellant,
        thrust_chamber=thrust_chamber,
    )

    # 4) (Optional) Recovery system - if you want to see flight with parachutes
    recovery = Recovery()
    recovery.add_event(
        ApogeeBasedEvent(
            trigger_value=1.0,
            parachute=HemisphericalParachute(diameter=1.5),
        )
    )
    recovery.add_event(
        AltitudeBasedEvent(
            trigger_value=400.0,
            parachute=HemisphericalParachute(diameter=3.0),
        )
    )

    # 5) Rocket (with motor, recovery, fuselage, etc.)
    fuselage = Fuselage(length=3.0, drag_coefficient=0.6, outer_diameter=0.15)

    rocket = Rocket(
        propulsion=motor,
        recovery=recovery,
        fuselage=fuselage,
        mass_without_motor=15.0,  # structure, payload, avionics, etc.
    )

    # 6) Internal-ballistics + flight simulation parameters
    params = InternalBallisticsCoupledParams(
        atmosphere=Atmosphere1976(),
        d_t=0.01,  # time-step for flight & IB
        dd_t=10,  # sub-steps
        initial_elevation_amsl=0,  # your launch site altitude
        igniter_pressure=1e6,  # initial guess to ignite
        rail_length=5.0,  # launch rail
    )

    simulation = InternalBallisticsCoupled(rocket=rocket, params=params)
    ib_operation, ballistic_operation = simulation.run()

    # 7) Print results
    simulation.print_results()

    # 8) Plot basic flight parameters (acc, velocity, altitude vs time)
    ballistics_plots(
        ballistic_operation.t,
        ballistic_operation.acceleration,
        ballistic_operation.v,
        ballistic_operation.y,
    ).show()


if __name__ == "__main__":
    main()
