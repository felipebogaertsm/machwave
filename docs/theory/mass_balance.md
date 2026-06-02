# 2. Balance of Mass

## 2.1 General Chamber Mass Balance

The **conservation of mass** for an open control volume (the rocket chamber) states
that the rate of change of **mass stored** equals the difference between **mass
generated** and **mass out**:

\[
\frac{dM_{stored}}{dt} = \dot{m}_{gen} - \dot{m}_{out}
\]

Treating the chamber contents as an ideal gas at uniform state (pressure \(P_0\),
temperature \(T_0\), volume \(V_0\)):

\[
M_{stored} = \rho_c V_0 = \frac{P_0 V_0}{R T_0}
\]

Differentiating with \(R T_0\) quasi-steady and allowing \(V_0\) to vary
(product rule on \(P_0 V_0\)):

\[
\frac{dM_{stored}}{dt} = \frac{1}{R T_0}\left(V_0 \frac{dP_0}{dt} + P_0 \frac{dV_0}{dt}\right)
\]

Substituting into the mass balance and solving for \(dP_0/dt\):

\[
\boxed{\frac{dP_0}{dt} = \frac{R T_0}{V_0}\left(\dot{m}_{gen} - \dot{m}_{out}\right) - \frac{P_0}{V_0}\frac{dV_0}{dt}}
\]

The \(-P_0\,\dot V_0/V_0\) term captures pressure decay due to free-volume
expansion (e.g. grain regression in a solid motor, port growth in a hybrid). For a
rigid control volume \(\dot V_0 = 0\) and the expression reduces to
\(dP_0/dt = (R T_0/V_0)(\dot m_{gen} - \dot m_{out})\).

This single ODE is the foundation of all internal-ballistics simulations in machwave.
It is integrated numerically using the 4th-order Runge–Kutta solver in
[`machwave.core.solvers`][machwave.core.solvers].

---

## 2.2 Solid Rocket Motor

*Reference: Seidel, H. (1965). Transient Chamber Pressure and Thrust in Solid Rocket
Motors. AFRPL.*

### 2.2.1 Mass Generation Rate

Propellant regression exposes new surface at the **burn rate** \(r\) [m/s]. The
mass generated per unit time is:

\[
\dot{m}_{gen} = \rho_p \cdot r \cdot A_b
\]

where \(\rho_p\) is the solid propellant density and \(A_b\) is the instantaneous
burn area. This feeds the \(\dot{m}_{in}\) argument of the unified
[`compute_chamber_pressure_mass_balance`][machwave.core.mass_balance.compute_chamber_pressure_mass_balance].

### 2.2.2 Mass Exit Rate — Choked Flow

When the nozzle is choked (\(P_e / P_0 \leq P^*/P_0\), see §1.4), the throat is
sonic and the choked mass flow from §1.7 applies:

\[
\dot{m}_{exit} = \frac{C_d P_0 A_t}{\sqrt{R T_0}}\,H_\text{choked},
\qquad
H_\text{choked} = \sqrt{k}\left(\frac{2}{k+1}\right)^{(k+1)/[2(k-1)]}
\]

### 2.2.3 Mass Exit Rate — Sub-critical Flow

When \(P_e / P_0 > P^*/P_0\) the throat is subsonic. Applying the isentropic
energy equation (§1.1) and density relation (§1.3) between the stagnation state
and the throat at back pressure \(P_e\), with \(P_r = P_e/P_0\):

\[
v_t = \sqrt{\frac{2k}{k-1}R T_0\left[1 - P_r^{(k-1)/k}\right]},
\qquad
\rho_t = \frac{P_0}{R T_0}P_r^{1/k}
\]

Mass flow through the throat area \(A_t\):

\[
\dot{m}_{exit} = \rho_t\, v_t\, A_t
= \frac{C_d P_0 A_t}{\sqrt{R T_0}}\,H_\text{sub},
\qquad
H_\text{sub} = \sqrt{\frac{2k}{k-1}}\,P_r^{1/k}\sqrt{1 - P_r^{(k-1)/k}}
\]

(Seidel 1965, Eq. 35.)

### 2.2.4 Free-Volume Expansion Rate

As propellant regresses, the free chamber volume grows at the rate the solid
phase recedes:

\[
\dot V_0 = r \cdot A_b
\]

i.e. the volumetric burn rate of the grain. This is passed to the ODE as the
\(\dot V_0\) term in §2.1.

