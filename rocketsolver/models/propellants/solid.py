# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Propellant data was gathered from ProPEP3. Burn rate was sourced from Richard 
Nakka's website.
"""

from rocketsolver.models.propulsion.propellant.solid import SolidPropellant

KNDX = SolidPropellant(
    [
        {"min": 0, "max": 0.779e6, "a": 8.875, "n": 0.619},
        {"min": 0.779e6, "max": 0.779e6, "a": 7.553, "n": -0.009},
        {"min": 2.572e6, "max": 5.930e6, "a": 3.841, "n": 0.688},
        {"min": 5.930e6, "max": 8.502e6, "a": 17.20, "n": -0.148},
        {"min": 8.502e6, "max": 11.20e6, "a": 4.775, "n": 0.442},
    ],
    0.95,
    1795.0 * 1.00,
    1.1308,
    1.0430,
    1712,
    42.391 * 1e-3,
    42.882 * 1e-3,
    152.4,
    154.1,
    0.307,
    0.321,
)

# Obtained from (Magnus version):
# https://www.nakka-rocketry.net/sorb.html
KNSB = SolidPropellant(
    [
        {"min": 0, "max": 11e6, "a": 5.13, "n": 0.222},
    ],
    0.95,
    1837.3 * 0.95,
    1.1361,
    1.0420,
    1603,
    39.857 * 1e-3,
    40.048 * 1e-3,
    151.4,
    153.5,
    0.316,
    0.321,
)

# Obtained from:
# https://www.nakka-rocketry.net/sorb.html
KNSB_NAKKA = SolidPropellant(
    [
        {"min": 0, "max": 0.807e6, "a": 10.708, "n": 0.625},
        {"min": 0.807e6, "max": 1.503e6, "a": 8.763, "n": -0.314},
        {"min": 1.503e6, "max": 3.792e6, "a": 7.852, "n": -0.013},
        {"min": 3.792e6, "max": 7.033e6, "a": 3.907, "n": 0.535},
        {"min": 7.033e6, "max": 10.67e6, "a": 9.653, "n": 0.064},
    ],
    0.95,
    1837.3 * 0.95,
    1.1361,
    1.0420,
    1603,
    39.857 * 1e-3,
    40.048 * 1e-3,
    151.4,
    153.5,
    0.316,
    0.321,
)

KNSU = SolidPropellant(
    [{"min": 0, "max": 100e6, "a": 8.260, "n": 0.319}],
    0.95,
    1899.5 * 0.95,
    1.1330,
    1.1044,
    1722,
    41.964 * 1e-3,
    41.517 * 1e-3,
    153.3,
    155.1,
    0.306,
    0.321,
)

KNER = SolidPropellant(
    [{"min": 0, "max": 100e6, "a": 2.903, "n": 0.395}],
    0.94,
    1820.0 * 0.95,
    1.1390,
    1.0426,
    1608,
    38.570 * 1e-3,
    38.779 * 1e-3,
    153.8,
    156.0,
    0.315,
    0.321,
)


def get_solid_propellant_from_name(prop_name: str) -> SolidPropellant:
    """ "
    Returns propellant data based on the propellant name entered by the user as a string.
    """

    if prop_name.lower() == "kndx":
        return KNDX
    elif prop_name.lower() == "knsb":
        return KNSB
    elif prop_name.lower() == "knsb-nakka":
        return KNSB_NAKKA
    elif prop_name.lower() == "knsu":
        return KNSU
    elif prop_name.lower() == "kner":
        return KNER
    else:
        print(
            "\nPropellant name not recognized. Using values for KNSB instead."
        )
        return KNSB
