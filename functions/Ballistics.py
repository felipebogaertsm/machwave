import numpy as np
import fluids.atmosphere as atm


class Rocket:
    def __init__(self, mass_wo_motor, Cd, D_rocket, structure):
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
    def __init__(self, t, y, v, a, v_rail, y_burnout, Mach):
        self.t = t
        self.y = y
        self.v = v
        self.a = a
        self.v_rail = v_rail
        self.y_burnout = y_burnout
        self.Mach = Mach
