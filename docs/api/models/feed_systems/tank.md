# models.feed_systems.tank

!!! note "Requires the `liquid` extra"
    `pip install machwave[liquid]`. Constructing a `Tank` without it raises an `ImportError` naming that command.

Stateless two-phase propellant tank model backed by CoolProp.
The `Tank` carries no propellant state.
Pressure and density are pure functions of the state supplied by the caller.
`get_pressure(fluid_mass, internal_energy)` returns the tank pressure from two-phase equilibrium.
That is the saturation pressure while liquid is present, and the vapor pressure from the real-gas equation of state otherwise.
`get_density(fluid_mass, internal_energy)` returns the density at current conditions.

A tank runs an energy balance by default.
Its internal energy is a second state variable that the integrator carries beside the mass.
The internal energy starts at `initial_internal_energy` and falls by the enthalpy of the fluid that drains out (`get_outflow_specific_enthalpy`).
The tank cools as it drains, and its saturation pressure falls over the burn.
This is the equilibrium model of Zimmerman et al. (2013) without wall heat transfer.
Every query on such a tank needs the internal energy as well as the mass, and raises a `ValueError` when it is missing.

Passing `isothermal=True` holds the temperature where the tank was loaded.
A self-pressurizing tank then holds its saturation pressure flat while any liquid remains.
For a propellant such as N2O this over-predicts the feed pressure late in the burn.

Tanks are identified by CoolProp fluid name (e.g., `"N2O"`, `"Oxygen"`, `"Hydrogen"`).

**Reference.** Zimmerman, J. E., Waxman, B. S., Cantwell, B. J., & Zilliac, G. G. (2013). Review and Evaluation of Models for Self-Pressurizing Propellant Tank Dynamics. AIAA 2013-4045. [doi:10.2514/6.2013-4045](https://doi.org/10.2514/6.2013-4045)

::: machwave.models.feed_systems.tank