### 2.2.5 Solid-Motor ODE

Substituting §2.2.1, §2.2.2–§2.2.3, and §2.2.4 into §2.1:

\[
\boxed{\frac{dP_0}{dt} = \frac{R T_0}{V_0}\left(\rho_p r A_b - \frac{C_d P_0 A_t\, H}{\sqrt{R T_0}}\right) - \frac{P_0\, r A_b}{V_0}}
\]

Evaluated by
[`compute_chamber_pressure_mass_balance`][machwave.core.mass_balance.compute_chamber_pressure_mass_balance]
with \(\dot{m}_{in} = \rho_p r A_b\) and `free_chamber_volume_rate` \(= r A_b\),
as called from
[`SolidMotorState`][machwave.simulation.solid.states.SolidMotorState]. The
expansion term slightly lowers steady-state \(P_0\) and total impulse relative to
a rigid-volume model.

### 2.2.6 Combustion Efficiency

*Reference: Sutton & Biblarz (2017), Ch. 3.*

The **combustion efficiency** \(\eta_\text{comb}\) is the ratio of the actual to the
ideal (adiabatic) flame temperature, stored per propellant and applied directly to
the flame temperature in the chamber-pressure balance:

\[
\eta_\text{comb} = \frac{T_{0,\text{actual}}}{T_{0,\text{adiabatic}}},
\qquad
T_{0,\text{eff}} = \eta_\text{comb}\, T_{0,\text{adiabatic}}.
\]

It derates the characteristic-velocity (choked-outflow) term of §2.2.2 and is not
applied to the thrust coefficient \(C_F\), which carries the nozzle losses of
[nozzle losses](nozzle_losses.md).

Characteristic velocity is \(c^* = \sqrt{R T_0}/\Gamma\) with
\(\Gamma = \sqrt{k}\,(2/(k+1))^{(k+1)/[2(k-1)]}\), so \(c^* \propto \sqrt{T_0}\). The
combustion efficiency is therefore distinct from the characteristic-velocity
efficiency \(\eta_{c^*} = c^*_\text{actual}/c^*_\text{ideal}\):

\[
\eta_{c^*} = \sqrt{\eta_\text{comb}}, \qquad \eta_\text{comb} = \eta_{c^*}^{\,2}.
\]

Applying \(\eta_\text{comb}\) directly to \(T_0\) follows the Nakka SRM spreadsheet
convention. With Saint Robert's law \(r = a P_0^n\) and
\(P_0 = (K_n \rho_p a\, c^*)^{1/(1-n)}\):

\[
P_0 \propto \eta_\text{comb}^{\,1/[2(1-n)]},
\qquad
I_{sp} \propto \eta_{c^*} = \sqrt{\eta_\text{comb}}.
\]

\(T_{0,\text{eff}}\) is computed by
[`get_effective_flame_temperature`][machwave.core.performance.get_effective_flame_temperature]
and passed as `flame_temperature` to
[`compute_chamber_pressure_mass_balance`][machwave.core.mass_balance.compute_chamber_pressure_mass_balance]
from [`SolidMotorState`][machwave.simulation.solid.states.SolidMotorState]. As the
actual chamber-gas temperature, it is used in both the outflow and storage terms of
the §2.2.5 ODE.

---

## 2.3 Biliquid Rocket Engine

*References: Sutton & Biblarz (2017), Ch. 6; Huzel & Huang (1992), Ch. 1, 4, 7.*

For a biliquid engine the mass-generation term is no longer set by surface
regression but by the **injector mass flow** of two independent propellant
streams. Mass exits through the same choked throat as in §2.2.2.

### 2.3.1 Mass Inflow Rate — Injector

*References: Sutton & Biblarz (2017) Ch. 8 (Thrust Chambers — Injectors);
Huzel & Huang (1992) Ch. 4 §4.5 (Injector Design).*

Each propellant stream is treated as an **incompressible fluid** flowing through an
orifice from the upstream feed pressure \(P_\text{up}\) to the chamber pressure
\(P_0\). Combining Bernoulli with continuity through an effective orifice area
\(A_\text{eff}\) and applying a discharge coefficient \(C_d\) to lump together
contraction and viscous losses gives (Huzel & Huang §4.5; Sutton & Biblarz §8.2):

\[
\boxed{\dot{m} = C_d\,A_\text{eff}\,\sqrt{2\rho\,(P_\text{up} - P_0)}}
\]

