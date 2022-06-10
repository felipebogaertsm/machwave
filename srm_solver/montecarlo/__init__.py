# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from dataclasses import dataclass
from typing import Any, Optional

import numpy as np

from simulations import Simulation


@dataclass
class MonteCarloParameter:
    """
    Stores a Monte Carlo parameter alongside its upper/lower bound.
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

    def __lt__(self, other: Any) -> bool:
        return self.value < other

    def __gt__(self, other: Any) -> bool:
        return self.value > other

    def __ge__(self, other: Any) -> bool:
        return self.value >= other

    def __le__(self, other: Any) -> bool:
        return self.value <= other

    def __add__(self, other: Any) -> float:
        try:
            return self.value + other.value
        except AttributeError:
            return self.value + other

    def __sub__(self, other: Any) -> float:
        try:
            return self.value - other.value
        except AttributeError:
            return self.value - other

    def __pow__(self, other: Any) -> float:
        return self.value ** other

    def __truediv__(self, other: Any) -> float:
        return self.value / other

    def __rmul__(self, other: Any) -> float:
        return self.value * other


class MonteCarloSimulation:
    """
    Stores, executes and presents data from a Monte Carlo simulation.
    """

    def __init__(
        self,
        parameters: list[Any],
        number_of_scenarios: int,
        simulation: Simulation,
    ) -> None:
        self.parameters = parameters
        self.number_of_scenarios = number_of_scenarios
        self.simulation = simulation

        self.scenarios: list[list[float | int]] = []

    def generate_scenario(self) -> list[float | int]:
        """
        Still need to implement recursive search of MonteCarloParameter
        instances.
        """

        new_scenario = []

        for parameter in self.parameters:
            if isinstance(parameter, MonteCarloParameter):
                parameter = parameter.get_random_value()
            else:
                try:
                    param = parameter
                    sub_params = vars(param)

                    i = 0

                    while True:
                        print(f"ITERATION NO #{i}")
                        new_sub_params = {}

                        if len(sub_params) == 0:
                            break

                        for name, attr in sub_params.items():
                            if isinstance(attr, MonteCarloParameter):
                                setattr(
                                    attr,
                                    name,
                                    attr.get_random_value(),
                                )
                            else:
                                new_sub_params += vars(attr)

                        sub_params = new_sub_params
                        i += 1

                except TypeError:
                    pass

            new_scenario.append(parameter)

        self.scenarios.append(new_scenario)
        return new_scenario

    def run(self) -> None:
        results = []

        for _ in range(self.number_of_scenarios):
            scenario = self.generate_scenario()
            results.append(self.simulation(*scenario).run())
            print("Apogee:", np.max(results[-1][2].y))

        return results
