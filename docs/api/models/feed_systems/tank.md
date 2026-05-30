# models.feed_systems.tank

Stateless two-phase propellant tank model backed by CoolProp. The `Tank` carries no propellant-mass state: pressure and density are pure functions of a fluid mass supplied by the caller, so the integrator owns the mass and the model stays re-runnable. `get_pressure(fluid_mass)` returns the tank pressure from two-phase equilibrium (saturation pressure while liquid is present, ideal-gas vapour otherwise), and `get_density(fluid_mass)` the density at current conditions.

Tanks are identified by CoolProp fluid name (e.g., `"N2O"`, `"Oxygen"`, `"Hydrogen"`).

::: machwave.models.feed_systems.tank
