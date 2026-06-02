# 2. Balance of Mass

The **conservation of mass** for an open control volume (the thrust chamber) states that the rate of change of **mass stored** equals the difference between the **mass in** and the **mass out**:

$$
\frac{dM_{stored}}{dt} = \dot{m}_{in} - \dot{m}_{out}
$$

(Seidel 1965, Eq. 1)

This principle is applied to all chemical rocket motors/engines modeled in Machwave. Among the 3 terms of the equation above, only $\dot{m}_{in}$ is dependent on the motor/engine category.

Treating the chamber contents as an ideal gas at uniform state:

$$
M_{stored} = \rho_c V_0 = \frac{P_0 V_0}{R T_0}
$$

Differentiating with $R T_0$ quasi-steady and allowing $V_0$ to vary (product rule on $P_0 V_0$):

$$
\frac{dM_{stored}}{dt} = \frac{1}{R T_0}\left(V_0 \frac{dP_0}{dt} + P_0 \frac{dV_0}{dt}\right)
$$

Substituting into the mass balance and solving for $dP_0/dt$ gives the chamber-pressure ODE:

$$
\frac{dP_0}{dt} = \frac{R T_0}{V_0}\left(\dot{m}_{in} - \dot{m}_{out}\right) - \frac{P_0}{V_0}\frac{dV_0}{dt}
$$

where:

- $P_0$ is the chamber stagnation pressure [Pa]
- $T_0$ is the chamber stagnation temperature [K]
- $V_0$ is the free chamber volume [m$^3$]
- $R$ is the specific gas constant of the combustion products [J/(kg·K)]
- $\dot{m}_{in}$ is the mass inflow rate [kg/s]
- $\dot{m}_{out}$ is the nozzle mass exit rate [kg/s]

The $-P_0\,\dot V_0/V_0$ term captures pressure decay due to free-volume expansion (e.g. grain regression in a solid motor, port growth in a hybrid). For a rigid control volume $\dot V_0 = 0$ and the expression reduces to $dP_0/dt = (R T_0/V_0)(\dot m_{in} - \dot m_{out})$.

This single ODE is the foundation of all internal-ballistics simulations in machwave. It is integrated numerically using the 4th-order Runge–Kutta solver in [`machwave.core.solvers`][machwave.core.solvers].

---

## 2.1 Solid Rocket Motor

For a solid motor, propellant regression exposes new surface at the **burn rate** $r$, so the inflow term is the mass generated per unit time:

$$
\dot{m}_{in} = \rho_p\, r\, A_b
$$

where:

- $\rho_p$ is the solid propellant density [kg/m$^3$]
- $r$ is the burn rate [m/s]
- $A_b$ is the instantaneous burn area [m$^2$]

This feeds the $\dot{m}_{in}$ argument of the unified [`compute_chamber_pressure_mass_balance`][machwave.core.mass_balance.compute_chamber_pressure_mass_balance].

When the nozzle is choked ($P_e/P_0 \leq P^*/P_0$; Sutton & Biblarz §3.3), the throat is sonic and the choked mass flow applies:

$$
\dot{m}_{out} = \frac{C_d P_0 A_t}{\sqrt{R T_0}}\,H_\text{choked},
\qquad
H_\text{choked} = \sqrt{k}\left(\frac{2}{k+1}\right)^{(k+1)/[2(k-1)]}
$$

where:

- $C_d$ is the throat discharge coefficient
- $A_t$ is the nozzle throat area [m$^2$]
- $k$ is the isentropic exponent of the combustion products

When $P_e/P_0 > P^*/P_0$ the throat is subsonic. Applying the isentropic energy equation and density relation (Sutton & Biblarz §3.3) between the stagnation state and the throat at back pressure $P_e$, with $P_r = P_e/P_0$:

$$
v_t = \sqrt{\frac{2k}{k-1}R T_0\left[1 - P_r^{(k-1)/k}\right]},
\qquad
\rho_t = \frac{P_0}{R T_0}P_r^{1/k}
$$

so the mass flow through the throat area $A_t$ becomes:

$$
\dot{m}_{out} = \rho_t\, v_t\, A_t = \frac{C_d P_0 A_t}{\sqrt{R T_0}}\,H_\text{sub},
\qquad
H_\text{sub} = \sqrt{\frac{2k}{k-1}}\,P_r^{1/k}\sqrt{1 - P_r^{(k-1)/k}}
$$

(Seidel 1965, Eq. 35)

As the propellant regresses, the free chamber volume grows at the rate the solid phase recedes — the volumetric burn rate of the grain:

$$
\dot V_0 = r\, A_b
$$

Substituting the inflow, exit-flow, and free-volume terms into the general balance gives the solid-motor ODE:

$$
\frac{dP_0}{dt} = \frac{R T_0}{V_0}\left(\rho_p r A_b - \frac{C_d P_0 A_t\, H}{\sqrt{R T_0}}\right) - \frac{P_0\, r A_b}{V_0}
$$