The total inflow is the sum of the fuel and oxidiser streams:

\[
\dot{m}_{gen} = \dot{m}_{fuel} + \dot{m}_{ox},
\qquad
\dot{m}_{i} = C_{d,i}\,A_{\text{eff},i}\,\sqrt{2\rho_i\,(P_{\text{up},i} - P_0)},
\quad i \in \{fuel, ox\}.
\]

Implemented in `get_mass_flow_orifice` (module
[`machwave.core.incompressible_flow`](../api/core.md)) and called per stream by the
feed system (see §2.3.2). This single-phase incompressible branch is the default;
self-pressurised propellants (e.g. nitrous oxide) can instead select a
homogeneous-equilibrium two-phase model (`get_homogeneous_equilibrium_mass_flux` in
`machwave.core.two_phase_flow`), which captures choking on the two-phase sound speed.

### 2.3.2 Upstream Pressure — Pressurised Tank

*References: Sutton & Biblarz (2017) Ch. 6 §6.3 (Propellant Feed Systems);
Huzel & Huang (1992) Ch. 5 (Gas-Pressurized Feed Systems) and Ch. 8 (Propellant
Tanks).*

machwave currently models a **stacked-tank pressure-fed** architecture: a single
pressurant volume above the oxidiser also drives the fuel via a piston, with a
constant pressure drop \(\Delta P_\text{piston}\) accounting for friction and
piston weight (Huzel & Huang §5.2; Sutton & Biblarz §6.3). The injector upstream
pressures are therefore:

\[
P_{\text{up},ox} = P_{\text{tank},ox},
\qquad
P_{\text{up},fuel} = P_{\text{tank},ox} - \Delta P_\text{piston}.
\]

Each tank is modelled as a **two-phase isothermal vessel** (constant \(T\), saturation
pinning when liquid is present, ideal-gas vapour when only vapour remains; cf. Huzel &
Huang Ch. 8 for tank thermodynamics). Properties come from CoolProp; details in
[`Tank`][machwave.models.feed_systems.tank.Tank] and the orchestrating
[`StackedTankPressureFedFeedSystem`][machwave.models.feed_systems.cycles.stacked_tank_pressure_fed.StackedTankPressureFedFeedSystem].

### 2.3.3 Propellant Depletion

The injectors draw fuel and oxidiser independently, so a tank can be emptied within a
single step. To keep tank masses non-negative, each stream is capped at the mass
remaining in its own tank over the step \(\Delta t\):

\[
\dot{m}_{fuel} \leftarrow \min\!\left(\dot{m}_{fuel},\, \frac{m_{fuel}}{\Delta t}\right),
\qquad
\dot{m}_{ox} \leftarrow \min\!\left(\dot{m}_{ox},\, \frac{m_{ox}}{\Delta t}\right).
\]

The two streams are clamped independently — the instantaneous mixture ratio
\(\mathrm{O\!/\!F} = \dot{m}_{ox}/\dot{m}_{fuel}\) is recomputed from the capped flows
and passed to the thermochemistry, so a depleting tank simply drives the engine off
its design ratio. The burn ends as soon as either tank is exhausted. Implemented in
[`BiliquidEngineState`][machwave.simulation.biliquid.states.BiliquidEngineState].

### 2.3.4 Mass Exit Rate — Choked Throat

*References: Sutton & Biblarz (2017) Ch. 3 §3.3 (Isentropic Flow through Nozzles);
Huzel & Huang (1992) Ch. 1 §1.4 (The Gas-Flow Processes).*

The exit term is identical to §2.2.2 — the choked-flow expression derived in §1.7
(Sutton & Biblarz §3.3). For the biliquid engine the implementation drops the throat
discharge coefficient (\(C_d \equiv 1\)) and uses the chamber-state isentropic
exponent \(k = k_\text{chamber}\):

\[
\dot{m}_{out} = \frac{P_0\, A_t}{\sqrt{R T_0}}\,\sqrt{k}\left(\frac{2}{k+1}\right)^{(k+1)/[2(k-1)]}.
\]

### 2.3.5 Biliquid Chamber-Pressure ODE

*References: Huzel & Huang (1992) Ch. 1 §1.4 and Ch. 4 §4.1 (Combustion-Chamber
Processes); Sutton & Biblarz (2017) Ch. 8 §8.1 (Combustion Chamber Basic
Configurations).*

