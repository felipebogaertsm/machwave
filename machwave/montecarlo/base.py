import uuid
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

import numpy as np
import plotly.graph_objects as go
from scipy import stats as scipy_stats

from machwave.common.generic import obtain_attributes_from_object
from machwave.montecarlo.random import get_random_generator
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
        state_index: int,
        property: str,
    ) -> np.ndarray:
        """
        Retrieves a specific property from the simulation results.

        Args:
            state_index: Index of the state/result to retrieve the
                property from.
            property: Name of the property or the attribute of the state
                to retrieve.

        Returns:
            Numpy array containing the values of the specified property.
        """
        return np.array(
            [getattr(result[state_index], property) for result in self.results]
        )

    def get_property_stats(self, state_index: int, property: str) -> dict[str, float]:
        """
        Calculates the mean, median, variance, and standard deviation
        of a specific property from the simulation results.

        Args:
            state_index (int): Index of the state/result to retrieve
                the property from.
            property (str): Name of the property or the attribute of the
                state to retrieve.

        Returns:
            dict[str, float]: A dictionary containing the mean, median,
                variance, and standard deviation of the specified
                property.
        """
        values = self.retrieve_values_from_result(
            state_index=state_index, property=property
        )

        return {
            "mean": float(np.mean(values)),
            "median": float(np.median(values)),
            "variance": float(np.var(values)),
            "std_dev": float(np.std(values)),
        }

    def plot_histogram(
        self,
        state_index: int,
        property: str,
        x_axes_title: str = "x",
        *args,
        **kwargs,
    ) -> None:
        """
        Plots a histogram given a result index and the property name.

        Args:
            state_index: Index of the state/result to plot.
            property: Name of the property or the attribute of the state
                to plot.
            x_axes_title: Title of the x axes. By default, the property name
                is used.
            *args: Additional arguments to pass to the histogram plot.
            **kwargs: Additional keyword arguments to pass to the histogram
                plot.
        """
        values = self.retrieve_values_from_result(
            state_index=state_index, property=property
        )

        fig = go.Figure()
        fig.add_trace(go.Histogram(x=values, *args, **kwargs))
        fig.update_xaxes(title_text=property or x_axes_title)

        fig.show()

    def plot_histogram_with_kde(
        self,
        state_index: int,
        property: str,
        x_axes_title: str = "x",
        nbins: int = 30,
        kde_points: int = 200,
        *args,
        **kwargs,
    ) -> None:
        """
        Plots a histogram with a Kernel Density Estimate (KDE) curve.

        Args:
            state_index: Index of the state/result to plot.
            property: Name of the property or the attribute of the state
                to plot.
            x_axes_title: Title of the x axes. By default, the property name
                is used.
            nbins: Number of bins for the histogram (default: 30).
            kde_points: Number of points for the KDE curve (default: 200).
            *args: Additional arguments to pass to the histogram plot.
            **kwargs: Additional keyword arguments to pass to the histogram
                plot.
        """
        values = self.retrieve_values_from_result(
            state_index=state_index, property=property
        )

        kde = scipy_stats.gaussian_kde(values)
        xs = np.linspace(values.min(), values.max(), kde_points)
        kde_vals = kde(xs)

        fig = go.Figure()
        fig.add_trace(
            go.Histogram(
                x=values,
                histnorm="probability density",
                nbinsx=nbins,
                opacity=0.5,
                name="Histogram",
                *args,
                **kwargs,
            )
        )
        fig.add_trace(
            go.Scatter(x=xs, y=kde_vals, mode="lines", name="KDE", line=dict(width=2))
        )
        fig.update_layout(
            xaxis_title=property or x_axes_title,
            yaxis_title="Density",
            title=f"Histogram + '{property}' KDE",
        )
        fig.show()

    def plot_cdf(
        self, state_index: int, property: str, x_axes_title: str = "x", *args, **kwargs
    ) -> None:
        """
        Plots the empirical cumulative distribution function (CDF) of a
        specific property from the simulation results.

        Args:
            state_index: Index of the state/result to plot.
            property: Name of the property or the attribute of the state
                to plot.
            x_axes_title: Title of the x axes. By default, the property name
                is used.
            *args: Additional arguments to pass to the CDF plot.
            **kwargs: Additional keyword arguments to pass to the CDF plot.
        """
        values = self.retrieve_values_from_result(
            state_index=state_index, property=property
        )

        sorted_vals = np.sort(values)
        cdf = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(x=sorted_vals, y=cdf, mode="lines", name="CDF", *args, **kwargs)
        )
        fig.update_layout(
            xaxis_title=property or x_axes_title,
            yaxis_title="Cummulative Probability",
            title=f"CDF of '{property}'",
        )
        fig.show()

    def plot_time_series_extremes(
        self,
        state_index: int,
        time_property: str,
        series_property: str,
        x_axes_title: str = "time",
        title: str | None = None,
        **plotly_kwargs,
    ) -> None:
        """
        Among all Monte Carlo scenarios, find:
          - the scenario whose series_property has the lowest mean;
          - the scenario whose series_property has the highest mean;
          - the scenario whose series_property has the median.

        Then plot those three curves against the longest time array,
        padding shorter series with NaN so that each stops where its
        data ends. Finally, shade between the min-mean and max-mean
        curves only where both have real data.

        Args:
            state_index: index into each simulation result that holds
                your object containing time/series.
            time_property: attribute name of the time array in that
                object.
            series_property: attribute name of the y(t) array in that
                object.
            x_axes_title: label for the x-axis.
            title: overall plot title.
            **plotly_kwargs: extra kwargs to pass into go.Scatter
                (e.g. line={"dash":"dash"}).
        """
        all_times = []
        all_series = []

        # 1. Gather every scenario’s raw time-series
        for sim_result in self.results:
            state_obj = sim_result[state_index]
            t = np.asarray(getattr(state_obj, time_property))  # e.g. state.time
            y = np.asarray(getattr(state_obj, series_property))  # e.g. state.thrust

            all_times.append(t)
            all_series.append(y)

        # 2. Identify the longest time array (highest length)
        lengths = [len(t) for t in all_times]
        idx_longest = int(np.argmax(lengths))
        common_time = all_times[idx_longest]
        Nmax = len(common_time)

        # 3. Pad each series array with np.nan out to Nmax
        padded_series = []
        for y in all_series:
            n = len(y)
            if n < Nmax:
                # create an array of length Nmax, fill first n entries with y, rest with nan
                padded = np.full(Nmax, np.nan, dtype=float)
                padded[:n] = y
                padded_series.append(padded)
            else:
                # already the longest (or equal), no padding needed
                padded_series.append(y.copy())

        series_mat = np.vstack(padded_series)  # shape = (n_scenarios, Nmax)

        # 4. Compute each scenario’s mean over its actual points (ignore NaN)
        means = np.nanmean(series_mat, axis=1)  # shape = (n_scenarios,)

        # 5. Find indices for lowest-mean, highest-mean, and closest-to-median
        i_min = int(np.nanargmin(means))
        i_max = int(np.nanargmax(means))

        median_of_means = np.median(means)
        i_med = int(np.nanargmin(np.abs(means - median_of_means)))

        y_min = series_mat[i_min]  # length = Nmax, but NaN beyond its real data
        y_med = series_mat[i_med]
        y_max = series_mat[i_max]

        # 6. Build Plotly figure
        fig = go.Figure()

        # Lowest-mean curve (no fill yet)
        fig.add_trace(
            go.Scatter(
                x=common_time,
                y=y_min,
                name="Lowest-mean scenario",
                line=dict(color="blue"),
                **plotly_kwargs,
            )
        )

        # Highest-mean curve, with fill down to the previous trace
        # (y_min), but beyond the overlap (where either is NaN),
        # Plotly will simply not draw.
        fig.add_trace(
            go.Scatter(
                x=common_time,
                y=y_max,
                name="Highest-mean scenario",
                line=dict(color="red"),
                fill="tonexty",
                **plotly_kwargs,
            )
        )

        # Median-mean curve on top
        fig.add_trace(
            go.Scatter(
                x=common_time,
                y=y_med,
                name="Median-mean scenario",
                line=dict(color="green", width=2, dash="dash"),
                **plotly_kwargs,
            )
        )

        fig.update_layout(
            xaxis_title=x_axes_title,
            yaxis_title=series_property,
            title=title
            or f"Extremes of '{series_property}' across {self.number_of_scenarios} scenarios",
        )

        fig.show()
