"""
This example simulates a rocket with a solid motor that reaches an altitude 
of 3 km.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from rocketsolver.models.propulsion.grain import Grain
from rocketsolver.models.propulsion.grain.geometries import BatesSegment
from rocketsolver.models.propulsion.structure import (
    MotorStructure,
    Nozzle,
)
from rocketsolver.models.propulsion.structure.chamber import (
    BoltedCombustionChamber,
)
from rocketsolver.models.propulsion.propellants.solid import KNSB_NAKKA
from rocketsolver.models.recovery import Recovery
from rocketsolver.models.rocket import Rocket
from rocketsolver.models.materials.metals import Steel, Al6061T6
from rocketsolver.models.materials.elastics import EPDM
from rocketsolver.models.propulsion.thermals import ThermalLiner
from rocketsolver.models.recovery.events import (
    AltitudeBasedEvent,
    ApogeeBasedEvent,
)
from rocketsolver.models.recovery.parachutes import HemisphericalParachute
from rocketsolver.models.rocket.fuselage import Fuselage
from rocketsolver.models.atmosphere import Atmosphere1976
from rocketsolver.models.propulsion import SolidMotor
from rocketsolver.services.common.utilities import timing
from rocketsolver.simulations.internal_balistics_coupled import (
    InternalBallisticsCoupled,
    InternalBallisticsCoupledParams,
)


@timing
def main():
    # Motor:
    propellant = KNSB_NAKKA

    grain = Grain()

    bates_segment_1 = BatesSegment(
        outer_diameter=0.086,
        core_diameter=0.032,
        length=0.150,
        spacing=0.01,
    )

    bates_segment_2 = BatesSegment(
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

    nozzle = Nozzle(
        throat_diameter=0.0327,
        divergent_angle=12,
        convergent_angle=40,
        expansion_ratio=5,
        material=Steel(),
    )

    liner = ThermalLiner(thickness=0.002, material=EPDM())

    chamber = BoltedCombustionChamber(
        casing_inner_diameter=0.09525,
        outer_diameter=0.1016,
        liner=liner,
        length=grain.total_length + 0.01,
        casing_material=Al6061T6(),
        bulkhead_material=Al6061T6(),
        screw_material=Steel(),
        max_screw_count=30,
        screw_clearance_diameter=0.0085,
        screw_diameter=0.00675,
    )

    structure = MotorStructure(
        safety_factor=4,
        dry_mass=6.404,
        nozzle=nozzle,
        chamber=chamber,
    )

    motor = SolidMotor(grain=grain, propellant=propellant, structure=structure)

    # Recovery:
    recovery = Recovery()
    recovery.add_event(
        ApogeeBasedEvent(
            trigger_value=1,
            parachute=HemisphericalParachute(diameter=1.25),
        )
    )
    recovery.add_event(
        AltitudeBasedEvent(
            trigger_value=450,
            parachute=HemisphericalParachute(diameter=2.66),
        )
    )

    # Rocket:
    fuselage = Fuselage(
        length=2900, drag_coefficient=0.75, outer_diameter=0.12
    )

    rocket = Rocket(
        propulsion=motor,
        recovery=recovery,
        fuselage=fuselage,
        mass_without_motor=12.7,
    )

    # IB coupled simulation:
    params = InternalBallisticsCoupledParams(
        atmosphere=Atmosphere1976(),
        d_t=0.01,
        dd_t=10,
        initial_elevation_amsl=645,
        igniter_pressure=1.5e6,
        rail_length=5,
    )
    simulation = InternalBallisticsCoupled(rocket=rocket, params=params)

    (ib_operation, ballistic_operation) = simulation.run()

    simulation.print_results()


if __name__ == "__main__":
    main()