where $H$ is $H_\text{choked}$ or $H_\text{sub}$ depending on the throat regime. Evaluated by [`compute_chamber_pressure_mass_balance`][machwave.core.mass_balance.compute_chamber_pressure_mass_balance] with $\dot{m}_{in} = \rho_p r A_b$ and `free_chamber_volume_rate` $= r A_b$, as called from [`SolidMotorState`][machwave.simulation.solid.states.SolidMotorState]. The expansion term slightly lowers steady-state $P_0$ and total impulse relative to a rigid-volume model.

Separately, machwave applies a **combustion efficiency** $\eta_\text{comb}$ — the ratio of the actual to the ideal (adiabatic) flame temperature — directly to the flame temperature in the balance:

$$
\eta_\text{comb} = \frac{T_{0,\text{actual}}}{T_{0,\text{adiabatic}}},
\qquad
T_{0,\text{eff}} = \eta_\text{comb}\, T_{0,\text{adiabatic}}
$$

It derates the characteristic-velocity (choked-outflow) term and is not applied to the thrust coefficient $C_f$, which carries the nozzle losses of [nozzle losses](nozzle_losses.md). The characteristic velocity is $c^* = \sqrt{R T_0}/\Gamma$ with $\Gamma = \sqrt{k}\,(2/(k+1))^{(k+1)/[2(k-1)]}$, so $c^* \propto \sqrt{T_0}$ and the combustion efficiency is distinct from the characteristic-velocity efficiency $\eta_{c^*} = c^*_\text{actual}/c^*_\text{ideal}$:

$$
\eta_{c^*} = \sqrt{\eta_\text{comb}}, \qquad \eta_\text{comb} = \eta_{c^*}^{\,2}
$$

Applying $\eta_\text{comb}$ directly to $T_0$ follows the Nakka SRM spreadsheet convention. With Saint Robert's law $r = a P_0^n$ and $P_0 = (K_n \rho_p a\, c^*)^{1/(1-n)}$:

$$
P_0 \propto \eta_\text{comb}^{\,1/[2(1-n)]},
\qquad
I_{sp} \propto \eta_{c^*} = \sqrt{\eta_\text{comb}}
$$

$T_{0,\text{eff}}$ is computed by [`get_effective_flame_temperature`][machwave.core.performance.get_effective_flame_temperature] and passed as `flame_temperature` to [`compute_chamber_pressure_mass_balance`][machwave.core.mass_balance.compute_chamber_pressure_mass_balance] from [`SolidMotorState`][machwave.simulation.solid.states.SolidMotorState]. As the actual chamber-gas temperature, it enters both the outflow and storage terms of the solid-motor ODE.

---

## 2.2 Biliquid Rocket Engine

For a biliquid engine the inflow term is set not by surface regression but by the **injector mass flow** of two independent propellant streams; mass exits through the same choked throat as for the solid motor.

Each propellant stream is treated as an **incompressible fluid** flowing through an orifice from the upstream feed pressure $P_\text{up}$ to the chamber pressure $P_0$. Combining Bernoulli with continuity through an effective orifice area $A_\text{eff}$ and applying a discharge coefficient $C_d$ to lump together contraction and viscous losses gives (Huzel & Huang §4.5; Sutton & Biblarz §8.2):

$$
\dot{m} = C_d\,A_\text{eff}\,\sqrt{2\rho\,(P_\text{up} - P_0)}
$$

so the total inflow is the sum of the fuel and oxidiser streams:

$$
\dot{m}_{in} = \dot{m}_{fuel} + \dot{m}_{ox},
\qquad
\dot{m}_{i} = C_{d,i}\,A_{\text{eff},i}\,\sqrt{2\rho_i\,(P_{\text{up},i} - P_0)},
\quad i \in \{fuel, ox\}
$$

where:

- $A_\text{eff}$ is the effective orifice area [m$^2$]
- $P_\text{up}$ is the upstream feed pressure [Pa]
- $\rho$ is the propellant density [kg/m$^3$]

Implemented in `get_mass_flow_orifice` (module [`machwave.core.incompressible_flow`](../api/core.md)) and called per stream by the feed system. This single-phase incompressible branch is the default; self-pressurised propellants (e.g. nitrous oxide) can instead select a homogeneous-equilibrium two-phase model (`get_homogeneous_equilibrium_mass_flux` in `machwave.core.two_phase_flow`), which captures choking on the two-phase sound speed.

machwave currently models a **stacked-tank pressure-fed** architecture: a single pressurant volume above the oxidiser also drives the fuel via a piston, with a constant pressure drop $\Delta P_\text{piston}$ accounting for friction and piston weight (Huzel & Huang §5.2; Sutton & Biblarz §6.3). The injector upstream pressures are therefore:

$$
P_{\text{up},ox} = P_{\text{tank},ox},
\qquad
P_{\text{up},fuel} = P_{\text{tank},ox} - \Delta P_\text{piston}
$$

Each tank is modelled as a **two-phase isothermal vessel** (constant $T$, saturation pinning when liquid is present, ideal-gas vapour when only vapour remains; cf. Huzel & Huang Ch. 8). Properties come from CoolProp; details in [`Tank`][machwave.models.feed_systems.tank.Tank] and the orchestrating [`StackedTankPressureFedFeedSystem`][machwave.models.feed_systems.cycles.stacked_tank_pressure_fed.StackedTankPressureFedFeedSystem].