Biliquid engines have a rigid combustion chamber (\(\dot V_0 = 0\)), so the
expansion term in §2.1 vanishes. Substituting §2.3.1 and §2.3.4 into §2.1
yields the biliquid form of the well-stirred reactor balance (Huzel & Huang §1.4;
Sutton & Biblarz §8.1):

\[
\boxed{\frac{dP_0}{dt} = \frac{R T_0}{V_0}\left[
  \dot{m}_{fuel} + \dot{m}_{ox}
  - \frac{P_0\,A_t}{\sqrt{R T_0}}\sqrt{k}\!\left(\frac{2}{k+1}\right)^{\!(k+1)/[2(k-1)]}
\right]}
\]

Evaluated by the same
[`compute_chamber_pressure_mass_balance`][machwave.core.mass_balance.compute_chamber_pressure_mass_balance]
used in §2.2 — with \(\dot{m}_{in} = \dot{m}_{fuel} + \dot{m}_{ox}\), \(C_d = 1\),
and chamber-state \(\{T_0, R, k\}\) — and integrated with the same RK4 solver as §2.2.

The thermochemical state \(\{T_0, R, k\}\) is evaluated by NASA-CEA at each step from
the current \(P_0\), the design expansion ratio, and the instantaneous mixture ratio
\(\dot{m}_{ox} / \dot{m}_{fuel}\). The result is held constant within the RK4
sub-stages — an explicit lag that is acceptable because chamber properties are
only weakly pressure-dependent (cf. Sutton & Biblarz §5.4 on equilibrium
thermochemistry). Before flow develops the formulation's design O/F is used as
the seed; after one tank empties the last evaluated properties are reused for
the chamber-pressure decay.

### 2.3.6 Modelling Assumptions and Limitations

*References: Sutton & Biblarz (2017) Ch. 8-9; Huzel & Huang (1992) Ch. 1, 4, 8.*

The biliquid engine mass balance is built on a number of simplifying assumptions; users should
keep these in mind when interpreting transient results:

- **Well-stirred reactor / instantaneous combustion.** Cold liquid propellant is
  assumed to burn to equilibrium products immediately upon entering the chamber.
  Atomisation, vaporisation, and finite reaction times are not resolved
  (Huzel & Huang Ch. 4 §4.1; Sutton & Biblarz Ch. 9 covers the real combustion
  process and its instabilities).
- **Uniform chamber state.** Pressure, temperature, and composition are spatially
  uniform — there is no L\* effect, no residence-time penalty, and no chamber-cooling
  energy loss (cf. Huzel & Huang §4.1 on \(L^*\) sizing).
- **Constant \(T_0\), constant \(V_0\).** Flame temperature is treated as the CEA
  equilibrium value at the *current* \(P_0\) and design \(\varepsilon\) (Sutton &
  Biblarz Ch. 5); free volume is fixed (no regenerative cooling jacket displacement,
  no throat erosion — see Huzel & Huang Ch. 4 for cooling-jacket geometry).
- **Isothermal tank.** The two-phase model assumes constant tank temperature; the
  energy of vaporisation that would normally cool a self-pressurised tank during
  blowdown is **not** modelled (Huzel & Huang Ch. 8 covers tank thermodynamics in
  more depth).
- **Bulk fluid density at the injector.** When the tank is two-phase, the orifice
  flow uses the bulk mixture density rather than the liquid saturation density —
  acceptable while the tank is mostly liquid, less accurate as it empties
  (Huzel & Huang §4.5 on injector hydraulics).
- **Burn ends at first depletion.** Each stream is capped at its remaining tank mass
  and the burn stops as soon as either tank empties (§2.3.3); the fuel-rich (or
  oxidiser-rich) tail a real engine produces as one propellant runs out is not
  modelled (Sutton & Biblarz §6.1).

---

## References

1. Seidel, H. (1965). *Transient Chamber Pressure and Thrust in Solid Rocket Motors*. Air Force Rocket Propulsion Laboratory (AFRPL).
2. Sutton, G. P., & Biblarz, O. (2017). *Rocket Propulsion Elements* (9th ed.). Wiley.
3. Huzel, D. K., & Huang, D. H. (1992). *Modern Engineering for Design of Liquid-Propellant Rocket Engines*. AIAA Progress in Astronautics and Aeronautics, Vol. 147.
