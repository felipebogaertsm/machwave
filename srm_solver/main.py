# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import fire
import time
import numpy as np
import json
from pathlib import Path

from models.motor.bates import Bates
from models.motor.structure import (
    BoltedCombustionChamber,
    MotorStructure,
    Nozzle,
)
from samples.propellants import get_propellant_from_name
from models.recovery import Recovery
from models.rocket import Rocket
from models.materials.metals import Steel
from srm_solver.models.materials.elastics import EPDM
from srm_solver.models.motor.thermals import ThermalLiner
from srm_solver.models.recovery.events import (
    AltitudeBasedEvent,
    ApogeeBasedEvent,
)
from srm_solver.models.recovery.parachutes import HemisphericalParachute
from srm_solver.models.rocket.fuselage import Fuselage
from srm_solver.models.rocket.structure import RocketStructure

from utils.utilities import output_eng_csv, print_results
from utils.plots import (
    performance_interactive_plot,
    performance_plot,
    main_plot,
    mass_flux_plot,
    ballistics_plots,
)

from simulations.internal_balistics_coupled import InternalBallisticsCoupled
from simulations.structural import StructuralSimulation


def main(from_json="input.json"):
    # /////////////////////////////////////////////////////////////////////////
    # TIME FUNCTION START
    # Starts the timer.

    start = time.time()

    # /////////////////////////////////////////////////////////////////////////
    # INPUTS
    # This section must be used to enter all the inputs for the script mode to be
    # executed.

    with open(Path(from_json)) as motor_input:
        data = json.load(motor_input)

    # Motor name (NO SPACES):
    name = data["motor"]["name"]
    # Motor manufacturer (NO SPACES):
    manufacturer = data["motor"]["manufacturer"]
    # Motor structural mass [kg]:
    motor_structural_mass = data["structure"]["mass"]

    # SIMULATION PARAMETERS INPUT
    # .eng file resolution:
    eng_res = data["simulationSettings"]["engResolution"]
    # Time step [s]:
    d_t = data["simulationSettings"]["dt"]
    # In order to optimize the speed of the program, the time step entered above is
    # multiplied by a factor 'dd_t' after the propellant is finished burning and
    # thrust produced is 0.
    dd_t = data["simulationSettings"]["ddt"]
    # Minimal safety factor:
    safety_factor = data["structure"]["safetyFactor"]

    # BATES PROPELLANT INPUT
    # Grain count:
    segment_count = data["grain"]["count"]
    # Grain external diameter [m]:
    grain_outer_diameter = data["grain"]["outerDiameter"]
    # Grains 1 to 'segment_count' core diameter [m]:
    grain_core_diameter = np.array(data["grain"]["coreDiameter"])
    # Grains 1 to 'segment_count' length [m]:
    segment_length = np.array(data["grain"]["length"])
    # Grain spacing (used to determine chamber length) [m]:
    grain_spacing = data["grain"]["spacing"]

    # PROPELLANT CHARACTERISTICS INPUT
    # Propellant name:
    propellant = data["propellant"]["name"]

    # THRUST CHAMBER
    # Casing inside diameter [m]:
    casing_inner_diameter = data["structure"]["casingInnerDiameter"]
    # Chamber outside diameter [m]:
    casing_outer_diameter = data["structure"]["casingOuterDiameter"]
    # Liner thickness [m]
    liner_thickness = data["structure"]["linerThickness"]
    # Throat diameter [m]:
    nozzle_throat_diameter = data["structure"]["nozzleThroatDiameter"]
    # Nozzle divergent and convergent angle [degrees]:
    divergent_angle = data["structure"]["nozzleDivergentAngle"]
    convergent_angle = data["structure"]["nozzleConvergentAngle"]
    # Expansion ratio:
    expansion_ratio = data["structure"]["expansionRatio"]
    # Nozzle materials heat properties 1 and 2 (page 87 of a015140):
    C1 = data["structure"]["casingC1"]
    C2 = data["structure"]["casingC2"]

    # EXTERNAL CONDITIONS
    # Igniter pressure [Pa]:
    igniter_pressure = data["simulationSettings"]["igniterPressure"]
    # Elevation above mean sea level [m]:
    initial_elevation_amsl = data["simulationSettings"]["initialAmslElevation"]

    # MECHANICAL DATA
    # Chamber yield strength [Pa]:
    casing_yield_strength = data["structure"]["casingYieldStrength"]
    # Bulkhead yield strength [Pa]:
    bulkhead_yield_strength = data["structure"]["bulkheadYieldStrength"]
    # Nozzle material yield strength [Pa]:
    nozzle_yield_strength = data["structure"]["nozzleYieldStrength"]

    # FASTENER DATA
    # Screw diameter (excluding threads) [m]:
    screw_diameter = data["structure"]["screwDiameter"]
    # Screw clearance hole diameter [m]:
    screw_clearance_diameter = data["structure"]["screwClearanceDiameter"]
    # Tensile strength of the screw [Pa]:
    screw_ultimate_strength = data["structure"]["screwUltimateStrength"]
    # Maximum number of fasteners:
    max_number_of_screws = data["structure"]["maxScrewCount"]

    # VEHICLE DATA
    # Mass of the rocket without the motor [kg]:
    mass_wo_motor = data["rocket"]["massWithoutMotor"]
    # Rocket drag coefficient:
    drag_coeff = data["rocket"]["dragCoeff"]
    # Frontal diameter [m]:
    rocket_outer_diameter = data["rocket"]["outerDiameter"]
    # Launch rail length [m]
    rail_length = data["simulationSettings"]["railLength"]
    # Time after apogee for drogue parachute activation [s]
    drogue_time = data["recovery"]["drogueTime"]
    # Drogue drag coefficient
    drag_coeff_drogue = data["recovery"]["drogueDragCoeff"]
    # Drogue effective diameter [m]
    drogue_diameter = data["recovery"]["drogueDiameter"]
    # Main parachute drag coefficient [m]
    drag_coeff_main = data["recovery"]["mainDragCoeff"]
    # Main parachute effective diameter [m]
    main_diameter = data["recovery"]["mainDiameter"]
    # Main parachute height activation [m]
    main_chute_activation_height = data["recovery"]["mainActivationHeight"]

    # /////////////////////////////////////////////////////////////////////////
    # PRE CALCULATIONS AND DEFINITIONS
    # This section is responsible for creating all of the instances of classes that
    # can be obtained from the input data.
    # It includes instanced of the classes: PropellantSelected, BATES,
    # MotorStructure, Rocket, Rocket and Recovery.
    # It also does some small calculations of the chamber length and chamber
    # diameter.

    # Motor:
    propellant_data = get_propellant_from_name(prop_name=propellant)

    grain = Bates(
        segment_count=segment_count,
        segment_spacing=10e-3,
        outer_diameter=grain_outer_diameter,
        core_diameter=grain_core_diameter,
        segment_length=segment_length,
    )

    nozzle = Nozzle(
        throat_diameter=nozzle_throat_diameter,
        divergent_angle=divergent_angle,
        convergent_angle=convergent_angle,
        expansion_ratio=expansion_ratio,
        material=Steel(),
    )

    liner = ThermalLiner(thickness=2e-3, material=EPDM())

    chamber = BoltedCombustionChamber(
        inner_diameter=casing_inner_diameter - 2 * liner_thickness,
        outer_diameter=casing_outer_diameter,
        liner=liner,
        length=grain.total_length,
        C1=0,
        C2=0,
        casing_material=Steel(),
        bulkhead_material=Steel(),
        screw_material=Steel(),
        max_screw_count=max_number_of_screws,
        screw_clearance_diameter=screw_clearance_diameter,
        screw_diameter=screw_diameter,
    )

    structure = MotorStructure(
        safety_factor=safety_factor,
        dry_mass=motor_structural_mass,
        nozzle=nozzle,
        chamber=chamber,
    )

    # Recovery:
    recovery = Recovery()
    recovery.add_event(
        ApogeeBasedEvent(
            trigger_value=1,
            parachute=HemisphericalParachute(diameter=drogue_diameter),
        )
    )
    recovery.add_event(
        AltitudeBasedEvent(
            trigger_value=450,
            parachute=HemisphericalParachute(diameter=main_diameter),
        )
    )

    # Rocket:
    fuselage = Fuselage(
        length=4e3,
        drag_coefficient=drag_coeff,
        outer_diameter=rocket_outer_diameter,
    )

    rocket_structure = RocketStructure(mass_without_motor=mass_wo_motor)

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

    ballistics, ib_parameters = InternalBallisticsCoupled(
        propellant=propellant_data,
        grain=grain,
        structure=structure,
        rocket=rocket,
        recovery=recovery,
        d_t=d_t,
        dd_t=dd_t,
        initial_elevation_amsl=initial_elevation_amsl,
        igniter_pressure=igniter_pressure,
        rail_length=rail_length,
    ).run()

    # /////////////////////////////////////////////////////////////////////////
    # MOTOR STRUCTURE
    # This section runs the structural simulation. The function
    # 'run_structural_simulation' returns an instance of the class
    # StructuralParameters.

    structural_parameters = StructuralSimulation(
        structure, ib_parameters.P0
    ).run()

    # /////////////////////////////////////////////////////////////////////////
    # RESULTS
    # This section prints the important data based on previous calculations.

    print_results(
        grain,
        structure,
        ib_parameters,
        structural_parameters,
        ballistics,
        rocket,
    )

    # /////////////////////////////////////////////////////////////////////////
    # OUTPUT TO ENG AND CSV FILE
    # This section exports the results inside a .csv and a .eng file. The .eng
    # file is totally compatible with OpenRocket or RASAero software. The .csv is
    # exported mainly for the ease of visualization and storage.

    output_eng_csv(
        ib_parameters,
        structure,
        propellant_data,
        25,
        d_t,
        manufacturer,
        name,
    )

    # /////////////////////////////////////////////////////////////////////////
    # TIME FUNCTION END
    # Ends the time function.

    print("Execution time: %.4f seconds\n\n" % (time.time() - start))

    # /////////////////////////////////////////////////////////////////////////
    # PLOTS
    # Saves some of the most important plots to the 'output' folder.

    performance_figure = performance_plot(
        ib_parameters.T,
        ib_parameters.P0,
        ib_parameters.t,
        ib_parameters.t_thrust,
    )
    main_figure = main_plot(
        ib_parameters.t,
        ib_parameters.T,
        ib_parameters.P0,
        ib_parameters.Kn,
        ib_parameters.m_prop,
        ib_parameters.t_thrust,
    )
    mass_flux_figure = mass_flux_plot(
        ib_parameters.t, ib_parameters.grain_mass_flux, ib_parameters.t_thrust
    )
    ballistics_plots(
        ballistics.t, ballistics.acc, ballistics.v, ballistics.y, 9.81
    )
    performance_interactive_plot(ib_parameters).show()


if __name__ == "__main__":
    fire.Fire(main)
