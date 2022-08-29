# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from dataclasses import dataclass
from typing import Optional

import numpy as np
import plotly.graph_objects as go

from .. import Analyze
from rocketsolver.models.atmosphere import Atmosphere
from rocketsolver.models.propulsion import MotorFromDataframe, SolidMotor
from rocketsolver.models.recovery import Recovery
from rocketsolver.models.rocket import Rocket
from rocketsolver.operations.ballistics._1dof import Ballistic1DOperation
from rocketsolver.simulations.ballistics import BallisticSimulation
from rocketsolver.simulations.internal_ballistics import InternalBallistics
from rocketsolver.utils.isentropic_flow import (
    get_total_impulse,
    get_specific_impulse,
    get_thrust_coefficient,
)
from rocketsolver.utils.math import get_percentage_error
from rocketsolver.utils.units import convert_mpa_to_pa, convert_pa_to_mpa
from rocketsolver.utils.geometric import get_circle_area
from rocketsolver.utils.utilities import generate_eng


@dataclass
class AnalyzeSRMOperation(Analyze):
    empirical_motor: MotorFromDataframe
    theoretical_motor: SolidMotor
    external_pressure: float

    thrust_header_name: Optional[str] = "Force (N)"
    time_header_name: Optional[str] = "Time (s)"
    pressure_header_name: Optional[str] = "Pressure (MPa)"

    igniter_pressure: Optional[float] = 1.5e6  # in Pa
    external_pressure: Optional[float] = 1e5  # in Pa
    simulation_resolution: Optional[float] = 0.01

    def __post_init__(self):
        self.ib_simulation = InternalBallistics(
            motor=self.theoretical_motor,
            d_t=self.simulation_resolution,
            igniter_pressure=self.igniter_pressure,
            external_pressure=self.external_pressure,
        )

        (
            self.theoretical_motor_time,
            self.theoretical_motor_operation,
        ) = self.ib_simulation.run()

    def run_ballistic_simulation(
        self,
        rocket: Rocket,
        recovery: Recovery,
        atmosphere: Atmosphere,
        d_t: float = 0.1,
        initial_elevation: float = 0.0,
        rail_length: float = 5.0,
    ) -> tuple[np.ndarray, Ballistic1DOperation]:
        self.ballistic_simulation = BallisticSimulation(
            thrust=self.empirical_motor.get_thrust(),
            initial_propellant_mass=self.empirical_motor.initial_propellant_mass,
            motor_dry_mass=self.theoretical_motor.structure.dry_mass,
            time=self.empirical_motor.get_time(),
            rocket=rocket,
            recovery=recovery,
            atmosphere=atmosphere,
            d_t=d_t,
            initial_elevation_amsl=initial_elevation,
            rail_length=rail_length,
        )

        (
            t,
            ballistic_operation,
        ) = self.ballistic_simulation.run()

        return (t, ballistic_operation)

    def get_tabular_comparison_body(self) -> list[list[str | float]]:
        parameters = [
            "Maximum thrust",
            "Maximum pressure",
            "Average thrust",
            "Average pressure",
            "Thrust time",
            "Total impulse",
            "Specific impulse",
        ]
        expected_values = np.array(
            [
                np.max(self.theoretical_motor_operation.thrust),
                np.max(self.theoretical_motor_operation.P_0) / 1e6,
                np.average(self.theoretical_motor_operation.thrust),
                np.average(self.theoretical_motor_operation.P_0) / 1e6,
                np.average(self.theoretical_motor_operation.thrust_time),
                np.average(self.theoretical_motor_operation.total_impulse),
                np.average(self.theoretical_motor_operation.specific_impulse),
            ]
        )
        obtained_values = np.array(
            [
                np.max(self.empirical_motor.get_thrust()),
                np.max(self.empirical_motor.get_pressure()) / 1e6,
                np.average(self.empirical_motor.get_thrust()),
                np.average(self.empirical_motor.get_pressure()) / 1e6,
                np.average(self.empirical_motor.thrust_time),
                np.average(self.empirical_motor.get_total_impulse()),
                np.average(self.empirical_motor.get_specific_impulse()),
            ]
        )
        units = [
            "N",
            "MPa",
            "N",
            "MPa",
            "s",
            "N-s",
            "s",
        ]

        percentage_error = get_percentage_error(
            expected_values, obtained_values
        )

        return [
            parameters,
            expected_values,
            obtained_values,
            units,
            percentage_error,
        ]

    def plot_tabular_comparison(self) -> go.Figure:
        figure = go.Figure()

        figure.add_trace(
            go.Table(
                header=dict(
                    values=[
                        "Parameter",
                        "Expected value",
                        "Obtained value",
                        "Unit",
                        "Percentage error",
                    ],
                    align="center",
                ),
                cells=dict(
                    values=self.get_tabular_comparison_body(),
                    align="center",
                    format=["", ".2f", ".2f", "", ".2f"],
                ),
            )
        )

        return figure

    def plot_thrust_propellant_mass(
        self,
        title: str = "SRM Hot-Fire Analysis",
        thrust_color: str = "#d62728",
        propellant_mass_color: str = "#1f77b4",
    ) -> go.Figure:
        figure = go.Figure()

        figure.add_trace(
            go.Scatter(
                x=self.empirical_motor.get_time(),
                y=self.empirical_motor.get_thrust(),
                name="Thrust (N)",
                yaxis="y",
                line=dict(color=thrust_color),
            ),
        )

        figure.add_trace(
            go.Scatter(
                x=self.empirical_motor.get_time(),
                y=self.empirical_motor.get_propellant_mass(),
                name="Est. propellant mass (kg)",
                yaxis="y2",
                line=dict(color=propellant_mass_color),
            ),
        )

        figure.update_xaxes(title_text="Time (s)")
        figure.update_layout(
            title_text=title,
            yaxis=dict(
                title="<b>Thrust</b> (N)",
                titlefont=dict(color=thrust_color),
                tickfont=dict(color=thrust_color),
            ),
            yaxis2=dict(
                title="<b>Propellant mass</b> (kg)",
                titlefont=dict(color=propellant_mass_color),
                tickfont=dict(color=propellant_mass_color),
                side="right",
                overlaying="y",
            ),
        )

        return figure

    def plot_pressure(
        self,
        title: str = "SRM Hot-Fire Analysis - Chamber Pressure",
        test_pressure_color: str = "#d62728",
        theoretical_pressure_color: str = "#1f77b4",
    ) -> go.Figure:
        figure = go.Figure()

        figure.add_trace(
            go.Scatter(
                x=self.empirical_motor.get_time(),
                y=convert_pa_to_mpa(self.empirical_motor.get_pressure()),
                name="Experimental data",
                line=dict(color=test_pressure_color),
            ),
        )

        figure.add_trace(
            go.Scatter(
                x=self.theoretical_motor_time,
                y=convert_pa_to_mpa(self.theoretical_motor_operation.P_0),
                name="Theoretical data",
                line=dict(color=theoretical_pressure_color),
            ),
        )

        figure.update_xaxes(title_text="Time (s)")
        figure.update_layout(
            title_text=title,
            yaxis=dict(title="<b>Chamber pressure</b> (MPa)"),
        )

        return figure

    def plot_pressure_thrust(
        self,
        title: str = "SRM Hot-Fire Analysis - Chamber Pressure and Thrust",
        thrust_color: str = "#d62728",
        pressure_color: str = "#1f77b4",
    ) -> go.Figure:
        figure = go.Figure()

        figure.add_trace(
            go.Scatter(
                x=self.empirical_motor.get_time(),
                y=self.empirical_motor.get_thrust(),
                name="Thrust (N)",
                yaxis="y",
                line=dict(color=thrust_color),
            ),
        )

        figure.add_trace(
            go.Scatter(
                x=self.empirical_motor.get_time(),
                y=self.empirical_motor.get_pressure(),
                name="Pressure (MPa)",
                yaxis="y2",
                line=dict(color=pressure_color),
            ),
        )

        figure.update_xaxes(title_text="Time (s)")
        figure.update_layout(
            title_text=title,
            yaxis=dict(
                title="<b>Thrust</b> (N)",
                titlefont=dict(color=thrust_color),
                tickfont=dict(color=thrust_color),
            ),
            yaxis2=dict(
                title="<b>Pressure</b> (Pa)",
                titlefont=dict(color=pressure_color),
                tickfont=dict(color=pressure_color),
                side="right",
                overlaying="y",
            ),
        )

        return figure

    def plot_thrust_coefficient(
        self, title: str = "SRM Hot-Fire Analysis - Thrust Coefficient"
    ) -> go.Figure:
        figure = go.Figure()

        figure.add_trace(
            go.Scatter(
                x=self.empirical_motor.get_time(),
                y=self.empirical_motor.get_thrust_coefficient(),
                name="Thrust coefficient",
            ),
        )

        figure.update_yaxes(title_text="<b>Thrust coefficient</b> (N)")
        figure.update_xaxes(title_text="Time (s)")
        figure.update_layout(title_text=title)

        return figure