The injectors draw fuel and oxidiser independently, so a tank can be emptied within a single step. To keep tank masses non-negative, each stream is capped at the mass remaining in its own tank over the step $\Delta t$:

$$
\dot{m}_{fuel} \leftarrow \min\!\left(\dot{m}_{fuel},\, \frac{m_{fuel}}{\Delta t}\right),
\qquad
\dot{m}_{ox} \leftarrow \min\!\left(\dot{m}_{ox},\, \frac{m_{ox}}{\Delta t}\right)
$$

The two streams are clamped independently — the instantaneous mixture ratio $\mathrm{O\!/\!F} = \dot{m}_{ox}/\dot{m}_{fuel}$ is recomputed from the capped flows and passed to the thermochemistry, so a depleting tank simply drives the engine off its design ratio. The burn ends as soon as either tank is exhausted. Implemented in [`BiliquidEngineState`][machwave.simulation.biliquid.states.BiliquidEngineState].

The exit term is identical to the solid-motor choked-flow expression (Sutton & Biblarz §3.3), except the biliquid implementation drops the throat discharge coefficient ($C_d \equiv 1$) and uses the chamber-state isentropic exponent $k = k_\text{chamber}$:

$$
\dot{m}_{out} = \frac{P_0\, A_t}{\sqrt{R T_0}}\,\sqrt{k}\left(\frac{2}{k+1}\right)^{(k+1)/[2(k-1)]}
$$

Biliquid engines have a rigid combustion chamber ($\dot V_0 = 0$), so the free-volume term in the general balance vanishes. Substituting the injector inflow and choked-exit terms into it yields the biliquid form of the well-stirred reactor balance (Huzel & Huang §1.4; Sutton & Biblarz §8.1):

$$
\frac{dP_0}{dt} = \frac{R T_0}{V_0}\left[
  \dot{m}_{fuel} + \dot{m}_{ox}
  - \frac{P_0\,A_t}{\sqrt{R T_0}}\sqrt{k}\!\left(\frac{2}{k+1}\right)^{\!(k+1)/[2(k-1)]}
\right]
$$

Evaluated by the same [`compute_chamber_pressure_mass_balance`][machwave.core.mass_balance.compute_chamber_pressure_mass_balance] used for the solid motor — with $\dot{m}_{in} = \dot{m}_{fuel} + \dot{m}_{ox}$, $C_d = 1$, and chamber-state $\{T_0, R, k\}$ — and integrated with the same RK4 solver.

The thermochemical state $\{T_0, R, k\}$ is evaluated by NASA-CEA at each step from the current $P_0$, the design expansion ratio, and the instantaneous mixture ratio $\dot{m}_{ox}/\dot{m}_{fuel}$. The result is held constant within the RK4 sub-stages — an explicit lag that is acceptable because chamber properties are only weakly pressure-dependent (cf. Sutton & Biblarz §5.4). Before flow develops, the formulation's design O/F seeds the state; after one tank empties, the last evaluated properties are reused for the chamber-pressure decay.

The biliquid mass balance rests on several simplifying assumptions; keep these in mind when interpreting transient results:

- **Well-stirred reactor / instantaneous combustion.** Cold liquid propellant is assumed to burn to equilibrium products immediately upon entering the chamber. Atomisation, vaporisation, and finite reaction times are not resolved (Huzel & Huang Ch. 4; Sutton & Biblarz Ch. 9).
- **Uniform chamber state.** Pressure, temperature, and composition are spatially uniform — there is no $L^*$ effect, no residence-time penalty, and no chamber-cooling energy loss.
- **Constant $T_0$, constant $V_0$.** Flame temperature is the CEA equilibrium value at the *current* $P_0$ and design $\varepsilon$; free volume is fixed (no regenerative cooling-jacket displacement, no throat erosion).
- **Isothermal tank.** The two-phase model assumes constant tank temperature; the energy of vaporisation that would normally cool a self-pressurised tank during blowdown is **not** modelled (Huzel & Huang Ch. 8).
- **Bulk fluid density at the injector.** When the tank is two-phase, the orifice flow uses the bulk mixture density rather than the liquid saturation density — acceptable while the tank is mostly liquid, less accurate as it empties.
- **Burn ends at first depletion.** Each stream is capped at its remaining tank mass and the burn stops as soon as either tank empties; the fuel-rich (or oxidiser-rich) tail a real engine produces as one propellant runs out is not modelled (Sutton & Biblarz §6.1).

---

# References

1. Seidel, H. (1965). *Transient Chamber Pressure and Thrust in Solid Rocket Motors*. Air Force Rocket Propulsion Laboratory (AFRPL).
2. Sutton, G. P., & Biblarz, O. (2017). *Rocket Propulsion Elements* (9th ed.). Wiley.
3. Huzel, D. K., & Huang, D. H. (1992). *Modern Engineering for Design of Liquid-Propellant Rocket Engines*. AIAA Progress in Astronautics and Aeronautics, Vol. 147.
