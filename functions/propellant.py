# Burn rate data was gathered from Nakka and Magnus Gudnason paper 's072205'.
# Propellant data was gathered from ProPEP3.
#
# ce: Combustion, two phase, heat loss, friction inefficiency factor
# pp: Propellant density [kg/m^3]
# k_mix_ch: Isentropic exponent (chamber)
# k_2ph_ex: Isentropic exponent (exhaust)
# T0_ideal: Ideal combustion temperature [K]
# T0: Real combustion temperature [K]
# M_ch: Molar weight (chamber) [100g/mole]
# M_ex: Molar weight (exhaust) [100g/mole]
# Isp_frozen, Isp_shifting: Frozen and shifting specific getImpulses [s]
# qsi_ch: Number of condensed phase moles per 100 gram (chamber) [mole]
# qsi_ex: Number of condensed phase moles per 100 gram (exhaust) [mole]

import scipy.constants


class PropellantSelected:
    def __init__(self, ce, pp, k_mix_ch, k_2ph_ex, T0_ideal, M_ch, M_ex, Isp_frozen, Isp_shifting, qsi_ch, qsi_ex):
        self.ce = ce
        self.pp = pp
        self.k_mix_ch = k_mix_ch
        self.k_2ph_ex = k_2ph_ex
        # Real combustion temperature based on the ideal temp. and the combustion efficiency [K]:
        self.T0 = T0_ideal * ce
        self.M_ch = M_ch
        self.M_ex = M_ex
        # Gas constant per molecular weight calculations:
        self.R_ch = scipy.constants.R / M_ch
        self.R_ex = scipy.constants.R / M_ex
        self.Isp_frozen = Isp_frozen
        self.Isp_shifting = Isp_shifting
        self.qsi_ch = qsi_ch
        self.qsi_ex = qsi_ex


class Propellant:
    def __init__(self, ce, pp, k_mix_ch, k_2ph_ex, T0_ideal, M_ch, M_ex, Isp_frozen, Isp_shifting, qsi_ch, qsi_ex):
        self.ce = ce
        self.pp = pp
        self.k_mix_ch = k_mix_ch
        self.k_2ph_ex = k_2ph_ex
        self.T0_ideal = T0_ideal
        self.M_ch = M_ch
        self.M_ex = M_ex
        self.Isp_frozen = Isp_frozen
        self.Isp_shifting = Isp_shifting
        self.qsi_ch = qsi_ch
        self.qsi_ex = qsi_ex


# PROPELLANTS:

kndx = Propellant(0.95, 1795.0 * 1.00, 1.1308, 1.0430, 1712, 42.391 * 1e-3,
                  42.882 * 1e-3, 152.4, 154.1, 0.307, 0.321)
knsb = Propellant(0.95, 1837.3 * 0.95, 1.1361, 1.0420, 1603, 39.857 * 1e-3,
                  40.048 * 1e-3, 151.4, 153.5, 0.316, 0.321)
knsu = Propellant(0.95, 1899.5 * 0.95, 1.1330, 1.1044, 1722, 41.964 * 1e-3,
                  41.517 * 1e-3, 153.3, 155.1, 0.306, 0.321)
kner = Propellant(0.94, 1820.0 * 0.95, 1.1390, 1.0426, 1608, 38.570 * 1e-3,
                  38.779 * 1e-3, 153.8, 156.0, 0.315, 0.321)


def prop_data(prop: str):

    """"
    Returns prop data based on the prop name entered by the user as a string.
    """

    if prop.lower() == 'kndx':
        ce, pp, k_mix_ch, k_2ph_ex, T0_ideal, M_ch, M_ex, Isp_frozen, Isp_shifting, qsi_ch, qsi_ex = \
            kndx.ce, kndx.pp, kndx.k_mix_ch, kndx.k_2ph_ex, kndx.T0_ideal, kndx.M_ch, kndx.M_ex, kndx.Isp_frozen, \
            kndx.Isp_shifting, kndx.qsi_ch, kndx.qsi_ex
    elif prop.lower() == 'knsb' or prop.lower() == 'knsb-nakka':
        ce, pp, k_mix_ch, k_2ph_ex, T0_ideal, M_ch, M_ex, Isp_frozen, Isp_shifting, qsi_ch, qsi_ex = \
            knsb.ce, knsb.pp, knsb.k_mix_ch, knsb.k_2ph_ex, knsb.T0_ideal, knsb.M_ch, knsb.M_ex, knsb.Isp_frozen, \
            knsb.Isp_shifting, knsb.qsi_ch, knsb.qsi_ex
    elif prop.lower() == 'knsu':
        ce, pp, k_mix_ch, k_2ph_ex, T0_ideal, M_ch, M_ex, Isp_frozen, Isp_shifting, qsi_ch, qsi_ex = \
            knsu.ce, knsu.pp, knsu.k_mix_ch, knsu.k_2ph_ex, knsu.T0_ideal, knsu.M_ch, knsu.M_ex, knsu.Isp_frozen, \
            knsu.Isp_shifting, knsu.qsi_ch, knsu.qsi_ex
    elif prop.lower() == 'kner':
        ce, pp, k_mix_ch, k_2ph_ex, T0_ideal, M_ch, M_ex, Isp_frozen, Isp_shifting, qsi_ch, qsi_ex = \
            kner.ce, kner.pp, kner.k_mix_ch, kner.k_2ph_ex, kner.T0_ideal, kner.M_ch, kner.M_ex, kner.Isp_frozen, \
            kner.Isp_shifting, kner.qsi_ch, kner.qsi_ex
    else:
        print('\nPropellant name not recognized. Using values for KNSB instead.')
        ce, pp, k_mix_ch, k_2ph_ex, T0_ideal, M_ch, M_ex, Isp_frozen, Isp_shifting, qsi_ch, qsi_ex = \
            knsb.ce, knsb.pp, knsb.k_mix_ch, knsb.k_2ph_ex, knsb.T0_ideal, knsb.M_ch, knsb.M_ex, knsb.Isp_frozen, \
            knsb.Isp_shifting, knsb.qsi_ch, knsb.qsi_ex

    return ce, pp, k_mix_ch, k_2ph_ex, T0_ideal, M_ch, M_ex, Isp_frozen, Isp_shifting, qsi_ch, qsi_ex


def get_burn_rate_coefs(prop: str, P0: float):
    """
    Sets the burn rate coefficients 'a' and 'n' according to the instantaneous chamber pressure
    """

    if prop.lower() == 'kndx':
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
            print('\nCHAMBER PRESSURE OUT OF BOUNDS, change Propellant or nozzle throat diameter.\n')
            a, n = -1, -1
    elif prop.lower() == 'knsb-nakka':
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
            print('\nCHAMBER PRESSURE OUT OF BOUNDS, change Propellant or nozzle throat diameter.\n')
            a, n = -1, -1
    elif prop.lower() == 'knsb':
        a, n = 5.132, 0.222
    elif prop.lower() == 'knsu':
        a, n = 8.260, 0.319
    elif prop.lower() == 'kndxio':
        a, n = 9.25, 0.342
    elif prop.lower() == 'kndxch':
        a, n = 11.784, 0.297
    elif prop.lower() == 'rnx57':
        a, n = 2.397, 0.446
    elif prop.lower() == 'kner':
        a, n = 2.903, 0.395
    elif prop.lower() == 'knmn':
        a, n = 5.126, 0.224
    elif prop.lower() == 'custom':
        a, n = input('Type value of "a": '), input('Type value of "n": ')
    else:
        a, n = input('Type value of "a": '), input('Type value of "n": ')

    return a, n
