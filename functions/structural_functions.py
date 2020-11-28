import numpy as np
import matplotlib.pyplot as plt


class MotorStructure:
    def __init__(self, sf, m_motor, D_in, D_out, D_chamber, L_chamber, D_screw, D_clearance, D_throat, A_throat, C1, C2,
                 Div_angle):
        self.sf = sf
        self.m_motor = m_motor
        self.D_in = D_in
        self.D_out = D_out
        self.D_chamber = D_chamber
        self.L_chamber = L_chamber
        self.D_screw = D_screw
        self.D_clearance = D_clearance
        self.D_throat = D_throat
        self.A_throat = A_throat
        self.C1 = C1
        self.C2 = C2
        self.Div_angle = Div_angle

    def bulkhead_thickness(self, Y_bulkhead, P0):
        """ Returns the thickness of a plane bulkhead for a pressure vessel """
        bulkhead_t = self.D_in * np.sqrt((0.75 * np.max(P0)) / (Y_bulkhead / self.sf))
        return bulkhead_t

    def nozzle_thickness(self, Y_nozzle, Div_angle, Conv_angle, P0):
        """ Returns nozzle convergent and divergent thickness """
        nozzle_conv_t = (np.max(P0) * self.D_in / 2) / (Y_nozzle / self.sf - 0.6 * np.max(P0)
                                                        * (np.cos(np.deg2rad(Conv_angle))))
        nozzle_div_t = (np.max(P0) * self.D_in / 2) / (Y_nozzle / self.sf - 0.6 * np.max(P0)
                                                       * (np.cos(np.deg2rad(Div_angle))))
        return nozzle_conv_t, nozzle_div_t

    def casing_safety_factor(self, Y_cc, P0):
        """ Returns the thickness for a cylindrical pressure vessel """
        thickness = (self.D_out - self.D_in) / 2
        P_bursting = (Y_cc * thickness) / (self.D_in * 0.5 + 0.6 * thickness)
        casing_sf = P_bursting / np.max(P0)
        return casing_sf

    def optimal_fasteners(self, max_number_of_screws, P0, Y_cc, U_screw):
        shear_sf = np.zeros(max_number_of_screws)
        tear_sf = np.zeros(max_number_of_screws)
        compression_sf = np.zeros(max_number_of_screws)

        for i in range(1, max_number_of_screws + 1):
            Area_shear = (self.D_screw ** 2) * np.pi * 0.25
            Area_tear = (((np.pi * 0.25 * ((self.D_out ** 2) - (self.D_in ** 2))) / i) -
                         (np.arcsin((self.D_clearance / 2) / (self.D_in / 2))) * 0.25
                         * ((self.D_out ** 2) - (self.D_in ** 2)))
            Area_compression = ((self.D_out / 2) - (self.D_in / 2)) * self.D_clearance
            forceFastener = (np.max(P0) * (np.pi * (self.D_in / 2) ** 2)) / i
            shear_stress = forceFastener / Area_shear
            shear_sf[i - 1] = U_screw / shear_stress
            tear_stress = forceFastener / Area_tear
            tear_sf[i - 1] = (Y_cc / np.sqrt(3)) / tear_stress
            compression_stress = forceFastener / Area_compression
            compression_sf[i - 1] = Y_cc / compression_stress

        sfFastener = np.vstack((shear_sf, tear_sf, compression_sf))
        max_sf_fastener = np.max(np.min(sfFastener, axis=0))
        optimal_fasteners = np.argmax(np.min(sfFastener, axis=0))
        return optimal_fasteners, max_sf_fastener, shear_sf, tear_sf, compression_sf
