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
burn area. This is used directly in
[`compute_chamber_pressure_mass_balance_srm`][machwave.core.equations.srm_mass_balance.compute_chamber_pressure_mass_balance_srm].

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

Implemented in
[`compute_chamber_pressure_mass_balance_srm`][machwave.core.equations.srm_mass_balance.compute_chamber_pressure_mass_balance_srm].

---

## 2.3 Liquid Rocket Engine (LRE)

!!! warning "To be completed"
    This section is a work in progress.

---

## References

1. Seidel, H. (1965). *Transient Chamber Pressure and Thrust in Solid Rocket Motors*. Air Force Rocket Propulsion Laboratory (AFRPL).
2. Sutton, G. P., & Biblarz, O. (2017). *Rocket Propulsion Elements* (9th ed.). Wiley. Ch. 12.