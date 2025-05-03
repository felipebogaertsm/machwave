import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from machwave.models.atmosphere import Atmosphere1976
from machwave.models.materials import EPDM, Al6063T5, Steel
from machwave.models.propulsion.grain import Grain
from machwave.models.propulsion.grain.geometries import BatesSegment
from machwave.models.propulsion.motors import SolidMotor
from machwave.models.propulsion.propellants.solid import KNSB_NAKKA
from machwave.models.propulsion.thermals import ThermalLiner
from machwave.models.propulsion.thrust_chamber import ThrustChamber
from machwave.models.propulsion.thrust_chamber.combustion_chamber import (
    BoltedCombustionChamber,
)
from machwave.models.propulsion.thrust_chamber.nozzle import Nozzle
from machwave.models.recovery import Recovery
from machwave.models.recovery.events import (
    AltitudeBasedEvent,
    ApogeeBasedEvent,
)
from machwave.models.recovery.parachutes import HemisphericalParachute
from machwave.models.rocket import Rocket
from machwave.models.rocket.fuselage import Fuselage
from machwave.montecarlo import MonteCarloParameter, MonteCarloSimulation
from machwave.simulations.internal_balistics_coupled import (
    InternalBallisticsCoupled,
    InternalBallisticsCoupledParams,
)


def main():
    # Motor:
    propellant = KNSB_NAKKA

    grain = Grain()

    bates_segment_45 = BatesSegment(
        outer_diameter=MonteCarloParameter(value=115e-3, tolerance=1e-3),
        core_diameter=MonteCarloParameter(value=45e-3, tolerance=1e-3),
        length=MonteCarloParameter(value=200e-3, tolerance=1e-3),
        spacing=MonteCarloParameter(value=10e-3, tolerance=5e-3),
    )
    bates_segment_60 = BatesSegment(
        outer_diameter=MonteCarloParameter(value=115e-3, tolerance=1e-3),
        core_diameter=MonteCarloParameter(value=60e-3, tolerance=1e-3),
        length=MonteCarloParameter(value=200e-3, tolerance=1e-3),
        spacing=MonteCarloParameter(value=10e-3, tolerance=5e-3),
    )

    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_60)
    grain.add_segment(bates_segment_60)
    grain.add_segment(bates_segment_60)

    nozzle = Nozzle(
        inlet_diameter=80e-3,
        throat_diameter=MonteCarloParameter(value=37e-3, tolerance=0.5e-3),
        divergent_angle=12,
        convergent_angle=45,
        expansion_ratio=8,
        material=Steel(),
    )

    liner = ThermalLiner(thickness=2e-3, material=EPDM())

    chamber = BoltedCombustionChamber(
        inner_diameter=128.2e-3,
        outer_diameter=141.3e-3,
        liner=liner,
        length=grain.total_length + 10e-3,
        casing_material=Al6063T5(),
        bulkhead_material=Al6063T5(),
        screw_material=Steel(),
        max_screw_count=30,
        screw_clearance_diameter=9e-3,
        screw_diameter=6.75e-3,
    )

    thrust_chamber = ThrustChamber(
        dry_mass=21.013,
        nozzle=nozzle,
        combustion_chamber=chamber,
    )

    motor = SolidMotor(
        grain=grain, propellant=propellant, thrust_chamber=thrust_chamber
    )

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
        length=4e3,
        drag_coefficient=0.5,
        outer_diameter=0.17,
    )

    rocket = Rocket(
        propulsion=motor,
        recovery=recovery,
        fuselage=fuselage,
        mass_without_motor=25,
    )

    # Simulation:
    params = InternalBallisticsCoupledParams(
        Atmosphere1976(),
        0.01,
        10,
        600,
        1.5e6,
        5,
    )

    montecarlo_sim = MonteCarloSimulation(
        [rocket, params],
        100,
        InternalBallisticsCoupled,
    )

    montecarlo_sim.run()
    montecarlo_sim.plot_histogram(0, "total_impulse", "Total Impulse (N.s)")
    montecarlo_sim.plot_histogram(1, "apogee", "Apogee (m)")


if __name__ == "__main__":
    main()
