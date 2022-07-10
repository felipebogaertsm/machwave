# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import pandas as pd
from plotly import graph_objects as go
from plotly.subplots import make_subplots

from analytics import AnalyzeSRMOperation
from analytics.test_data.propulsion import SRMTestData
from models.recovery import Recovery
from models.rocket import Rocket
from models.recovery.events import (
    AltitudeBasedEvent,
    ApogeeBasedEvent,
)
from models.recovery.parachutes import HemisphericalParachute
from models.rocket.fuselage import Fuselage
from models.rocket.structure import RocketStructure
from models.atmosphere import Atmosphere1976
from operations.internal_ballistics import SRMOperation
from simulations.ballistics import BallisticSimulation


def main():
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

    # Read from CSV:
    df = pd.read_csv("example_data/hot_fire_olympus_1/test_data.csv")
    thrust = df["Force (N)"].to_numpy()
    time = df["Time (s)"].to_numpy()
    time = time - time[0]

    # IB coupled simulation:
    simulation = BallisticSimulation(
        thrust=thrust,
        initial_propellant_mass=19.84,
        motor_dry_mass=20.0,
        time=time,
        rocket=rocket,
        recovery=recovery,
        atmosphere=Atmosphere1976(),
        d_t=0.1,
        initial_elevation_amsl=600,
        igniter_pressure=1.5e6,
        rail_length=5,
    )

    (
        t,
        ballistic_operation,
    ) = simulation.run()

    simulation.print_results()

    # Analyze:
    test_data = SRMTestData(data=df, initial_propellant_mass=19.84)
    analyze = AnalyzeSRMOperation(
        operation=SRMOperation,
        simulation=simulation,
        test_data=test_data,
    )

    figure = make_subplots(specs=[[{"secondary_y": True}]])

    figure.add_trace(
        go.Line(x=test_data.get_time(), y=test_data.get_propellant_mass()),
        secondary_y=False,
    )
    figure.add_trace(
        go.Line(x=test_data.get_time(), y=test_data.get_thrust()),
        secondary_y=True,
    )

    figure.show()


if __name__ == "__main__":
    main()
