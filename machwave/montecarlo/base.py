import typing
import uuid
from copy import deepcopy
from dataclasses import dataclass

import numpy as np
import scipy.stats as scipy_stats

from machwave.common.generic import obtain_attributes_from_object
from machwave.montecarlo.random import get_random_generator
from machwave.services.plots import montecarlo as plot_service
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

    def __lt__(self, other: typing.Any) -> bool:
        return self.value < other

    def __gt__(self, other: typing.Any) -> bool:
        return self.value > other

    def __ge__(self, other: typing.Any) -> bool:
        return self.value >= other

    def __le__(self, other: typing.Any) -> bool:
        return self.value <= other

    def __add__(self, other: typing.Any) -> float:
        try:
            return self.value + other.value
        except AttributeError:
            return self.value + other

    def __sub__(self, other: typing.Any) -> float:
        try:
            return self.value - other.value
        except AttributeError:
            return self.value - other

    def __pow__(self, other: typing.Any) -> float:
        return self.value**other

    def __truediv__(self, other: typing.Any) -> float:
        return self.value / other

    def __rmul__(self, other: typing.Any) -> float:
        return self.value * other


class MonteCarloSimulation:
    """
    The MonteCarloSimulation class:
    - Stores data for a Monte Carlo simulation
    - Executes the simulation
    - Delegates plotting to `plot_service.py`
    """

    def __init__(
        self,
        parameters: list[typing.Any],
        number_of_scenarios: int,
        simulation: type[Simulation],
    ) -> None:
        """
        Initializes a MonteCarloSimulation object.

        Args:
            parameters: list with the input parameters for a simulation class.
            number_of_scenarios: Number of scenarios to be simulated.
            simulation: Simulation class reference.
        """
        self.parameters = parameters
        self.number_of_scenarios = number_of_scenarios
        self.simulation = simulation

        self.scenarios: list = []
        self.results: list = []

        self._object_store = dict()  # for nested parameter processing

    def generate_scenario(self) -> list[typing.Any]:
        """
        Generates a Monte Carlo scenario in the form of a list of parameters.
        """
        new_scenario = []
        parameters_copy = deepcopy(self.parameters)

        for parameter in parameters_copy:
            if isinstance(parameter, MonteCarloParameter):
                parameter = parameter.get_random_value()
            else:
                self._process_nested_parameters(parameter)

            new_scenario.append(parameter)

        self.scenarios.append(new_scenario)
        return new_scenario

    def _process_nested_parameters(self, parameter: typing.Any) -> None:
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

        i = 0
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
        Executes `number_of_scenarios` runs of the underlying Simulation.
        """
        self.results = []
        for _ in range(self.number_of_scenarios):
            scenario = self.generate_scenario()
            self.results.append(self.simulation(*scenario).run())

    def retrieve_values_from_result(
        self,
        state_index: int,
        property_name: str,
    ) -> np.ndarray:
        """
        Retrieves a specific scalar property from all simulation results.
        Returns a NumPy array of length = number_of_scenarios.

        Args:
            state_index: Index of the state in the simulation result.
            property_name: Name of the property to retrieve from the results.
        Returns:
            NumPy array containing the values of the specified property
            across all simulation results.
        """
        return np.array(
            [
                getattr(sim_result[state_index], property_name)
                for sim_result in self.results
            ]
        )

    def get_property_stats(
        self, state_index: int, property_name: str
    ) -> dict[str, float]:
        """
        Compute descriptive statistics for a scalar property across all results.

        Metrics returned:
        mean, median, variance, std_dev, mode, skew
        (Fishers, unbiased), kurtosis (excess, unbiased),
        p5 (5th percentile), p95 (95th percentile).

        Args:
            state_index: Index of the state in the simulation result.
            property_name: Name of the property to retrieve from the
                results.
        Returns:
            Dictionary containing the mean, median, variance, and
            standard deviation of the specified property across all
            simulation results.
        """
        values = np.asarray(
            self.retrieve_values_from_result(state_index, property_name)
        )

        mean_val = np.mean(values)
        median_val = np.median(values)
        var_val = np.var(values)
        std_val = np.std(values)

        mode_val = float(scipy_stats.mode(values, nan_policy="omit").mode[0])
        skew_val = scipy_stats.skew(values, bias=False)  # unbiased Fisher skew
        kurt_val = scipy_stats.kurtosis(values, fisher=True, bias=False)
        p5, p95 = np.percentile(values, [5, 95])

        return {
            "mean": float(mean_val),
            "median": float(median_val),
            "variance": float(var_val),
            "std_dev": float(std_val),
            "mode": float(mode_val),
            "skew": float(skew_val),
            "kurtosis": float(kurt_val),
            "p5": float(p5),
            "p95": float(p95),
        }

    def plot_histogram(
        self,
        state_index: int,
        property_name: str,
        x_axes_title: str = "x",
        **plotly_kwargs,
    ) -> None:
        plot_service.plot_histogram(
            self.results, state_index, property_name, x_axes_title, **plotly_kwargs
        )

    def plot_histogram_with_kde(
        self,
        state_index: int,
        property_name: str,
        x_axes_title: str = "x",
        nbins: int = 30,
        kde_points: int = 200,
        **plotly_kwargs,
    ) -> None:
        plot_service.plot_histogram_with_kde(
            self.results,
            state_index,
            property_name,
            x_axes_title,
            nbins,
            kde_points,
            **plotly_kwargs,
        )

    def plot_cdf(
        self,
        state_index: int,
        property_name: str,
        x_axes_title: str = "x",
        **plotly_kwargs,
    ) -> None:
        plot_service.plot_cdf(
            self.results, state_index, property_name, x_axes_title, **plotly_kwargs
        )

    def plot_time_series_extremes(
        self,
        state_index: int,
        time_property: str,
        series_property: str,
        x_axes_title: str = "time",
        title: str | None = None,
        **plotly_kwargs,
    ) -> None:
        plot_service.plot_time_series_extremes(
            self.results,
            state_index,
            time_property,
            series_property,
            x_axes_title,
            title,
            **plotly_kwargs,
        )
