import numpy as np
import fluids.atmosphere as atm


class Rocket:
    def __init__(self, mass_wo_motor, Cd, D_rocket, structure):
        self.mass_wo_motor = mass_wo_motor
        self.Cd = Cd
        self.D_rocket = D_rocket


class Ballistics:
    def __init__(self, t, y, v, a, v_rail, y_burnout, Mach):
        self.t = t
        self.y = y
        self.v = v
        self.a = a
        self.v_rail = v_rail
        self.y_burnout = y_burnout
        self.Mach = Mach
