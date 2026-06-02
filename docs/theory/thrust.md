# 1. Thrust and Performance

Machwave calculates the **thrust** of a rocket motor/engine using the **thrust coefficient formulation**, which is derived from the idealized flow through a rocket nozzle.
The ideal thrust coefficient is calculated and multiplied by the **nozzle efficiency** to obtain the real thrust coefficient.
The nozzle efficiency accounts for the deviations from the idealized assumptions, such as boundary layer losses, chemical kinetic losses, and more.

$$
F = C_f\, P_0\, A_t
$$

(Sutton & Biblarz, Eq. 3-31)

where:

- $F$ is the thrust [N]
- $C_f$ is the thrust coefficient
- $P_0$ is the chamber stagnation pressure [Pa]
- $A_t$ is the nozzle throat area [m$^2$]

Implemented in [`get_thrust_from_thrust_coefficient`][machwave.core.compressible_flow.nozzle.get_thrust_from_thrust_coefficient].

The **ideal thrust coefficient** is given by:

$$
C_{f,\text{ideal}} = \sqrt{\frac{2k_e^2}{k_e-1}\left(\frac{2}{k_e+1}\right)^{(k_e+1)/(k_e-1)}\!\left[1-\left(\frac{P_e}{P_0}\right)^{(k_e-1)/k_e}\right]} + \varepsilon\,\frac{P_e - P_\text{ext}}{P_0}
$$

(Sutton & Biblarz, Eq. 3-30)

where:

- $k_e$ is the exhaust isentropic exponent
- $P_e$ is the exit pressure [Pa]
- $P_\text{ext}$ is the external (ambient) pressure [Pa]
- $\varepsilon$ is the expansion ratio

Implemented in [`get_ideal_thrust_coefficient`][machwave.core.compressible_flow.nozzle.get_ideal_thrust_coefficient].

Real nozzles deviate from the ideal assumptions baked into the ideal thrust coefficient.
Machwave lumps these deviations into a single **nozzle efficiency** $\eta_\text{nozzle}$ applied multiplicatively to the ideal coefficient:

$$
C_{f} = \eta_\text{nozzle}\, C_{f,\text{ideal}}
$$

$$
\eta_\text{nozzle} = 1 - \sum_i \eta_i
$$

where each $\eta_i$ is a loss fraction accounting for one or more of the idealized assumptions.
Which and how many losses are included depends on the motor/engine category (see [nozzle losses](nozzle_losses.md)).

Implemented in
[`apply_thrust_coefficient_correction`][machwave.core.compressible_flow.nozzle.apply_thrust_coefficient_correction],
with the efficiency from
[`get_overall_nozzle_efficiency`][machwave.core.compressible_flow.losses.get_overall_nozzle_efficiency].

After the thrust is calculated, the total impulse is obtained by integrating it over the thrust time:

$$
I_{total} = \int_0^{t_{thrust}} F\,dt
$$

where:

- $I_{total}$ is the total impulse [N-s]
- $t_{thrust}$ is the total thrust time [s]

Machwave integrates the discrete thrust-time trace numerically.

Implemented in
[`get_total_impulse`][machwave.core.performance.get_total_impulse].

Finally, the **specific impulse** measures the impulse delivered per unit weight of propellant consumed:

$$
I_{sp} = \frac{I_{total}}{m_{prop}\,g_0} \quad [\text{s}]
$$

where:

- $I_{sp}$ is the specific impulse [s]
- $m_{prop}$ is the initial propellant mass [kg]
- $g_0 = 9.80665\ \text{m/s}^2$ is the standard gravitational acceleration

Implemented in
[`get_specific_impulse`][machwave.core.performance.get_specific_impulse].

# References

1. Sutton, G. P., & Biblarz, O. (2001). *Rocket Propulsion Elements* (7th ed.). Wiley. Ch. 2-3.
