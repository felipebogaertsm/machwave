# Mass Balance

Machwave applies the **conservation of mass** to an open control volume (the combustion chamber).
This means that the rate of change of **mass stored** equals the difference between the **mass inflow** and the **mass outflow**:

$$
\frac{dM_{stored}}{dt} = \dot{m}_{in} - \dot{m}_{out}
$$

(Seidel 1965, Eq. 1)

This principle is applied to all chemical rocket motors/engines modeled in Machwave.
Among the three terms of the equation above, only $\dot{m}_{in}$ depends on the motor/engine category.

By applying the ideal gas law to $M_{stored}$, the mass balance can be rewritten in terms of the chamber stagnation state:

$$
M_{stored} = \rho_c V_0 = \frac{P_0 V_0}{R T}
$$

where:
- $\rho_c$ is the chamber gas density [kg/m$^3$]
- $P_0$ is the chamber stagnation pressure [Pa]
- $V_0$ is the free chamber volume [m$^3$]
- $R$ is the specific gas constant of the combustion products [J/(kg-K)]
- $T$ is the flame temperature [K]

Since the flow in the chamber is assumed quasi-stagnant (low Mach number), the adiabatic flame temperature is taken as the ideal chamber stagnation temperature.

The actual **flame temperature** $T$ is obtained by multiplying the **adiabatic flame temperature** $T_{0}$ by a **combustion efficiency** $\eta_{comb}$.
The combustion efficiency accounts for the fact that the actual flame temperature is often lower than the ideal adiabatic value due to incomplete combustion, heat losses or other inefficiencies in the combustion process.

In Machwave, $\eta_{comb}$ is defined as a *temperature* ratio, $\eta_{comb} = T / T_0$.
It should not be confused with the characteristic velocity efficiency $\eta_{c^*} = c^*_\text{actual} / c^*_\text{ideal}$ common in the literature, which relates to temperature as $\eta_{comb} = \eta_{c^*}^2$ (since $c^* \propto \sqrt{T}$).
Typical values for $\eta_{comb}$ range from 0.9 to 0.99, depending mainly on the propellant combination and motor/engine size.
A unitary $\eta_{comb}$ tends to overestimate the chamber pressure.

$$
T = \eta_{comb} T_0
$$

Substituting $M_{stored}$ into the mass balance and rearranging gives the general form of the chamber pressure differential equation:

$$
\frac{dP_0}{dt} = \frac{R T}{V_0}\left(\dot{m}_{in} - \dot{m}_{out}\right) - \frac{P_0}{V_0}\frac{dV_0}{dt}
$$

where:

- $P_0$ is the chamber stagnation pressure [Pa]
- $T$ is the flame temperature [K]
- $V_0$ is the free chamber volume [m$^3$]
- $R$ is the specific gas constant of the combustion products [J/(kg-K)]
- $\dot{m}_{in}$ is the mass inflow rate [kg/s]
- $\dot{m}_{out}$ is the nozzle mass exit rate [kg/s]

In differentiating $M_{stored} = P_0 V_0 / (R T)$, the gas constant $R$ and flame temperature $T$ are treated as constant in time, so that only $P_0$ and $V_0$ vary; the $dR/dt$ and $dT/dt$ contributions are neglected (Seidel 1965).

The mass outflow $\dot{m}_{out}$ is the flow through the nozzle throat and follows the same expression for every motor/engine category.
It is written compactly in terms of a dimensionless flow function $H$:

$$
\dot{m}_{out} = \frac{C_d P_0 A_t}{\sqrt{R T}}\, H
$$

where:

- $C_d$ is the throat discharge coefficient (dimensionless)
- $A_t$ is the nozzle throat area [m$^2$]
- $H$ is the dimensionless flow function, set by the throat regime

$H$ changes depending on the flow condition.
If the flow through the nozzle is **choked**, the sonic condition is reached at the throat and $H = H_{choked}$; if it is **subsonic**, $H = H_{sub}$.
Whether the flow is choked or subsonic is decided by the **critical pressure ratio** $P^*$: writing the back-pressure ratio as $P_r = P_\text{ext} / P_0$, the flow is **choked** when $P_r \leq P^*$ and **subsonic** otherwise.

$$
H_\text{choked} = \sqrt{k}\left(\frac{2}{k+1}\right)^{(k+1)/[2(k-1)]}
$$

$$
H_\text{sub} = \sqrt{\frac{2k}{k-1}}\,P_r^{1/k}\sqrt{1 - P_r^{(k-1)/k}}
$$

(Seidel 1965, Eqs. 19 and 20)

where:

