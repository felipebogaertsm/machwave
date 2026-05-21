import typing
import uuid
from copy import deepcopy
from dataclasses import dataclass

import numpy as np
import scipy.stats as scipy_stats

import machwave.common.objects as common_objects
import machwave.montecarlo.random as random
import machwave.services.plots.montecarlo as plot_service
import machwave.simulation as machwave_simulation

SEARCH_TREE_DEPTH_LIMIT = 20


@dataclass(init=False, slots=True)
class MonteCarloParameter(float):
    """Float value annotated with a distribution and spread for sampling."""

    _spread: float | tuple[float, float]
    _distribution: str

    def __new__(cls, value: float, *, spread=0.0, distribution="normal"):
        """Construct a parameter with a center value, spread, and distribution."""
        obj = float.__new__(cls, value)
        obj._spread = spread
        obj._distribution = distribution
        return obj

    @property
    def random_generator(self) -> random.RandomGenerator:
        """Return a generator that samples from this parameter's distribution."""
        return random.get_random_generator(
            self._distribution, float(self), self._spread
        )

    def get_random_value(self) -> float:
        """Sample a single random value from this parameter's distribution."""
        return self.random_generator.get_value()

    def __repr__(self) -> str:
        """Return a debugging representation of the parameter."""
        return (
            f"MonteCarloParameter({float(self):.6g}, spread={self._spread}, "
            f"dist='{self._distribution}')"
        )


class MonteCarloSimulation:
    """
    Monte Carlo driver that runs scenarios and stores their results.

    Stores parameters and simulation type, executes the configured number of
    scenarios, and delegates plotting to `plot_service.py`.
    """

    def __init__(
        self,
        parameters: list[typing.Any],
        number_of_scenarios: int,
        simulation: type[machwave_simulation.InternalBallisticsSimulation],
    ) -> None:
        """
        Initialize a Monte Carlo driver.

        Args:
            parameters: Input parameters for a simulation class.
            number_of_scenarios: Number of scenarios to simulate.
            simulation: Simulation class reference.
        """
        self.parameters = parameters
        self.number_of_scenarios = number_of_scenarios
        self.simulation = simulation

        self.scenarios: list = []
        self.results: list = []

        self._object_store = dict()  # for nested parameter processing

    def generate_scenario(self) -> list[typing.Any]:
        """Generates a Monte Carlo scenario in the form of a list of parameters."""
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
        Replace nested `MonteCarloParameter` instances with randomized values.

        Recursively walks the object's attributes; replacements are performed
        in place and intermediate objects are tracked using UUIDs.

        Args:
            parameter: Object whose attributes will be processed.
        """
        parameter_uuid = uuid.uuid4()
        self._object_store[parameter_uuid] = parameter
        search_tree = {parameter_uuid: common_objects.get_object_dict(parameter)}

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
                                common_objects.get_object_dict(item)
                            )
                    else:
                        object_uuid = uuid.uuid4()
                        self._object_store[object_uuid] = attr
                        new_search_tree[object_uuid] = common_objects.get_object_dict(
                            attr
                        )

            search_tree = new_search_tree

    def run(self) -> None:
        """Executes `number_of_scenarios` runs of the underlying Simulation."""
        self.results = []
        for _ in range(self.number_of_scenarios):
            scenario = self.generate_scenario()
            self.results.append(self.simulation(*scenario).run())

    def retrieve_values_from_result(self, property_name: str) -> np.ndarray:
        """
        Retrieve a scalar property across every Monte Carlo result.

        Args:
            property_name: Attribute name on the `SimulationResult`.

        Returns:
            Array of length `number_of_scenarios`.
        """
        return np.array(
            [getattr(sim_result, property_name) for sim_result in self.results]
        )

    def get_property_stats(self, property_name: str) -> dict[str, float]:
        """
        Return descriptive statistics for a scalar property across results.

        Metrics returned: mean, median, variance, std_dev, mode, skew (Fisher,
        unbiased), kurtosis (excess, unbiased), p5 (5th percentile), p95 (95th
        percentile).

        Args:
            property_name: Attribute name on the `SimulationResult`.

        Returns:
            Mapping of metric name to value.
        """
        values = np.asarray(self.retrieve_values_from_result(property_name))

        mean_val = np.mean(values)
        median_val = np.median(values)
        var_val = np.var(values)
        std_val = np.std(values)

        mode_val = float(scipy_stats.mode(values, nan_policy="omit").mode)
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
        property_name: str,
        x_axes_title: str = "x",
        **plotly_kwargs,
    ) -> None:
        """Plot a histogram of a scalar property across all results."""
        plot_service.plot_histogram(
            self.results, property_name, x_axes_title, **plotly_kwargs
        )

    def plot_histogram_with_kde(
        self,
        property_name: str,
        x_axes_title: str = "x",
        nbins: int = 30,
        kde_points: int = 200,
        **plotly_kwargs,
    ) -> None:
        """Plot a histogram of a scalar property with a KDE overlay."""
        plot_service.plot_histogram_with_kde(
            self.results,
            property_name,
            x_axes_title,
            nbins,
            kde_points,
            **plotly_kwargs,
        )

    def plot_cdf(
        self,
        property_name: str,
        x_axes_title: str = "x",
        **plotly_kwargs,
    ) -> None:
        """Plot the empirical CDF of a scalar property across all results."""
        plot_service.plot_cdf(
            self.results, property_name, x_axes_title, **plotly_kwargs
        )

    def plot_time_series_extremes(
        self,
        time_property: str,
        series_property: str,
        x_axes_title: str = "time",
        title: str | None = None,
        **plotly_kwargs,
    ) -> None:
        """Plot min and max envelopes of a time series across all results."""
        plot_service.plot_time_series_extremes(
            self.results,
            time_property,
            series_property,
            x_axes_title,
            title,
            **plotly_kwargs,
        )
