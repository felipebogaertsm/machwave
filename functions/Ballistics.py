import numpy as np
import fluids.atmosphere as atm


class Rocket:
    def __init__(self, mass_wo_motor, Cd, D_rocket, structure, ib_parameters):
        self.mass_wo_motor = mass_wo_motor
        self.Cd = Cd
        self.D_rocket = D_rocket
        self.structure = structure
        self.ib_parameters = ib_parameters


class Ballistics:
    def __init__(self, t, y, v, a, v_rail, y_burnout, Mach):
        self.t = t
        self.y = y
        self.v = v
        self.a = a
        self.v_rail = v_rail
        self.y_burnout = y_burnout
        self.Mach = Mach


def get_trajectory(rocket, h0, rail_length, drogue_time, Cd_drogue, D_drogue, Cd_main, D_main,
                   main_chute_activation_height):
    # Initial conditions [m, m/s, s]
    y, v, t = np.array([0]), np.array([0]), np.array([0])
    # Time step (0.01 recommended) [s]
    dt = 0.01
    # Drag coefficient
    Cd = rocket.Cd
    # Rocket mass (without motor) and payload mass [kg]
    m_wo_motor = rocket.mass_wo_motor
    # Empty motor mass [kg]
    m_motor = rocket.structure.m_motor
    # Rocket radius [m]
    r = rocket.D_rocket / 2

    # ______________________________________________________________
    # BALLISTICS SIMULATION

    m_prop = rocket.ib_parameters.m_prop
    apogee = 0
    apogee_time = - 1
    main_time = 0

    i = 0
    while y[i] >= 0 or m_prop[i - 1] > 0:

        T = np.interp(t, rocket.ib_parameters.t, rocket.ib_parameters.F, left=0, right=0)
        m_prop = np.interp(t, rocket.ib_parameters.t, rocket.ib_parameters.m_prop,
                           left=rocket.ib_parameters.m_prop[0], right=0)

        if i == 0:
            a = np.array([T[0] * (m_wo_motor + m_prop[0] + m_motor) * 0])

        # Local density 'p_air' [kg/m3] and acceleration of gravity 'g' [m/s2].
        p_air = atm.ATMOSPHERE_1976(y[i] + h0).rho
        g = atm.ATMOSPHERE_1976.gravity(h0 + y[i])

        # Instantaneous mass of the vehicle [kg]:
        M = m_wo_motor + m_motor + m_prop[i]

        if i == 0:
            M_initial = M

        # Drag properties:
        if v[i] < 0 and y[i] <= main_chute_activation_height and m_prop[i] == 0:
            if main_time == 0:
                main_time = t[i]
            A_drag = (np.pi * r ** 2) * Cd + (np.pi * D_drogue ** 2) * 0.25 * Cd_drogue + \
                    (np.pi * D_main ** 2) * 0.25 * Cd_main
        elif apogee_time >= 0 and t[i] >= apogee_time + drogue_time:
            A_drag = (np.pi * r ** 2) * Cd + (np.pi * D_drogue ** 2) * 0.25 * Cd_drogue
        else:
            A_drag = (np.pi * r ** 2) * Cd

        D = (A_drag * p_air) * 0.5

        k1, l1 = ballistics_ode(y[i], v[i], T[i], D, M, g)
        k2, l2 = ballistics_ode(y[i] + 0.5 * k1 * dt, v[i] + 0.5 * l1 * dt, T[i], D, M, g)
        k3, l3 = ballistics_ode(y[i] + 0.5 * k2 * dt, v[i] + 0.5 * l2 * dt, T[i], D, M, g)
        k4, l4 = ballistics_ode(y[i] + 0.5 * k3 * dt, v[i] + 0.5 * l3 * dt, T[i], D, M, g)

        y = np.append(y, y[i] + (1 / 6) * (k1 + 2 * (k2 + k3) + k4) * dt)
        v = np.append(v, v[i] + (1 / 6) * (l1 + 2 * (l2 + l3) + l4) * dt)
        a = np.append(a, (1 / 6) * (l1 + 2 * (l2 + l3) + l4))
        t = np.append(t, t[i] + dt)

        if y[i + 1] <= y[i] and m_prop[i] == 0 and apogee == 0:
            apogee = y[i]
            apogee_time = t[np.where(y == apogee)]

        i = i + 1

    if y[-1] < 0:
        y = np.delete(y, -1)
        v = np.delete(v, -1)
        a = np.delete(a, -1)
        t = np.delete(t, -1)

    Mach = np.zeros(np.size(v))
    for i in range(np.size(v)):
        Mach[i] = v[i] / atm.ATMOSPHERE_1976(y[i]).v_sonic

    print(np.max(Mach))

    v_rail = v[np.where(y >= rail_length)]
    v_rail = v_rail[0]
    y_burnout = y[np.where(v == np.max(v))]
    y_burnout = y_burnout[0]

    return Ballistics(t, y, v, a, v_rail, y_burnout, Mach)


def ballistics_ode(y, v, T, D, M, g):
    """ Returns dydt and dvdt. """
    if v < 0:
        x = -1
    else:
        x = 1
    dvdt = (T - x * D * (v ** 2)) / M - g
    dydt = v
    return dydt, dvdt
