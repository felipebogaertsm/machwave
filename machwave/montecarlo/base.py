import uuid
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

import numpy as np
import plotly.graph_objects as go

from machwave.montecarlo.random import get_random_generator
from machwave.services.common import obtain_attributes_from_object
from machwave.simulations import Simulation

SEARCH_TREE_DEPTH_LIMIT = 20


@dataclass
class MonteCarloParameter:
    """
    Stores a Monte Carlo parameter alongside its upper/lower bound.

    Args:
        value: Parameter main value
        lower_tolerance: Lower bound of the parameter
        upper_tolerance: Upper bound of the parameter
        tolerance: Tolerance of the parameter
        probability_distribution: Probability distribution of the random
            values. It can be set to 'uniform', 'normal' or any other
            distribution supported by the numpy.random module.
    """

    value: float | int
    lower_tolerance: float | int = 0
    upper_tolerance: float | int = 0
    tolerance: float | int = 0
    probability_distribution: str = "normal"

    def __post_init__(self) -> None:
        self.probability_distribution_class = get_random_generator(
            probability_distribution=self.probability_distribution,
            value=self.value,
            lower_tolerance=self.lower_tolerance,
            upper_tolerance=self.upper_tolerance,
            tolerance=self.tolerance,
        )

    def get_random_value(self) -> float:
        """
        Generates a random value for the parameter, according to the
        probability distribution and tolerances.

        Returns:
            Random value
        """
        return self.probability_distribution_class.get_value()

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
    The MonteCarloSimulation class:
    - Stores data for a Monte Carlo simulation
    - Executes the simulation
    - Presents distribution of results
    """

    def __init__(
        self,
        parameters: list[Any],
        number_of_scenarios: int,
        simulation: type[Simulation],
    ) -> None:
        """
        Initializes a MonteCarloSimulation object.

        Args:
            parameters: list with the input parameters for a simulation
                class instance.
            number_of_scenarios: Number of scenarios to be simulated.
            simulation: Simulation class instance.
        """
        self.parameters = parameters
        self.number_of_scenarios = number_of_scenarios
        self.simulation = simulation

        self.scenarios: list = []
        self.results: list = []

        self._object_store = dict()  # maps UUIDs to objects in generate_scenario

    def generate_scenario(self) -> list[Any]:
        """
        Generates a Monte Carlo scenario in the form of a list of parameters.

        These parameters are randomly generated within the tolerance bounds,
        set in the MonteCarloParameter class. The random numbers follow a
        Gaussian distribution.

        Returns:
            Monte Carlo scenario
        """
        new_scenario = []
        parameters_copy = deepcopy(self.parameters)

        for parameter in parameters_copy:
            if isinstance(parameter, MonteCarloParameter):
                parameter = parameter.get_random_value()
            else:  # search for MonteCarloParameter instances recursively
                self._process_nested_parameters(parameter)

            new_scenario.append(parameter)

        self.scenarios.append(new_scenario)
        return new_scenario

    def _process_nested_parameters(self, parameter: Any) -> None:
        """
        Recursively processes an object's attributes to replace
        MonteCarloParameter instances with randomized values and store objects
        using UUIDs.

        Args:
            parameter: The object whose attributes will be processed.
        """
        parameter_uuid = uuid.uuid4()
        self._object_store[parameter_uuid] = parameter
        search_tree = {parameter_uuid: obtain_attributes_from_object(parameter)}

        i = 0  # iteration counter

        while search_tree and i < SEARCH_TREE_DEPTH_LIMIT:
            i += 1
            new_search_tree = {}

            for param_uuid, sub_params in search_tree.items():
                param = self._object_store[param_uuid]

                for name, attr in sub_params.items():
                    object_uuid = uuid.uuid4()

                    if isinstance(attr, MonteCarloParameter):
                        setattr(param, name, attr.get_random_value())
                    elif isinstance(attr, list):
                        for item in attr:
                            if isinstance(item, dict):
                                continue

                            self._object_store[object_uuid] = item

                            new_search_tree[object_uuid] = (
                                obtain_attributes_from_object(item)
                            )
                    else:
                        object_uuid = uuid.uuid4()
                        self._object_store[object_uuid] = attr

                        new_search_tree[object_uuid] = obtain_attributes_from_object(
                            attr
                        )

            search_tree = new_search_tree

    def run(self) -> None:
        """
        Executes the Monte Carlo simulation.
        """
        self.results = []

        for _ in range(self.number_of_scenarios):
            scenario = self.generate_scenario()
            self.results.append(self.simulation(*scenario).run())

    def retrieve_values_from_result(
        self,
        operation_index: int,
        property: str,
    ) -> np.ndarray:
        """
        Retrieves a specific property from the simulation results.

        Args:
            operation_index: Index of the operation/result to retrieve the
                property from.
            property: Name of the property or the attribute of the operation
                to retrieve.

        Returns:
            Numpy array containing the values of the specified property.
        """
        return np.array(
            [getattr(result[operation_index], property) for result in self.results]
        )

    def plot_histogram(
        self,
        operation_index: int,
        property: str,
        x_axes_title: str = "x",
        *args,
        **kwargs,
    ) -> None:
        """
        Plots a histogram given a result index and the property name.

        Args:
            operation_index: Index of the operation/result to plot.
            property: Name of the property or the attribute of the operation
                to plot.
            x_axes_title: Title of the x axes. By default, the property name
                is used.
            *args: Additional arguments to pass to the histogram plot.
            **kwargs: Additional keyword arguments to pass to the histogram
                plot.
        """
        values = self.retrieve_values_from_result(
            operation_index=operation_index, property=property
        )

        fig = go.Figure()
        fig.add_trace(go.Histogram(x=values, *args, **kwargs))
        fig.update_xaxes(title_text=property or x_axes_title)

        fig.show()
