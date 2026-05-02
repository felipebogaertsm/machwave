# 3. Thrust and Performance

## 3.1 Thrust

The force exerted by the rocket on its vehicle is derived by applying the
**linear momentum equation** to the nozzle control volume (see §1.8 for the full
derivation):

\[
F = \dot{m}\,v_e + (P_e - P_\text{ext})\,A_e = C_f\,P_0\,A_t
\]

Implemented in
[`get_thrust_from_thrust_coefficient`][machwave.core.compressible_flow.nozzle.get_thrust_from_thrust_coefficient].

---

## 3.2 Total Impulse

Total impulse is the time integral of thrust over the entire burn:

\[
I_{tot} = \int_0^{t_{burn}} F\,dt
\]

For practical computation, the discrete thrust-time trace is integrated
numerically. The closed-form equivalent for a constant average thrust is:

\[
\boxed{I_{tot} = F_{avg}\cdot t_{burn}}
\]

Implemented in
[`get_total_impulse`](../api/core.md).

---

## 3.3 Specific Impulse

Specific impulse \(I_{sp}\) measures the impulse delivered per unit weight of
propellant consumed — the rocket analogue of fuel efficiency:

\[
\boxed{I_{sp} = \frac{I_{tot}}{m_{prop}\,g_0}}
\quad [\text{s}]
\]

where \(g_0 = 9.80665\ \text{m/s}^2\) is the standard gravitational acceleration.
The unit *seconds* is universal: it does not depend on the unit system used for
thrust or mass.

Implemented in
[`get_specific_impulse`](../api/core.md).

---

## 3.4 Characteristic Velocity

The **characteristic velocity** \(c^*\) isolates the combustion quality from the
nozzle performance. Rearranging the choked mass flow (§1.7):

\[
\dot{m} = \frac{P_0\,A_t}{c^*}
\implies
\boxed{c^* = \frac{P_0\,A_t}{\dot{m}} = \frac{\sqrt{R T_0 / k}}{\left(\dfrac{2}{k+1}\right)^{(k+1)/[2(k-1)]}}}
\quad [\text{m/s}]
\]

A high \(c^*\) indicates high flame temperature and/or low molecular weight of
the products — properties determined solely by the propellant chemistry (computed
by CEA and stored in
[`machwave.models.propellants`][machwave.models.propellants]).

---

## 3.5 Effective Exhaust Velocity

Combining the thrust coefficient (§1.8) with \(c^*\):

\[
F = C_f\,P_0\,A_t = C_f\,\dot{m}\,c^*
\implies
c_{eff} = \frac{F}{\dot{m}} = C_f\,c^*
\]

The specific impulse can therefore also be written as:

\[
I_{sp} = \frac{c_{eff}}{g_0} = \frac{C_f\,c^*}{g_0}
\]

This factorisation shows that nozzle efficiency (\(C_f\)) and combustion
efficiency (\(c^*\)) contribute independently to \(I_{sp}\).

---

## References

1. Sutton, G. P., & Biblarz, O. (2017). *Rocket Propulsion Elements* (9th ed.). Wiley. Ch. 2, 3.
2. Huzel, D. K., & Huang, D. H. (1992). *Modern Engineering for Design of Liquid-Propellant Rocket Engines*. AIAA Progress in Astronautics and Aeronautics, Vol. 147. Ch. 1.
