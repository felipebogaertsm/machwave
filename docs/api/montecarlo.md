# Monte Carlo

Uncertainty and sensitivity analysis via Monte Carlo simulation. Wrap any motor parameter with `MonteCarloParameter` to assign a statistical distribution (normal or uniform) and spread. `MonteCarloSimulation` then generates N randomized scenarios, runs the internal ballistics for each, and provides statistical aggregates (mean, std, percentiles, skew, kurtosis) over the results.

Useful for characterizing thrust variability, pressure envelope, and impulse confidence intervals due to manufacturing tolerances and propellant batch variation.

::: machwave.montecarlo
