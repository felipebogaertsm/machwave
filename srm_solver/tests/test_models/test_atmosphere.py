# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import pytest


def test_atmosphere_1976(atmosphere_1976):
    pressure_at_sea_level = atmosphere_1976.get_pressure(y_amsl=0)
    assert pressure_at_sea_level == pytest.approx(101325)

    for i in range(int(100e3)):  # 0 up to 100 km
        height = float(i)
        # Test density:
        density = atmosphere_1976.get_density(y_amsl=height)
        assert density >= 0
        # Test gravity:
        gravity = atmosphere_1976.get_gravity(y_amsl=height)
        assert gravity >= 0
        # Test pressure:
        pressure = atmosphere_1976.get_pressure(y_amsl=height)
        assert pressure >= 0
