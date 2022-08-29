# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import time

import numpy as np

from rocketsolver.models.propulsion.grain import Grain
from rocketsolver.models.propulsion.grain.bates import BatesSegment
from rocketsolver.models.propulsion.structure import (
    MotorStructure,
    Nozzle,
)
from rocketsolver.models.propulsion.structure.chamber import BoltedCombustionChamber
from rocketsolver.models.propellants.solid import get_solid_propellant_from_name
from rocketsolver.models.recovery import Recovery
from rocketsolver.models.rocket import Rocket
from rocketsolver.models.materials.metals import Steel, Al6063T5
from rocketsolver.models.materials.elastics import EPDM
from rocketsolver.models.propulsion.thermals import ThermalLiner
from rocketsolver.models.recovery.events import (
    AltitudeBasedEvent,
    ApogeeBasedEvent,
)
from rocketsolver.models.recovery.parachutes import HemisphericalParachute
from rocketsolver.models.rocket.fuselage import Fuselage
from rocketsolver.models.rocket.structure import RocketStructure
from rocketsolver.models.atmosphere import Atmosphere1976
from rocketsolver.models.propulsion import SolidMotor

from rocketsolver.utils.utilities import output_eng_csv
from rocketsolver.utils.plots import (
    performance_interactive_plot,
    performance_plot,
    main_plot,
    mass_flux_plot,
    ballistics_plots,
)

from rocketsolver.simulations.internal_balistics_coupled import (
    InternalBallisticsCoupled,
)
from rocketsolver.simulations.structural import StructuralSimulation


def main():
    start = time.time()  # starting timer

    # Motor:
    propellant = get_solid_propellant_from_name(prop_name="KNSB-NAKKA")

    grain = Grain()

    bates_segment_45 = BatesSegment(
        outer_diameter=115e-3,
        core_diameter=45e-3,
        length=200e-3,
        spacing=10e-3,
    )
    bates_segment_60 = BatesSegment(
        outer_diameter=115e-3,
        core_diameter=60e-3,
        length=200e-3,
        spacing=10e-3,
    )

    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_60)
    grain.add_segment(bates_segment_60)
    grain.add_segment(bates_segment_60)

    nozzle = Nozzle(
        throat_diameter=37e-3,
        divergent_angle=12,
        convergent_angle=45,
        expansion_ratio=8,
        material=Steel(),
    )

    liner = ThermalLiner(thickness=2e-3, material=EPDM())

    chamber = BoltedCombustionChamber(
        casing_inner_diameter=128.2e-3,
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

    structure = MotorStructure(
        safety_factor=4,
        dry_mass=21.013,
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
        length=4e3,
        drag_coefficient=0.5,
        outer_diameter=0.17,
    )

    rocket_structure = RocketStructure(mass_without_motor=25)

    rocket = Rocket(
        fuselage=fuselage,
        structure=rocket_structure,
    )

    # IB coupled simulation:
    internal_ballistics_coupled_simulation = InternalBallisticsCoupled(
        motor=motor,
        rocket=rocket,
        recovery=recovery,
        atmosphere=Atmosphere1976(),
        d_t=0.001,
        dd_t=10,
        initial_elevation_amsl=636,
        igniter_pressure=1.5e6,
        rail_length=5,
    )

    (
        t,
        ib_operation,
        ballistic_operation,
    ) = internal_ballistics_coupled_simulation.run()

    internal_ballistics_coupled_simulation.print_results()

    # Structural simulation:
    structural_simulation = StructuralSimulation(
        motor.structure, np.max(ib_operation.P_0), 4
    )

    structural_parameters = structural_simulation.run()

    structural_simulation.print_results()

    print("\n\nExecution time: %.4f seconds\n\n" % (time.time() - start))

    # Plots:
    performance_interactive_plot(ib_operation).show()


if __name__ == "__main__":
    main()
