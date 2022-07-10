# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from dataclasses import dataclass

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .. import Analyze
from models.atmosphere import Atmosphere
from models.propulsion import SolidMotor
from models.recovery import Recovery
from models.rocket import Rocket
from operations.ballistics import Ballistic1DOperation
from simulations.ballistics import BallisticSimulation
from utils.isentropic_flow import get_total_impulse, get_specific_impulse


@dataclass
class AnalyzeSRMOperation(Analyze):
    initial_propellant_mass: float
    theoretical_motor: SolidMotor

    def get_thrust(self, col_name="Force (N)") -> np.ndarray:
        return self.get_from_df(col_name)

    def get_time(self, col_name="Time (s)") -> np.ndarray:
        return self.get_from_df(col_name)

    def get_pressure(self, col_name="Pressure (Pa)") -> np.ndarray:
        return self.get_from_df(col_name)

    def get_temperatures(
        self, col_name_startswith="Temperature"
    ) -> np.ndarray:
        """
        :param str col_name_startswith: The name that the column starts with
        :return: An array of temperatures captured by each thermopar.
        :rtype: np.ndarray
        """
        col_names = self.data.columns.values().tolist()
        temperature_col_names = [
            col_name
            for col_name in col_names
            if col_name.startswith(col_name_startswith)
        ]

        temperatures = np.array([])

        for name in temperature_col_names:
            temperatures = np.append(temperatures, self.get_from_df(name))

        return temperatures

    def get_total_impulse(self) -> float:
        return get_total_impulse(
            np.average(self.get_thrust()), self.get_time()[-1]
        )

    def get_specific_impulse(self) -> float:
        return get_specific_impulse(
            self.get_total_impulse(), self.initial_propellant_mass
        )

    def get_instantaneous_propellant_mass(self, t: float) -> float:
        """
        IMPORTANT NOTE: this method is only an estimation of the propellant
        mass during the operation of the motor. It assumes a constant nozzle
        efficiency throughout the operation and perfect correlation between
        thrust and pressure data.

        :param float t: The time at which the propellant mass is desired
        :return: The propellant mass at time t
        :rtype: np.ndarray
        """
        t_index = np.where(self.get_time() == t)[0][0]

        time = self.get_time()[t_index:-1]
        thrust = self.get_thrust()[t_index:-1]

        return (
            np.trapz(y=thrust, x=time) / self.get_total_impulse()
        ) * self.initial_propellant_mass

    def get_propellant_mass(self) -> np.ndarray:
        """
        Calculates propellant mass for each instant and appends in an array.

        :return: The propellant mass at each time step
        :rtype: np.ndarray
        """
        return np.array(
            list(
                map(
                    lambda time: self.get_instantaneous_propellant_mass(time),
                    self.get_time(),
                )
            )
        )

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
            thrust=self.get_thrust(),
            initial_propellant_mass=self.initial_propellant_mass,
            motor_dry_mass=self.theoretical_motor.structure.dry_mass,
            time=self.get_time(),
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

    def plot_thrust_propellant_mass(
        self,
        title: str = "SRM Hot-Fire Analysis",
        thrust_color: str = "#d62728",
        propellant_mass_color: str = "#1f77b4",
    ) -> go.Figure:
        figure = go.Figure()

        figure.add_trace(
            go.Scatter(
                x=self.get_time(),
                y=self.get_thrust(),
                name="Thrust (N)",
                yaxis="y",
                line=dict(color=thrust_color),
            ),
        )

        figure.add_trace(
            go.Scatter(
                x=self.get_time(),
                y=self.get_propellant_mass(),
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
