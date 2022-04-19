# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Propellant data was gathered from ProPEP3.
"""

from models.propellant import Propellant

KNDX = Propellant(
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

KNSB = Propellant(
    [
        {"min": 0, "max": 0.779e6, "a": 8.875, "n": 0.619},
        {"min": 0.779e6, "max": 2.572e6, "a": 7.553, "n": -0.009},
        {"min": 2.572e6, "max": 5.930e6, "a": 3.841, "n": 0.688},
        {"min": 5.930e6, "max": 8.502e6, "a": 17.20, "n": -0.148},
        {"min": 8.502e6, "max": 11.20e6, "a": 4.775, "n": 0.442},
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

KNSB_NAKKA = Propellant(
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

KNSU = Propellant(
    [{"min": 0, "max": 20, "a": 8.260, "n": 0.319}],
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

KNER = Propellant(
    [{"min": 0, "max": 20, "a": 2.903, "n": 0.395}],
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


def prop_data(prop_name: str):
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


def get_burn_rate_coefs(prop: str, P0: float):
    """
    Sets the burn rate coefficients 'a' and 'n' according to the instantaneous chamber pressure
    """

    if prop.lower() == "kndx":
        if P0 * 1e-6 <= 0.779:
            a, n = 8.875, 0.619
        elif 0.779 < P0 * 1e-6 <= 2.572:
            a, n = 7.553, -0.009
        elif 2.572 < P0 * 1e-6 <= 5.930:
            a, n = 3.841, 0.688
        elif 5.930 < P0 * 1e-6 <= 8.502:
            a, n = 17.2, -0.148
        elif 8.502 < P0 * 1e-6 <= 11.20:
            a, n = 4.775, 0.442
        else:
            raise Exception(
                "CHAMBER PRESSURE OUT OF BOUNDS, change Propellant or nozzle"
                " throat diameter."
            )
    elif prop.lower() == "knsb-nakka":
        if P0 * 1e-6 <= 0.807:
            a, n = 10.708, 0.625
        elif 0.807 < P0 * 1e-6 <= 1.503:
            a, n = 8.763, -0.314
        elif 1.503 < P0 * 1e-6 <= 3.792:
            a, n = 7.852, -0.013
        elif 3.792 < P0 * 1e-6 <= 7.033:
            a, n = 3.907, 0.535
        elif 7.033 < P0 * 1e-6 <= 10.67:
            a, n = 9.653, 0.064
        else:
            raise Exception(
                "CHAMBER PRESSURE OUT OF BOUNDS, change Propellant or nozzle"
                " throat diameter."
            )
    elif prop.lower() == "knsb":  # from Magnus Gudnason paper 's072205'
        a, n = 5.132, 0.222
    elif prop.lower() == "knsu":
        a, n = 8.260, 0.319
    elif prop.lower() == "kndxio":
        a, n = 9.25, 0.342
    elif prop.lower() == "kndxch":
        a, n = 11.784, 0.297
    elif prop.lower() == "rnx57":
        a, n = 2.397, 0.446
    elif prop.lower() == "kner":
        a, n = 2.903, 0.395
    elif prop.lower() == "knmn":
        a, n = 5.126, 0.224
    elif prop.lower() == "custom":
        a, n = input('Type value of "a": '), input('Type value of "n": ')
    else:
        a, n = input('Type value of "a": '), input('Type value of "n": ')

    return a, n
