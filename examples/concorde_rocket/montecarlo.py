# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import numpy as np
import plotly.graph_objects as go

from rocketsolver.models.propulsion.grain import Grain
from rocketsolver.models.propulsion.grain.bates import BatesSegment
from rocketsolver.models.propulsion.structure import MotorStructure
from rocketsolver.models.propulsion.structure.nozzle import Nozzle
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

from rocketsolver.montecarlo import MonteCarloParameter, MonteCarloSimulation

from rocketsolver.simulations.internal_balistics_coupled import (
    InternalBallisticsCoupled,
)


def main():
    # Motor:
    propellant = get_solid_propellant_from_name(prop_name="KNSB-NAKKA")

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
        throat_diameter=MonteCarloParameter(value=37e-3, tolerance=0.5e-3),
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

    # Simulation:

    montecarlo_sim = MonteCarloSimulation(
        [
            motor,
            rocket,
            recovery,
            Atmosphere1976(),
            0.01,
            10,
            600,
            1.5e6,
            5,
        ],
        1000,
        InternalBallisticsCoupled,
    )

    results = montecarlo_sim.run()
    apogee_results = np.array([result[2].apogee for result in results])

    # Presentation:

    fig = go.Figure()
    fig.add_trace(go.Histogram(x=apogee_results))
    fig.update_xaxes(title_text="Apogee (m)")

    fig.show()


if __name__ == "__main__":
    main()
