class Rocket:
    def __init__(self, mass_wo_motor, Cd, D_rocket):
        self.mass_wo_motor = mass_wo_motor
        self.Cd = Cd
        self.D_rocket = D_rocket


class Recovery:
    def __init__(self, drogue_time, Cd_drogue, D_drogue, Cd_main, D_main, main_chute_activation_height):
        self.drogue_time = drogue_time
        self.Cd_drogue = Cd_drogue
        self.D_drogue = D_drogue
        self.Cd_main = Cd_main
        self.D_main = D_main
        self.main_chute_activation_height = main_chute_activation_height


class Ballistics:
    def __init__(self, t, y, v, acc, v_rail, y_burnout, Mach, apogee_time, flight_time, P_ext):
        self.t = t
        self.y = y
        self.v = v
        self.acc = acc
        self.v_rail = v_rail
        self.y_burnout = y_burnout
        self.Mach = Mach
        self.apogee_time = apogee_time
        self.flight_time = flight_time
        self.P_ext = P_ext


def ballistics_ode(y, v, T, D, M, g):
    """ Returns dydt and dvdt. """
    if v < 0:
        x = -1
    else:
        x = 1
    dvdt = (T - x * D * (v ** 2)) / M - g
    dydt = v
    return dydt, dvdt
