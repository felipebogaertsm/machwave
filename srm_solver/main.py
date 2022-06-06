# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import time

from models.propulsion.grain import Grain
from models.propulsion.grain.bates import BatesSegment
from models.propulsion.structure import (
    BoltedCombustionChamber,
    MotorStructure,
    Nozzle,
)
from models.propellants import get_propellant_from_name
from models.recovery import Recovery
from models.rocket import Rocket
from models.materials.metals import Steel, Al6063T5
from models.materials.elastics import EPDM
from models.propulsion.thermals import ThermalLiner
from models.recovery.events import (
    AltitudeBasedEvent,
    ApogeeBasedEvent,
)
from models.recovery.parachutes import HemisphericalParachute
from models.rocket.fuselage import Fuselage
from models.rocket.structure import RocketStructure
from models.atmosphere import Atmosphere1976
from models.propulsion import SolidMotor

from utils.utilities import output_eng_csv
from utils.plots import (
    performance_interactive_plot,
    performance_plot,
    main_plot,
    mass_flux_plot,
    ballistics_plots,
)

from simulations.internal_balistics_coupled import InternalBallisticsCoupled
from simulations.structural import StructuralSimulation


def main():
    # /////////////////////////////////////////////////////////////////////////
    # TIME FUNCTION START
    # Starts the timer.

    start = time.time()

    # /////////////////////////////////////////////////////////////////////////
    # PRE CALCULATIONS AND DEFINITIONS
    # This section is responsible for creating all of the instances of classes that
    # can be obtained from the input data.
    # It includes instanced of the classes: PropellantSelected, BATES,
    # MotorStructure, Rocket, Rocket and Recovery.
    # It also does some small calculations of the chamber length and chamber
    # diameter.

    # Motor:
    propellant = get_propellant_from_name(prop_name="KNSB-NAKKA")

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

    # /////////////////////////////////////////////////////////////////////////
    # INTERNAL BALLISTICS AND TRAJECTORY
    # This section runs the main simulation of the program, returning the results
    # of all the internal ballistics and trajectory calculations.
    # The 'run_ballistics' function runs, in a single loop, the chamber pressure
    # PDE as well as the rocket flight mechanics ODE.
    # The exit pressure of the motor is automatically subtracted from the external
    # (or ambient) pressure of the rocket during flight, yielding more precise
    # motor thrust estimation.
    # 'run_ballistics' returns instances of the classes Ballistics and
    # InternalBallistics.

    internal_ballistics_coupled_simulation = InternalBallisticsCoupled(
        motor=motor,
        rocket=rocket,
        recovery=recovery,
        atmosphere=Atmosphere1976(),
        d_t=0.01,
        dd_t=10,
        initial_elevation_amsl=600,
        igniter_pressure=1.5e6,
        rail_length=5,
    )

    (
        t,
        ib_operation,
        ballistic_operation,
    ) = internal_ballistics_coupled_simulation.run()

    internal_ballistics_coupled_simulation.print_results()

    # /////////////////////////////////////////////////////////////////////////
    # MOTOR STRUCTURE
    # This section runs the structural simulation. The function
    # 'run_structural_simulation' returns an instance of the class
    # StructuralParameters.

    # structural_parameters = StructuralSimulation(
    #     structure, ib_parameters.P0, 4
    # ).run()

    # /////////////////////////////////////////////////////////////////////////
    # OUTPUT TO ENG AND CSV FILE
    # This section exports the results inside a .csv and a .eng file. The .eng
    # file is totally compatible with OpenRocket or RASAero software. The .csv is
    # exported mainly for the ease of visualization and storage.

    output_eng_csv(
        time=t,
        burn_time=ib_operation.burn_time,
        thrust=ib_operation.thrust,
        propellant_volume=ib_operation.propellant_volume,
        dt=0.1,
        chamber_od=motor.structure.chamber.outer_diameter,
        chamber_length=motor.structure.chamber.length,
        eng_resolution=25,
        propellant_density=motor.propellant.density,
        motor_dry_mass=motor.structure.dry_mass,
        manufacturer="LCP 2022",
        name="OLYMPUS",
    )

    # /////////////////////////////////////////////////////////////////////////
    # TIME FUNCTION END
    # Ends the time function.

    print("\n\nExecution time: %.4f seconds\n\n" % (time.time() - start))

    # /////////////////////////////////////////////////////////////////////////
    # PLOTS
    # Saves some of the most important plots to the 'output' folder.

    performance_plot(
        ib_operation.thrust,
        ib_operation.P_0,
        ib_operation.t,
        ib_operation.thrust_time,
    )

    main_plot(
        ib_operation.t,
        ib_operation.thrust,
        ib_operation.P_0,
        ib_operation.klemmung,
        ib_operation.m_prop,
        ib_operation.thrust_time,
    )

    mass_flux_plot(
        t,
        ib_operation.grain_mass_flux,
        ib_operation.thrust_time,
    )

    ballistics_plots(
        t,
        ballistic_operation.acceleration,
        ballistic_operation.v,
        ballistic_operation.y,
        9.81,
    )

    performance_interactive_plot(ib_operation).show()


if __name__ == "__main__":
    main()
