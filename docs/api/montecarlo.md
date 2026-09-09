# Monte Carlo

Uncertainty and sensitivity analysis via Monte Carlo simulation. Wrap any motor parameter with `MonteCarloParameter` to assign a statistical distribution (normal or uniform) and spread. `MonteCarloSimulation` then generates N randomized scenarios, runs the internal ballistics for each, and provides statistical aggregates (mean, std, percentiles, skew, kurtosis) over the results.

Useful for characterizing thrust variability, pressure envelope, and impulse confidence intervals due to manufacturing tolerances and propellant batch variation.

!!! note "Plotting requires the `plots` extra"
    Running a Monte Carlo simulation and reading its aggregates needs no extra. Only `plot_histogram`, `plot_histogram_with_kde`, `plot_cdf` and `plot_time_series_extremes` do: `pip install machwave[plots]`.

::: machwave.montecarlo
