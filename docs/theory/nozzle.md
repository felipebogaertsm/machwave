# 1. Nozzle Theory

This section derives the compressible flow relations used throughout `machwave` for
nozzle flow modelling. Every result is traced back to two fundamental laws: the
**First Law of Thermodynamics** and the **ideal gas law**.

**Assumptions**

- Quasi-one-dimensional flow (flow properties uniform across every cross-section).
- Adiabatic, inviscid — no heat exchange or friction inside the nozzle.
- Calorically perfect gas: specific heats \(c_p\), \(c_v\) and their ratio
  \(k = c_p/c_v\) are constant.
- No shaft work.

---

## 1.1 Steady-Flow Energy Equation

For a steady, adiabatic, work-free flow the First Law requires the **specific
stagnation enthalpy** to be conserved along every streamline:

\[
\boxed{h + \frac{v^2}{2} = \text{constant}}
\]

Applying this between any two stations \(x\) and \(y\):

\[
h_x + \frac{v_x^2}{2} = h_y + \frac{v_y^2}{2}
\]

which rearranges to

\[
h_x - h_y = \frac{1}{2}\left(v_y^2 - v_x^2\right).
\]

For a calorically perfect gas \(h = c_p T\), so this becomes

\[
c_p\left(T_x - T_y\right) = \frac{1}{2}\left(v_y^2 - v_x^2\right).
\]

Choosing station \(x\) as the **stagnation state** (\(v = 0\), subscript \(0\))
and \(y\) as any point in the flow:

\[
\boxed{c_p T_0 = c_p T + \frac{v^2}{2}}
\]

\(T_0\) is the **stagnation temperature**, a conserved quantity along the flow.

The ideal gas relation \(c_p - c_v = R\) and \(k = c_p/c_v\) give

\[
c_p = \frac{kR}{k-1}, \qquad R = \frac{\bar{R}}{M_w}
\]

where \(\bar{R} = 8.314\ \text{J mol}^{-1}\text{K}^{-1}\) and \(M_w\) is the
molar mass of the combustion products.

---

## 1.2 Mach Number and Stagnation Temperature Ratio

The local speed of sound in a perfect gas is \(a = \sqrt{kRT}\). Defining the
Mach number \(M = v/a\) and substituting \(v = Ma\) into the energy equation:

\[
c_p T_0 = c_p T + \frac{(Ma)^2}{2} = c_p T + \frac{kRM^2T}{2} = c_p T\left(1 + \frac{k-1}{2}M^2\right)
\]

since \(\frac{kR}{2c_p} = \frac{k-1}{2}\). Therefore

\[
\boxed{\frac{T_0}{T} = 1 + \frac{k-1}{2}M^2}
\]

---

## 1.3 Isentropic Stagnation Relations

For an isentropic process the entropy is constant, which for a perfect gas means

\[
P\rho^{-k} = \text{const}, \qquad \frac{P}{P_0} = \left(\frac{\rho}{\rho_0}\right)^k.
\]

Combined with the ideal gas law \(P = \rho R T\):

\[
\frac{P}{P_0} = \left(\frac{T}{T_0}\right)^{k/(k-1)}, \qquad
\frac{\rho}{\rho_0} = \left(\frac{T}{T_0}\right)^{1/(k-1)}.
\]

Substituting the temperature ratio from §1.2:

\[
\boxed{\frac{P_0}{P} = \left(1 + \frac{k-1}{2}M^2\right)^{k/(k-1)}}
\qquad
\boxed{\frac{\rho_0}{\rho} = \left(1 + \frac{k-1}{2}M^2\right)^{1/(k-1)}}
\]

These are the **isentropic stagnation relations**, implemented in
[`get_exit_pressure`][machwave.core.compressible_flow.isentropic.get_exit_pressure].

---

## 1.4 Critical (Sonic) Conditions and Choked Flow

At the throat \(M = 1\). Evaluating the stagnation relations at this condition
(denoting the sonic state with \(^*\)):

\[
\frac{T^*}{T_0} = \frac{2}{k+1}
\]

\[
\boxed{\frac{P^*}{P_0} = \left(\frac{2}{k+1}\right)^{k/(k-1)}}
\]

\[
\frac{\rho^*}{\rho_0} = \left(\frac{2}{k+1}\right)^{1/(k-1)}
\]

The nozzle is **choked** — the throat is sonic and the mass flow rate has reached
its maximum — whenever the back pressure satisfies

\[
\frac{P_\text{ext}}{P_0} \leq \left(\frac{2}{k+1}\right)^{k/(k-1)}.
\]

Implemented in
[`get_critical_pressure_ratio`][machwave.core.compressible_flow.isentropic.get_critical_pressure_ratio]
and
[`is_flow_choked`][machwave.core.compressible_flow.isentropic.is_flow_choked].

---

## 1.5 Area–Mach Relation

Applying continuity between the throat and an arbitrary cross-section of area
\(A\):

\[
\rho v A = \rho^* a^* A_t \implies \frac{A}{A_t} = \frac{\rho^* a^*}{\rho v}.
\]

Expressing each factor using §1.2 and §1.3:

\[
\frac{a^*}{v} = \frac{a^*}{Ma} = \frac{1}{M}\sqrt{\frac{T^*}{T}} = \frac{1}{M}\sqrt{\frac{2}{k+1}\cdot\frac{1}{1+\frac{k-1}{2}M^2}}
\]

