"""
Olympus is an O-class solid rocket motor designed during the LASC Cooperation 
Program (2020-2022). It was originally intended to be used in the Concorde 
5km-apogee rocket, but was never used in a flight. The motor was successfully
tested on July 2, 2022 and, at the time, it was the largest experimental motor
ever built in Latin America.
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
from rocketsolver.models.materials.metals import Steel, Al6063T5
from rocketsolver.models.materials.elastics import EPDM
from rocketsolver.models.propulsion.thermals import ThermalLiner
from rocketsolver.models.propulsion import SolidMotor
from rocketsolver.services.common.plots import (
    performance_interactive_plot,
    mass_flux_plot,
)
from rocketsolver.services.common.utilities import timing
from rocketsolver.simulations.internal_ballistics import (
    InternalBallistics,
    InternalBallisticsParams,
)


@timing
def main():
    # Motor:
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

    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_60)
    grain.add_segment(bates_segment_60)
    grain.add_segment(bates_segment_60)

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

    structure = MotorStructure(
        safety_factor=4,
        dry_mass=19,
        nozzle=nozzle,
        chamber=chamber,
    )

    motor = SolidMotor(grain=grain, propellant=propellant, structure=structure)

    simulation = InternalBallistics(
        motor=motor,
        params=InternalBallisticsParams(
            d_t=0.01, igniter_pressure=1e6, external_pressure=1e5
        ),
    )

    (time, ib_operation) = simulation.run()

    simulation.print_results()

    # Plots:
    performance_interactive_plot(ib_operation).show()
    mass_flux_plot(
        grain.get_mass_flux_per_segment(
            ib_operation.burn_rate,
            propellant.density,
            ib_operation.web,
        ),
        ib_operation.t,
    ).show()


if __name__ == "__main__":
    main()
