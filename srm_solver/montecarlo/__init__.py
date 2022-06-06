# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from dataclasses import dataclass
from typing import Optional

import numpy as np

from simulations import Simulation


@dataclass
class MonteCarloParameter:
    """
    Stores a Monte Carlo parameter alongside its uppser/lower bound.
    """

    value: float | int
    lower_tolerance: Optional[float | int] = 0
    upper_tolerance: Optional[float | int] = 0
    tolerance: Optional[float | int] = 0

    def get_random_value(self) -> float:
        return np.random.uniform(
            low=self.value - self.lower_tolerance - self.tolerance,
            high=self.value + self.upper_tolerance + self.tolerance,
        )


class MonteCarloSimulation:
    """
    Stores, executes and presents data from a Monte Carlo simulation.
    """

    def __init__(
        self,
        parameters: list[MonteCarloParameter],
        number_of_scenarios: int,
        simulation: Simulation,
    ) -> None:
        self.parameters = parameters
        self.number_of_scenarios = number_of_scenarios
        self.simulation = simulation

    def generate_scenario(self) -> list[float | int]:
        return [parameter.get_random_value() for parameter in self.parameters]

    def run(self) -> None:
        results = []

        for _ in range(self.number_of_scenarios):
            scenario = self.generate_scenario()
            results.append(self.simulation.run(*scenario))

        return results
