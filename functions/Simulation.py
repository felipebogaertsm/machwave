import numpy as np


class Simulation:
    def __init__(self):
        self.A_burn = None
        self.V0 = None
        self.Kn = None
        self.P0 = None

    def run_simulation(self, grain, structure, rocket, dt, P_igniter, P_external):

        A_burn_initial, V_propellant_initial = 0, 0
        for n in range(grain.N):
            A_burn_initial = A_burn_initial + grain.get_burn_area(0, n)
            V_propellant_initial = V_propellant_initial + grain.get_propellant_volume(0, n)

        A_burn = np.array([A_burn_initial])
        V_propellant = np.array([V_propellant_initial])
        x = np.array([0])
        t = np.array([0])
        P0 = np.array([P_igniter])
        r0 = np.array([])
        V0 = np.array([np.pi * (structure.D_chamber / 2) ** 2 * structure.L_chamber - V_propellant_initial])

        i = 0

        while A_burn[i] > 0 or P0[i] >= critical_pressure_ratio * P_igniter:
            a, n = burn_rate_coefs(propellant, P0[i])
        r0 = np.append(r0, (a * (P0[i] * 1e-6) ** n) * 1e-3)
        dt = dx / r0[i]
        x = np.append(x, x[i] + dx)
        t = np.append(t, t[i] + dt)

        for n in range(N):
            A_burn_instant = A_burn_instant + grain.get_burn_area(x[i], n)
            V_propellant_instant = V_propellant_instant + grain.get_propellant_volume(x[i], n)

        A_burn, V_propellant = np.append(A_burn, A_burn_instant), np.append(V_propellant, V_propellant_instant)
        V0 = np.append(V0, np.pi * (D_chamber / 2) ** 2 * L_chamber - V_propellant[i])

        k1 = solve_cp_seidel(P0[i], P_external, A_burn[i],
                             V0[i], A_throat, pp, k_mix_ch, R_ch, T0, r[i])
        k2 = solve_cp_seidel(P0[i] + 0.5 * k1 * dt, P_external, A_burn[i],
                             V0[i], A_throat, pp, k_mix_ch, R_ch, T0, r[i])
        k3 = solve_cp_seidel(P0[i] + 0.5 * k2 * dt, P_external, A_burn[i],
                             V0[i], A_throat, pp, k_mix_ch, R_ch, T0, r[i])
        k4 = solve_cp_seidel(P0[i] + 0.5 * k3 * dt, P_external, A_burn[i],
                             V0[i], A_throat, pp, k_mix_ch, R_ch, T0, r[i])

        P0 = np.append(P0, P0[i] + (1 / 6) * (k1 + 2 * (k2 + k3) + k4) * dt)

        i = i + 1

        pass
