# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Stores Ballistics class and methods.
"""


class Ballistics:
    def __init__(
        self,
        t,
        y,
        v,
        acc,
        v_rail,
        y_burnout,
        Mach,
        apogee_time,
        flight_time,
        P_ext
    ):
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
