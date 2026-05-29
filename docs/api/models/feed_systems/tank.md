# models.feed_systems.tank

Two-phase propellant tank model backed by CoolProp. The `Tank` class tracks fluid mass, computes tank pressure from two-phase thermodynamics (liquid + vapor equilibrium), and provides density at current conditions. Propellant is removed incrementally during simulation via `remove_propellant()`.

Tanks are identified by CoolProp fluid name (e.g., `"N2O"`, `"Oxygen"`, `"Hydrogen"`).

::: machwave.models.feed_systems.tank
