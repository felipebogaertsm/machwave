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

Differentiating (constant \(T_0\), constant \(V_0\)):

\[
\frac{dM_{stored}}{dt} = \frac{V_0}{R T_0}\frac{dP_0}{dt}
\]

Substituting into the mass balance:

\[
\boxed{\frac{dP_0}{dt} = \frac{R T_0}{V_0}\left(\dot{m}_{gen} - \dot{m}_{out}\right)}
\]

This single ODE is the foundation of all internal-ballistics simulations in machwave.
It is integrated numerically using the 4th-order Runge–Kutta solver in
[`machwave.core.solvers`][machwave.core.solvers].

---

## 2.2 Solid Rocket Motor (SRM)

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

### 2.2.4 SRM ODE

Substituting into §2.1:

\[
\boxed{\frac{dP_0}{dt} = \frac{R T_0}{V_0}\left(\rho_p r A_b - \frac{C_d P_0 A_t\, H}{\sqrt{R T_0}}\right)}
\]

Evaluated by
[`compute_chamber_pressure_mass_balance`][machwave.core.mass_balance.compute_chamber_pressure_mass_balance]
with \(\dot{m}_{in} = \rho_p r A_b\), as called from
[`SolidMotorState`][machwave.simulation.solid.states.SolidMotorState].

---

## 2.3 Liquid Rocket Engine (LRE)

*References: Sutton & Biblarz (2017), Ch. 6; Huzel & Huang (1992), Ch. 1, 4, 7.*

For an LRE the mass-generation term is no longer set by surface regression but by
the **injector mass flow** of two independent propellant streams. Mass exits through
the same choked throat as in §2.2.2.

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
feed system (see §2.3.2).

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
[`Tank`][machwave.models.feed_systems.tanks.base.Tank] and the orchestrating
[`StackedTankPressureFedFeedSystem`][machwave.models.feed_systems.cycles.stacked_tank_pressure_fed.StackedTankPressureFedFeedSystem].

### 2.3.3 Stoichiometric Limiting-Reagent Adjustment

*References: Sutton & Biblarz (2017) Ch. 6 §6.1 (Mixture Ratio); Huzel & Huang
(1992) Ch. 1 §1.3 (Performance Parameters).*

The injectors deliver fuel and oxidiser independently, so over a finite step \(\Delta t\)
one tank can run dry while the other still has propellant. machwave clamps the surplus
to preserve the design oxidiser–fuel ratio \(\mathrm{O\!/\!F} = \dot{m}_{ox}/\dot{m}_{fuel}\)
(Sutton & Biblarz §6.1):

\[
\text{if } \dot{m}_{fuel}\Delta t \geq m_{fuel}: \;\;
\dot{m}_{fuel} \leftarrow m_{fuel}/\Delta t,
\;\;
\dot{m}_{ox} \leftarrow \mathrm{O\!/\!F}\cdot\dot{m}_{fuel}
\]

(and symmetrically when oxidiser is the limiting reagent). This avoids unphysical
post-burnout transients in which one stream continues for several steps after the
other has been exhausted. Implemented in
[`LiquidEngineState`][machwave.simulation.liquid.states.LiquidEngineState].

### 2.3.4 Mass Exit Rate — Choked Throat

*References: Sutton & Biblarz (2017) Ch. 3 §3.3 (Isentropic Flow through Nozzles);
Huzel & Huang (1992) Ch. 1 §1.4 (The Gas-Flow Processes).*

The exit term is identical to §2.2.2 — the choked-flow expression derived in §1.7
(Sutton & Biblarz §3.3). For LRE the implementation drops the throat discharge
coefficient (\(C_d \equiv 1\)) and uses the chamber-state isentropic exponent
\(k = k_\text{chamber}\):

\[
\dot{m}_{out} = \frac{P_0\, A_t}{\sqrt{R T_0}}\,\sqrt{k}\left(\frac{2}{k+1}\right)^{(k+1)/[2(k-1)]}.
\]

### 2.3.5 LRE Chamber-Pressure ODE

*References: Huzel & Huang (1992) Ch. 1 §1.4 and Ch. 4 §4.1 (Combustion-Chamber
Processes); Sutton & Biblarz (2017) Ch. 8 §8.1 (Combustion Chamber Basic
Configurations).*

Substituting §2.3.1 and §2.3.4 into §2.1 yields the LRE form of the well-stirred
reactor balance (Huzel & Huang §1.4; Sutton & Biblarz §8.1):

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

The LRE mass balance is built on a number of simplifying assumptions; users should
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
- **Stoichiometric clamping.** When one tank empties first, the simulation drops
  the surplus reagent rather than tracking the fuel-rich (or ox-rich) tail of a
  real engine (Sutton & Biblarz §6.1).

---

## References

1. Seidel, H. (1965). *Transient Chamber Pressure and Thrust in Solid Rocket Motors*. Air Force Rocket Propulsion Laboratory (AFRPL).
2. Sutton, G. P., & Biblarz, O. (2017). *Rocket Propulsion Elements* (9th ed.). Wiley. Ch. 6, 12.
3. Huzel, D. K., & Huang, D. H. (1992). *Modern Engineering for Design of Liquid-Propellant Rocket Engines*. AIAA Progress in Astronautics and Aeronautics, Vol. 147. Ch. 1, 4, 7.
