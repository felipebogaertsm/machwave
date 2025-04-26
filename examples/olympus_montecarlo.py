import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from machwave.models.propulsion.grain import Grain
from machwave.models.propulsion.grain.geometries import BatesSegment
from machwave.models.propulsion.motors import SolidMotor
from machwave.models.propulsion.thrust_chamber import ThrustChamber
from machwave.models.propulsion.thrust_chamber.nozzle import Nozzle
from machwave.models.propulsion.thrust_chamber.combustion_chamber import (
    BoltedCombustionChamber,
)
from machwave.models.propulsion.propellants.solid import KNSB_NAKKA
from machwave.models.materials.metals import Steel, Al6063T5
from machwave.models.materials.polymers import EPDM
from machwave.models.propulsion.thermals import ThermalLiner
from machwave.montecarlo import MonteCarloParameter, MonteCarloSimulation
from machwave.simulations.internal_ballistics import (
    InternalBallistics,
    InternalBallisticsParams,
)


def main():
    propellant = KNSB_NAKKA

    grain = Grain()
    for _ in range(4):
        grain.add_segment(
            BatesSegment(
                outer_diameter=MonteCarloParameter(0.115, tolerance=0.001),
                core_diameter=MonteCarloParameter(0.045, tolerance=0.001),
                length=MonteCarloParameter(0.200, tolerance=0.001),
                spacing=MonteCarloParameter(0.010, tolerance=0.005),
            )
        )
    for _ in range(3):
        grain.add_segment(
            BatesSegment(
                outer_diameter=MonteCarloParameter(0.115, tolerance=0.001),
                core_diameter=MonteCarloParameter(0.060, tolerance=0.001),
                length=MonteCarloParameter(0.200, tolerance=0.001),
                spacing=MonteCarloParameter(0.010, tolerance=0.005),
            )
        )

    nozzle = Nozzle(
        inlet_diameter=0.080,
        throat_diameter=MonteCarloParameter(0.037, tolerance=0.0005),
        divergent_angle=12,
        convergent_angle=45,
        expansion_ratio=8,
        material=Steel(),
    )

    liner = ThermalLiner(thickness=2e-3, material=EPDM())

    chamber = BoltedCombustionChamber(
        inner_diameter=0.1282,
        outer_diameter=0.1413,
        liner=liner,
        length=grain.total_length + 0.010,
        casing_material=Al6063T5(),
        bulkhead_material=Al6063T5(),
        screw_material=Steel(),
        max_screw_count=30,
        screw_clearance_diameter=0.009,
        screw_diameter=0.00675,
    )

    thrust_chamber = ThrustChamber(
        dry_mass=21.013,
        nozzle=nozzle,
        combustion_chamber=chamber,
    )

    motor = SolidMotor(
        grain=grain,
        propellant=propellant,
        thrust_chamber=thrust_chamber,
    )

    ib_params = InternalBallisticsParams(
        d_t=0.01,
        external_pressure=1e5,
        igniter_pressure=1e6,
    )

    mc = MonteCarloSimulation(
        [motor, ib_params],
        100,
        InternalBallistics,
    )
    mc.run()
    mc.plot_histogram(1, "total_impulse", "Total Impulse (N·s)")


if __name__ == "__main__":
    main()
