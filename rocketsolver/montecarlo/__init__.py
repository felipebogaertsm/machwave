# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np

from rocketsolver.simulations import Simulation
from rocketsolver.utils.utilities import obtain_attributes_from_object


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
        return self.value**other

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
        Generates a monte carlo scenario in the form of a list of parameters
        """

        new_scenario = []
        parameters = deepcopy(self.parameters)

        for parameter in parameters:
            if isinstance(parameter, MonteCarloParameter):
                parameter = parameter.get_random_value()
            else:
                search_tree = {
                    parameter: obtain_attributes_from_object(parameter)
                }
                i = 0

                while True:
                    new_search_tree = {}  # search tree for the next iteration

                    if len(search_tree) == 0:
                        break  # skip iteration if there are no sub params

                    for param, sub_params in search_tree.items():
                        for name, attr in sub_params.items():
                            if isinstance(attr, MonteCarloParameter):
                                setattr(param, name, attr.get_random_value())
                            elif isinstance(attr, list):
                                for item in attr:
                                    if isinstance(item, dict):
                                        continue

                                    new_search_tree = {
                                        **new_search_tree,
                                        **{
                                            item: obtain_attributes_from_object(
                                                item
                                            )
                                        },
                                    }
                            else:
                                new_search_tree = {
                                    **new_search_tree,
                                    **{
                                        attr: obtain_attributes_from_object(
                                            attr
                                        )
                                    },
                                }

                    search_tree = new_search_tree
                    i += 1

            new_scenario.append(parameter)

        self.scenarios.append(new_scenario)
        return new_scenario

    def run(self) -> None:
        self.results = []

        for _ in range(self.number_of_scenarios):
            scenario = self.generate_scenario()
            self.results.append(self.simulation(*scenario).run())

        return self.results
