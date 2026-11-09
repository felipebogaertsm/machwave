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

The free chamber volume is the volume of the chamber bore, inside the liner if there is one or the casing if there is none, over the chamber internal length, minus the volume of unburnt propellant.
Inhibitors belong to the grain rather than to the chamber, so an inhibitor sleeve between the grain and the bore wall is not subtracted and the annulus it occupies counts as free chamber volume.

Since the flow in the chamber is assumed quasi-stagnant (low Mach number), the adiabatic flame temperature is taken as the ideal chamber stagnation temperature.

The actual **flame temperature** $T$ is obtained from the **adiabatic flame temperature** $T_{0}$ and a **combustion efficiency** $\eta_{c^*}$.
The combustion efficiency accounts for incomplete combustion, heat losses and other losses in the chamber that make the delivered characteristic velocity lower than the ideal one.

In Machwave, $\eta_{c^*}$ is the **characteristic velocity efficiency**, the ratio of the delivered to the ideal characteristic velocity.
This is how the number is usually quoted in test reports and textbooks:

$$
\eta_{c^*} = \frac{c^*_\text{actual}}{c^*_\text{ideal}}, \qquad c^* = \frac{P_0 A_t}{\dot{m}} = \frac{\sqrt{R T}}{H_\text{choked}}
$$

(Huzel & Huang 1967, Eq. 1-41, p. 16, and Eq. 1-32 with the theoretical form below it, p. 12)

$A_t = C_d A_{t,\text{geo}}$ is the effective throat area and $H_\text{choked}$ is the choked flow function defined below.
A $c^*$ reduced from test data with the geometric throat area also carries the throat discharge loss.
Machwave models that loss separately through $C_d$, so a measured efficiency should not be applied on top of a $C_d$ below one without accounting for it.
Since $c^* \propto \sqrt{T}$ at fixed $R$ and $k$, the temperature ratio is the square of the efficiency:

$$
T = \eta_{c^*}^2 T_0
$$

For a choked chamber at a given mass flow and throat area, the chamber pressure and the delivered $c^*$ both scale by $\eta_{c^*}$.
Huzel & Huang (1967, p. 16) give 0.87 to 1.03 for this factor.
Machwave accepts values in (0, 1], and typical values depend mainly on the propellant combination and motor/engine size.
A unitary $\eta_{c^*}$ tends to overestimate the chamber pressure.

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
\dot{m}_{out} = \frac{C_d P_0 A_{t,\text{geo}}}{\sqrt{R T}}\, H
$$

where:

- $C_d$ is the throat discharge coefficient (dimensionless)
- $A_{t,\text{geo}}$ is the geometric nozzle throat area [m$^2$]
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
\frac{dP_0}{dt} = \frac{R T}{V_0}\left(\dot{m}_{in} - \frac{C_d P_0 A_{t,\text{geo}}}{\sqrt{R T}}\, H\right) - \frac{P_0}{V_0}\frac{dV_0}{dt}
$$

(Seidel 1965, Eq. 35)

