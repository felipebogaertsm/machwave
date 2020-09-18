# Burn rate data was gathered from Nakka and Magnus Gudnason paper 's072205'.
# Propellant data was gathered from ProPEP3.
#
# ce: Combustion, two phase, heat loss, friction inefficiency factor
# pp: Propellant density [kg/m^3]
# kCh: Isentropic exponent (chamber)
# kEx: Isentropic exponent (exhaust)
# T0ideal: Ideal combustion temperature [K]
# T0: Real combustion temperature [K]
# MCh: Molar weight (chamber) [100g/mole]
# MEx: Molar weight (exhaust) [100g/mole]
# Isp_frozen, Isp_shifting: Frozen and shifting specific impulse [s]
# qsiCh: Number of condensed phase moles per 100 gram (chamber) [mole]
# qsiEx: Number of condensed phase moles per 100 gram (exhaust) [mole]


class Propellant:

    def __init__(self, ce, pp, kCh, kEx, T0ideal, MCh, MEx, Isp_frozen, Isp_shifting, qsiCh, qsiEx):
        self.ce = ce
        self.pp = pp
        self.kCh = kCh
        self.kEx = kEx
        self.T0ideal = T0ideal
        self.MCh = MCh
        self.MEx = MEx
        self.Isp_frozen = Isp_frozen
        self.Isp_shifting = Isp_shifting
        self.qsiCh = qsiCh
        self.qsiEx = qsiEx


# PROPELLANTS:

kndx = Propellant(0.95, 1795.0 * 1.00, 1.1309, 1.1369, 1712, 42.391 * 1e-3,
                  42.882 * 1e-3, 152.4, 154.1, 0.307, 0.321)
knsb = Propellant(0.95, 1837.3 * 0.95, 1.1362, 1.1484, 1603, 39.857 * 1e-3,
                  40.048 * 1e-3, 151.4, 153.5, 0.316, 0.321)
knsu = Propellant(0.95, 1899.5 * 0.95, 1.1332, 1.1387, 1722, 41.964 * 1e-3,
                  41.517 * 1e-3, 153.3, 155.1, 0.306, 0.321)
kner = Propellant(0.94, 1820.0 * 0.95, 1.1392, 1.1518, 1608, 38.570 * 1e-3,
                  38.779 * 1e-3, 153.8, 156.0, 0.315, 0.321)


def prop_data(prop: str):
    if prop.lower() == 'kndx':
        ce, pp, kCh, kEx, T0ideal, MCh, MEx, Isp_frozen, Isp_shifting, qsiCh, qsiEx = kndx.ce, kndx.pp, \
                                                                                      kndx.kCh, kndx.kEx, \
                                                                                      kndx.T0ideal, kndx.MCh, \
                                                                                      kndx.MEx, kndx.Isp_frozen, \
                                                                                      kndx.Isp_shifting, \
                                                                                      kndx.qsiCh, kndx.qsiEx
    elif prop.lower() == 'knsb':
        ce, pp, kCh, kEx, T0ideal, MCh, MEx, Isp_frozen, Isp_shifting, qsiCh, qsiEx = knsb.ce, knsb.pp, \
                                                                                      knsb.kCh, knsb.kEx, \
                                                                                      knsb.T0ideal, knsb.MCh, \
                                                                                      knsb.MEx, knsb.Isp_frozen, \
                                                                                      knsb.Isp_shifting, \
                                                                                      knsb.qsiCh, knsb.qsiEx
    elif prop.lower() == 'knsu':
        ce, pp, kCh, kEx, T0ideal, MCh, MEx, Isp_frozen, Isp_shifting, qsiCh, qsiEx = knsu.ce, knsu.pp, \
                                                                                      knsu.kCh, knsu.kEx, \
                                                                                      knsu.T0ideal, knsu.MCh, \
                                                                                      knsu.MEx, knsu.Isp_frozen, \
                                                                                      knsu.Isp_shifting, \
                                                                                      knsu.qsiCh, knsu.qsiEx
    elif prop.lower() == 'kner':
        ce, pp, kCh, kEx, T0ideal, MCh, MEx, Isp_frozen, Isp_shifting, qsiCh, qsiEx = kner.ce, kner.pp, \
                                                                                      kner.kCh, kner.kEx, \
                                                                                      kner.T0ideal, kner.MCh, \
                                                                                      kner.MEx, kner.Isp_frozen, \
                                                                                      kner.Isp_shifting, \
                                                                                      kner.qsiCh, kner.qsiEx
    else:
        print('\nPropellant name not recognized. Using values for KNSB instead.')
        ce, pp, kCh, kEx, T0ideal, MCh, MEx, Isp_frozen, Isp_shifting, qsiCh, qsiEx = knsb.ce, knsb.pp, \
                                                                                      knsb.kCh, knsb.kEx, \
                                                                                      knsb.T0ideal, knsb.MCh, \
                                                                                      knsb.MEx, knsb.Isp_frozen, \
                                                                                      knsb.Isp_shifting, \
                                                                                      knsb.qsiCh, knsb.qsiEx
    return ce, pp, kCh, kEx, T0ideal, MCh, MEx, Isp_frozen, Isp_shifting, qsiCh, qsiEx


def burn_rate_coefs(prop: str, P0: float):
    """ Sets the burn rate coefficients 'a' and 'n' according to the instantaneous chamber pressure """
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
    return a, n