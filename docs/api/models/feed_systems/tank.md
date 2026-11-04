# models.feed_systems.tank

!!! note "Requires the `liquid` extra"
    `pip install machwave[liquid]`. Constructing a `Tank` without it raises an `ImportError` naming that command.

Stateless two-phase propellant tank model backed by CoolProp. The `Tank` carries no propellant state: pressure and density are pure functions of the state supplied by the caller. `get_pressure(fluid_mass, internal_energy)` returns the tank pressure from two-phase equilibrium (saturation pressure while liquid is present, single-phase vapour from the real-gas equation of state otherwise), and `get_density(fluid_mass, internal_energy)` the density at current conditions.

A tank runs an energy balance by default. Its internal energy is a second state variable the integrator carries beside the mass, starting from `initial_internal_energy` and falling by the enthalpy of whatever drains out (`get_outflow_specific_enthalpy`):

$$
\frac{dm}{dt} = -\dot{m}_{out}, \qquad \frac{dU}{dt} = -\dot{m}_{out} \, h_{out}
$$

The mass and internal energy fix the state through a CoolProp (D, U) flash, so the liquid boils to refill the ullage, the tank cools, and the saturation pressure decays over the burn. This is the equilibrium model of Zimmerman et al. (2013, Eqs. 20-23) without the wall heat transfer term. Every query on such a tank takes that internal energy alongside the mass, and says so when it is missing.

Passing `isothermal=True` holds the temperature where the tank was loaded instead, so a self-pressurizing tank holds its saturation pressure flat for as long as any liquid remains. That is a quick upper bound on the feed pressure, or a fair model of a tank held at temperature, but for a self-pressurizing propellant such as N2O it over-predicts the feed pressure and the thrust late in the burn.

A tank running the energy balance resolves its mass and internal energy through one CoolProp (D, U) flash per state (one `AbstractState` per tank, through `CoolPropService.get_state_at_density_internal_energy`). The flash is checked against the saturation curve and solved on the dome directly when CoolProp lands on a wrong state.

Tanks are identified by CoolProp fluid name (e.g., `"N2O"`, `"Oxygen"`, `"Hydrogen"`).

**Reference.** J. E. Zimmerman, B. S. Waxman, B. J. Cantwell and G. G. Zilliac, "Review and Evaluation of Models for Self-Pressurizing Propellant Tank Dynamics", AIAA 2013-4045, 49th AIAA/ASME/SAE/ASEE Joint Propulsion Conference, 2013. [doi:10.2514/6.2013-4045](https://doi.org/10.2514/6.2013-4045)

::: machwave.models.feed_systems.tank