This single differential equation is the foundation of all internal ballistics simulations in Machwave.
It is evaluated by [`compute_chamber_pressure_mass_balance`][machwave.core.mass_balance.compute_chamber_pressure_mass_balance].
The forms of $\dot{m}_{in}$ for each motor/engine category are derived in [Solid Rocket Motor](#solid-rocket-motor) and [Biliquid Rocket Engine](#biliquid-rocket-engine).

## Integrating the Chamber Pressure

The equation is integrated with the classical fourth-order Runge–Kutta method.
Each step evaluates the right-hand side at four intermediate pressures (stages), with both $\dot{m}_{in}$ and $\dot{m}_{out}$ evaluated at each stage pressure.

Near equilibrium, a pressure deviation decays as $e^{\lambda t}$, with $\lambda = \partial \dot{P}_0 / \partial P_0$.
With a choked nozzle and an inflow independent of $P_0$:

$$
\lambda = -\frac{1}{\tau}, \qquad \tau = \frac{L^*}{C_d H \sqrt{R T}}, \qquad L^* = \frac{V_0}{A_{t,\text{geo}}}
$$

where $\tau$ is the chamber residence time and $L^*$ the characteristic length.
A pressure-dependent inflow changes $\lambda$: for a solid motor with burn rate exponent $n$, $\lambda = -(1 - n)/\tau$ at equilibrium.
The decay time $1/|\lambda|$ is near 0.1 ms for a liquid engine with $L^*$ near 9 cm, and 1 to 2 ms for a solid motor whose chamber is mostly filled with propellant; both can be shorter than the simulation step.

One Runge–Kutta step of length $\Delta t$ multiplies the deviation by

$$
G(z) = 1 + z + \frac{z^2}{2} + \frac{z^3}{6} + \frac{z^4}{24}, \qquad z = \lambda \Delta t
$$

instead of the exact $e^{z}$.
At $z = -1$ the two agree closely (0.375 against 0.368).
Below $z \approx -1.3$ the last stage lands on the far side of equilibrium, where the nonlinear terms can drive the integration to a false steady state.
Below $z = -2.785$, $|G| > 1$ and the deviation grows every step.

Each simulation step is therefore split into $N$ equal substeps, so that $|\lambda| \Delta t / N \le 1$:

$$
N = \max\left(1, \left\lceil -\lambda \Delta t \right\rceil\right)
$$

with $\lambda$ estimated by central difference at the start of the step.
In a solid motor only the chamber pressure is substepped; grain geometry and propellant properties advance once per simulation step. A biliquid engine substeps its whole state, as described below.

Implemented in [`rk4th_ode_solver`][machwave.core.solvers.rk4th_ode_solver]; the substep count of each step is recorded in [`SimulationResult`][machwave.simulation.results.SimulationResult].

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

The chamber state $\{T_0, R, k_{chamber}, k_{exhaust}\}$ is evaluated by NASA-CEA from the chamber pressure, the design expansion ratio, and the instantaneous mixture ratio.

The chamber is not integrated on its own. Its pressure, the fluid mass $m_i$ of every line and the internal energy $U_j$ of every tank that runs an energy balance make one state vector, advanced together by the classical fourth-order Runge-Kutta method [4]:

$$
\frac{d}{dt}
\begin{pmatrix} P_0 \\ m_i \\ U_j \end{pmatrix}
=
\begin{pmatrix}
\dfrac{R T}{V_0}\left(\sum_i \dot{m}_i - \dot{m}_{out}\right) \\
-\dot{m}_i \\
-h_{out,j}\,\dot{m}_j - P_j\,\dfrac{dV_j}{dt}
\end{pmatrix}
$$

At every stage the tank state follows from the stage $(m, U)$, each line flow $\dot{m}_i$ is solved at the stage $P_0$ with its feedline loss, and CEA is read at the stage $P_0$ and mixture ratio, so the step is fourth order where the right-hand side is smooth. The chamber decay rate sets the number of substeps of the whole vector, as above.

Two things limit the order in practice:

- **Line depletion.** The step on which a line runs dry drains each line by its start-of-step flow, capped at what it holds, and is first order. The liquid-to-vapor switch in a tank is not located inside a step.
- **Thermochemistry quantization.** CEA results are cached on chamber pressure rounded to 200 Pa and mixture ratio rounded to $10^{-3}$, so $T$, $R$ and $k$ are piecewise constant in the state. This leaves an error of about $10^{-9}$ relative, the size of the truncation error at the default step, so refining the step past the default gains nothing.

Implemented in [`BiliquidEngineState`][machwave.simulation.biliquid.states.BiliquidEngineState].

# References

1. Seidel, H. H. (1965). *Transient Chamber Pressure and Thrust in Solid Rocket Motors*. Brown Engineering Company, Inc., Huntsville, AL (DTIC AD-613962).
2. Sutton, G. P., & Biblarz, O. (2001). *Rocket Propulsion Elements* (7th ed.). Wiley.
3. Huzel, D. K., & Huang, D. H. (1967). *Design of Liquid Propellant Rocket Engines* (2nd ed.). NASA SP-125. https://ntrs.nasa.gov/citations/19710019929
4. Hairer, E., Nørsett, S. P., & Wanner, G. (1993). *Solving Ordinary Differential Equations I: Nonstiff Problems* (2nd ed.). Springer Series in Computational Mathematics, Vol. 8. https://doi.org/10.1007/978-3-540-78862-1