\[
\frac{\rho^*}{\rho} = \left(\frac{T^*}{T_0}\cdot\frac{T_0}{T}\right)^{1/(k-1)} = \left(\frac{2}{(k+1)}\left(1+\frac{k-1}{2}M^2\right)\right)^{1/(k-1)}
\]

Combining:

\[
\boxed{\frac{A}{A_t} = \frac{1}{M}\left[\frac{2}{k+1}\left(1+\frac{k-1}{2}M^2\right)\right]^{(k+1)/[2(k-1)]}}
\]

For a given expansion ratio \(\varepsilon = A_e/A_t\) there are two solutions:
\(M < 1\) (subsonic) and \(M > 1\) (supersonic). machwave always selects the
supersonic root using Brent's method; see
[`get_exit_mach_from_expansion_ratio`][machwave.core.compressible_flow.isentropic.get_exit_mach_from_expansion_ratio].

---

## 1.6 Exit Velocity

Applying the energy equation (§1.1) between the chamber (\(v \approx 0\)) and
the nozzle exit:

\[
v_e = \sqrt{2c_p T_0\left[1 - \frac{T_e}{T_0}\right]}
    = \sqrt{\frac{2kR}{k-1}T_0\left[1 - \left(\frac{P_e}{P_0}\right)^{(k-1)/k}\right]}
\]

where the last step uses the isentropic temperature ratio from §1.3 with \(T_e/T_0 = (P_e/P_0)^{(k-1)/k}\).

---

## 1.7 Choked Mass Flow Rate

At the throat \(M = 1\), so \(v^* = a^* = \sqrt{kRT^*}\). Using the continuity
equation and the critical relations from §1.4:

\[
\dot{m} = \rho^* a^* A_t = \frac{\rho_0}{\left(\frac{\rho_0}{\rho^*}\right)}\sqrt{kRT^*}\, A_t
\]

Substituting \(\rho_0 = P_0/(RT_0)\), \(T^* = 2T_0/(k+1)\):

\[
\boxed{\dot{m} = \frac{P_0\, A_t}{\sqrt{T_0}}\sqrt{\frac{k}{R}}\left(\frac{2}{k+1}\right)^{(k+1)/[2(k-1)]}}
\]

This is the key expression linking chamber pressure to propellant mass flow — used
in all mass-balance ODEs throughout machwave.

---

## 1.8 Thrust Coefficient

The **thrust** on a rocket nozzle equals the momentum flux leaving the exit plus
the pressure difference acting on the exit area:

\[
F = \dot{m}\,v_e + (P_e - P_\text{ext})\,A_e.
\]

Dividing by \(P_0 A_t\) defines the dimensionless **thrust coefficient**
\(C_f = F / (P_0 A_t)\). Substituting \(\dot{m}\) from §1.7 and \(v_e\) from
§1.6:

\[
\frac{\dot{m}\,v_e}{P_0 A_t}
  = \sqrt{\frac{k}{R}\left(\frac{2}{k+1}\right)^{(k+1)/(k-1)}}\cdot
    \sqrt{\frac{2kR}{k-1}\left[1-\left(\frac{P_e}{P_0}\right)^{(k-1)/k}\right]}
  = \sqrt{\frac{2k^2}{k-1}\left(\frac{2}{k+1}\right)^{(k+1)/(k-1)}\left[1-\left(\frac{P_e}{P_0}\right)^{(k-1)/k}\right]}
\]

Therefore:

\[
\boxed{C_f = \sqrt{\frac{2k^2}{k-1}\left(\frac{2}{k+1}\right)^{(k+1)/(k-1)}\!\left[1-\left(\frac{P_e}{P_0}\right)^{(k-1)/k}\right]} + \varepsilon\,\frac{P_e - P_\text{ext}}{P_0}}
\]

with \(\varepsilon = A_e/A_t\). Thrust follows immediately from the definition:

\[
F = C_f\, P_0\, A_t.
\]

Implemented in
[`get_ideal_thrust_coefficient`][machwave.core.compressible_flow.nozzle.get_ideal_thrust_coefficient]
and
[`get_thrust_from_thrust_coefficient`][machwave.core.compressible_flow.nozzle.get_thrust_from_thrust_coefficient].

---

## 1.9 Optimal Expansion Ratio

The pressure-thrust term \(\varepsilon(P_e - P_\text{ext})/P_0\) vanishes when
\(P_e = P_\text{ext}\) (perfectly expanded nozzle). Inserting \(P_e = P_\text{ext}\)
into the area–Mach relation (§1.5), with the exit Mach determined from the
isentropic pressure ratio (§1.3):

\[
\varepsilon_\text{opt} = \frac{1}{M_e}
  \left[\frac{2}{k+1}\left(1+\frac{k-1}{2}M_e^2\right)\right]^{(k+1)/[2(k-1)]}
\]

where \(M_e\) satisfies \(P_0/P_\text{ext} = (1 + (k-1)M_e^2/2)^{k/(k-1)}\),
or equivalently in closed form:

\[
\boxed{\varepsilon_\text{opt} = \left[
  \left(\frac{k+1}{2}\right)^{1/(k-1)}
  \left(\frac{P_\text{ext}}{P_0}\right)^{1/k}
  \sqrt{\frac{k+1}{k-1}\left(1 - \left(\frac{P_\text{ext}}{P_0}\right)^{(k-1)/k}\right)}
\right]^{-1}}
\]

Implemented in
[`get_optimal_expansion_ratio`][machwave.core.compressible_flow.nozzle.get_optimal_expansion_ratio].
