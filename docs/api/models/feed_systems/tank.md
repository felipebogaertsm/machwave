# models.feed_systems.tank

!!! note "Requires the `liquid` extra"
    `pip install machwave[liquid]`. Constructing a `Tank` without it raises an `ImportError` naming that command.

Stateless two-phase propellant tank model backed by CoolProp. The `Tank` carries no propellant state: pressure and density are pure functions of the state supplied by the caller. `get_pressure(fluid_mass, internal_energy)` returns the tank pressure from two-phase equilibrium (saturation pressure while liquid is present, single-phase vapour from the real-gas equation of state otherwise), and `get_density(fluid_mass, internal_energy)` the density at current conditions.

A tank runs an energy balance by default: its internal energy is a second state variable the integrator carries beside the mass, starting from `initial_internal_energy` and falling by the enthalpy of whatever drains out (`get_outflow_specific_enthalpy`). The tank cools as it drains and its saturation pressure decays over the burn. This is the equilibrium model of Zimmerman et al. (2013) without wall heat transfer. Every query on such a tank takes the internal energy alongside the mass, and says so when it is missing.

Passing `isothermal=True` holds the temperature where the tank was loaded, so a self-pressurizing tank holds its saturation pressure flat while any liquid remains. For a propellant such as N2O this over-predicts the feed pressure late in the burn.

Tanks are identified by CoolProp fluid name (e.g., `"N2O"`, `"Oxygen"`, `"Hydrogen"`).

**Reference.** Zimmerman, J. E., Waxman, B. S., Cantwell, B. J., & Zilliac, G. G. (2013). Review and Evaluation of Models for Self-Pressurizing Propellant Tank Dynamics. AIAA 2013-4045. [doi:10.2514/6.2013-4045](https://doi.org/10.2514/6.2013-4045)

::: machwave.models.feed_systems.tank