- $k$ is the isentropic exponent of the combustion products, evaluated at chamber conditions — the chamber value, distinct from the exhaust value $k_e$ used for the thrust coefficient in [Thrust and Performance](thrust.md) (dimensionless)
- $P_r = P_\text{ext} / P_0$ is the back-pressure ratio, formed with the external (ambient) pressure $P_\text{ext}$ (dimensionless)
- $P^* = \left(\dfrac{2}{k+1}\right)^{k/(k-1)}$ is the critical pressure ratio (dimensionless)

A choked throat is the normal operating condition.
The subsonic branch matters mainly during ignition and tail-off, when the chamber pressure is close to the ambient pressure.

Substituting $\dot{m}_{out}$ leaves only $\dot{m}_{in}$ to be specified per category, giving the chamber-pressure differential equation for any motor/engine:

$$
\frac{dP_0}{dt} = \frac{R T}{V_0}\left(\dot{m}_{in} - \frac{C_d P_0 A_t}{\sqrt{R T}}\, H\right) - \frac{P_0}{V_0}\frac{dV_0}{dt}
$$

(Seidel 1965, Eq. 35)

This single differential equation is the foundation of all internal ballistics simulations in Machwave.
It is evaluated by [`compute_chamber_pressure_mass_balance`][machwave.core.mass_balance.compute_chamber_pressure_mass_balance] and integrated numerically with the fourth-order Runge–Kutta solver in [`machwave.core.solvers`][machwave.core.solvers].
Both source terms are evaluated at the chamber pressure of each Runge–Kutta stage: $\dot{m}_{out}$ is linear in $P_0$, and $\dot{m}_{in}$ carries the pressure dependence of the burn rate (solid motor) or of the injector pressure drop (biliquid engine), so the integrator advances the true coupled $(\dot{m}_{in} - \dot{m}_{out})$ slope instead of freezing the inflow at the start of the step.
The next sections derive the specific forms of $\dot{m}_{in}$ for different categories of motors/engines.

## Solid Rocket Motor

For a solid motor, the mass inflow is generated by the combustion of the solid propellant grain.
The grain burn rate $r$ is dependent on the chamber pressure and is modeled by Saint Robert's law:

$$
r = a P_0^n
$$

(Seidel 1965, Eq. 2)

where:

- $a$ is the burn rate coefficient [m/s/Pa$^n$]
- $n$ is the burn rate exponent (dimensionless)

The mass flow generated is dependent on $r$, the grain density $\rho_p$ (assumed constant per grain segment throughout time) and the instantaneous burn area $A_b$:

$$
\dot{m}_{in} = \rho_p\, r\, A_b
$$

(Seidel 1965, Eq. 3)

where:

- $\rho_p$ is the solid propellant density [kg/m$^3$]
- $r$ is the burn rate [m/s]
- $A_b$ is the instantaneous burn area [m$^2$]

As the propellant regresses, the solid phase recedes and the free chamber volume grows at the volumetric burn rate of the grain:

$$
\dot V_0 = r\, A_b
$$

Implemented in [`SolidMotorState`][machwave.simulation.solid.states.SolidMotorState].

## Biliquid Rocket Engine

For a biliquid engine, the mass inflow is set by the **injector mass flow** of two independent propellant streams.

The total inflow is the sum of the fuel and oxidiser injector streams:

$$
\dot{m}_{in} = \dot{m}_{fuel} + \dot{m}_{ox}
$$

The stream flows $\dot{m}_{fuel}$ and $\dot{m}_{ox}$ are supplied by the feed system implementation. The mass balance consumes only their sum. In addition, a biliquid engine has a rigid chamber ($\dot V_0 = 0$), so the free chamber volume term of the general ODE vanishes.

The chamber state $\{T_0, R, k_{chamber}, k_{exhaust}\}$ is evaluated by NASA-CEA at each step from the current $P_0$, the design expansion ratio, and the instantaneous mixture ratio.

Implemented in [`BiliquidEngineState`][machwave.simulation.biliquid.states.BiliquidEngineState].

# References

1. Seidel, H. H. (1965). *Transient Chamber Pressure and Thrust in Solid Rocket Motors*. Brown Engineering Company, Inc., Huntsville, AL (DTIC AD-613962).
2. Sutton, G. P., & Biblarz, O. (2001). *Rocket Propulsion Elements* (7th ed.). Wiley.
3. Huzel, D. K., & Huang, D. H. (1992). *Modern Engineering for Design of Liquid-Propellant Rocket Engines*. AIAA Progress in Astronautics and Aeronautics, Vol. 147.
