"""
Sample APCP solid rocket motor.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from machwave.models.propulsion.grain import Grain
from machwave.models.propulsion.grain.geometries import BatesSegment
from machwave.models.propulsion.structure import (
    MotorStructure,
    Nozzle,
)
from machwave.models.propulsion.structure.chamber import (
    BoltedCombustionChamber,
)
from machwave.models.propulsion.propellants.solid import MIT_CHERRY_LIMEADE
from machwave.models.materials.metals import Steel, Al6061T6
from machwave.models.materials.polymers import EPDM
from machwave.models.propulsion.thermals import ThermalLiner
from machwave.models.propulsion import SolidMotor
from machwave.services.plots.internal_ballistics import (
    thrust_pressure_plot,
    mass_flux_plot,
)
from machwave.services.decorators import timing
from machwave.simulations.internal_ballistics import (
    InternalBallistics,
    InternalBallisticsParams,
)


@timing
def main():
    # Motor:
    propellant = MIT_CHERRY_LIMEADE

    grain = Grain()

    bates_segment = BatesSegment(
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

    nozzle = Nozzle(
        throat_diameter=0.022,
        divergent_angle=12,
        convergent_angle=45,
        expansion_ratio=8,
        material=Steel(),
    )

    liner = ThermalLiner(thickness=0.003, material=EPDM())

    chamber = BoltedCombustionChamber(
        casing_inner_diameter=0.09525,
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

    structure = MotorStructure(
        safety_factor=4,
        dry_mass=6,
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
    thrust_pressure_plot(
        ib_operation.t, ib_operation.thrust, ib_operation.P_0
    ).show()

    mass_flux_plot(
        ib_operation.t,
        grain.get_mass_flux_per_segment(
            ib_operation.burn_rate,
            propellant.density,
            ib_operation.web,
        ),
    ).show()


if __name__ == "__main__":
    main()
