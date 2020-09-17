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
