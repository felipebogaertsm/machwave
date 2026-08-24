# models.feed_systems.tank

Stateless two-phase propellant tank model backed by CoolProp. The `Tank` carries no propellant state: pressure and density are pure functions of the state supplied by the caller. `get_pressure(fluid_mass)` returns the tank pressure from two-phase equilibrium (saturation pressure while liquid is present, single-phase vapour from the real-gas equation of state otherwise), and `get_density(fluid_mass)` the density at current conditions.

A tank is isothermal by default: its temperature is held where it was loaded, so a self-pressurizing tank holds its saturation pressure flat for as long as any liquid remains. Passing `isothermal=False` runs an energy balance instead. The tank's internal energy then becomes a second state variable the integrator carries beside the mass, starting from `initial_internal_energy` and falling by the enthalpy of whatever drains out (`get_outflow_specific_enthalpy`), so the temperature and the saturation pressure decay over the burn. Every query on such a tank takes that internal energy alongside the mass, and says so when it is missing.

Tanks are identified by CoolProp fluid name (e.g., `"N2O"`, `"Oxygen"`, `"Hydrogen"`).

::: machwave.models.feed_systems.tank
