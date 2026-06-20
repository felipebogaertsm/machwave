"""
Solid Performance Program 1975 nozzle loss components.

References:
    Coats, D. E., Levine, J. N., Nickerson, G. R., Tyson, T. J., Cohen, N. S.,
    Harry, D. P. III, & Price, C. F. (1975).
    A Computer Program for the Prediction of Solid Propellant Rocket Motor Performance.
    Volume I (Technical Report AFRPL-TR-75-36, DTIC Accession AD-A015 140). Air Force
    Rocket Propulsion Laboratory, Edwards AFB, CA.
"""

from __future__ import annotations

import numpy as np

import machwave.core.conversions as conversions
import machwave.core.geometric as geometric
import machwave.models.nozzle_losses.base as losses_base
import machwave.models.nozzle_losses.components.base as components_base
import machwave.models.propellants as propellants

KINETICS_LOSS_PRESSURE_THRESHOLD_PSI = 200


class KineticsLoss(components_base.LossComponent):
    """
    Chemical kinetics loss.

    Kinetics loss accounts for the decrement in performance due to incomplete heat
    transfer of latent to sensible heat caused by the finite time required for the
    gas-phase chemical reactions to occur. Both specific impulses must be evaluated at
    the same expansion ratio.

    A pressure correction dampens the kinetics loss above
    `KINETICS_LOSS_PRESSURE_THRESHOLD_PSI`.
    """

    name = "kinetics_loss"
    label = "kinetics loss"
    applicable_mixture_types = frozenset({propellants.MixtureType.SOLID})
    target = losses_base.ThrustCoefficientTermTarget.BOTH
    timestep_parameter_map = {
        "i_sp_frozen": "propellant_properties.i_sp_frozen",
        "i_sp_shifting": "propellant_properties.i_sp_shifting",
        "chamber_pressure": "chamber_pressure",
    }
    typical_range = (0.001, 0.05)

    @staticmethod
    def compute_loss_fraction(
        i_sp_frozen: float, i_sp_shifting: float, chamber_pressure: float
    ) -> float:
        """
        Return the kinetics loss fraction.

        Args:
            i_sp_frozen: Specific impulse of the frozen flow [s].
            i_sp_shifting: Specific impulse of the shifting flow [s].
            chamber_pressure: Chamber pressure [Pa].

        Returns:
            Kinetics loss fraction in [0, 1].
        """
        chamber_pressure_psi = conversions.convert_pa_to_psi(chamber_pressure)
        i_sp_ratio = i_sp_frozen / i_sp_shifting

        if chamber_pressure_psi < KINETICS_LOSS_PRESSURE_THRESHOLD_PSI:
            pressure_correction = 1.0
        else:
            pressure_correction = (
                KINETICS_LOSS_PRESSURE_THRESHOLD_PSI / chamber_pressure_psi
            )

        return 0.333 * (1 - i_sp_ratio) * pressure_correction


class BoundaryLayerLoss(components_base.LossComponent):
    """
    Boundary layer loss, calibrated for solid motors.

    Boundary layer loss accounts for the decrement in performance due to viscous and
    heat-transfer effects on the nozzle walls. It is time dependent: the exponential
    transient is important in motors with short burn durations (under 4 s). Dependence
    on expansion ratio represents the effect of the amount of nozzle surface area.

    Time constant `c_2` comes from analysis of the transient heating of a BATES motor.
    Time constant `c_1` was obtained from a direct measurement of the heat loss in a
    BATES motor, among other things. Typical values:

    - Ordinary nozzle: `c_1 = 0.003650`, `c_2 = 0.000937`.
    - Solid steel nozzle with thick walls: `c_1 = 0.005060`, `c_2 = 0.0`.
    """

    name = "boundary_layer_loss"
    label = "boundary layer loss"
    applicable_mixture_types = frozenset({propellants.MixtureType.SOLID})
    target = losses_base.ThrustCoefficientTermTarget.BOTH
    timestep_parameter_map = {
        "chamber_pressure": "chamber_pressure",
        "throat_diameter": "nozzle.throat_diameter",
        "expansion_ratio": "nozzle.expansion_ratio",
        "time": "time",
        "c_1": "nozzle.c_1",
        "c_2": "nozzle.c_2",
    }
    typical_range = (0.001, 0.03)

    @staticmethod
    def compute_loss_fraction(
        chamber_pressure: float,
        throat_diameter: float,
        expansion_ratio: float,
        time: float,
        c_1: float,
        c_2: float,
    ) -> float:
        """
        Return the boundary layer loss fraction.

        Args:
            chamber_pressure: Chamber pressure [Pa].
            throat_diameter: Throat diameter [m].
            expansion_ratio: Nozzle expansion ratio.
            time: Time [s].
            c_1: First boundary-layer loss coefficient.
            c_2: Second boundary-layer loss coefficient.

        Returns:
            Boundary layer loss fraction in [0, 1].
        """
        chamber_pressure_psi = conversions.convert_pa_to_psi(chamber_pressure)
        throat_diameter_inch = conversions.convert_meter_to_inch(throat_diameter)

        term_1 = c_1 * (chamber_pressure_psi**0.8) / (throat_diameter_inch**0.2)
        term_2 = 1 + 2 * np.exp(
            (-c_2 * chamber_pressure_psi**0.8 * time) / (throat_diameter_inch**0.2)
        )
        term_3 = 1 + 0.016 * (expansion_ratio - 9)

        return 0.01 * term_1 * term_2 * term_3


class TwoPhaseFlowLoss(components_base.LossComponent):
    """
    Two-phase (condensed-phase) flow loss, for solid motors.

    Two-phase flow loss accounts for the decrement in performance due to the presence
    of a condensed phase in the combustion products.
    """

    name = "two_phase_flow_loss"
    label = "two-phase flow loss"
    applicable_mixture_types = frozenset({propellants.MixtureType.SOLID})
    target = losses_base.ThrustCoefficientTermTarget.BOTH
    timestep_parameter_map = {
        "chamber_pressure": "chamber_pressure",
        "mass_fraction_of_condensed_phase": "propellant_properties.qsi_chamber",
        "expansion_ratio": "nozzle.expansion_ratio",
        "throat_diameter": "nozzle.throat_diameter",
        "free_chamber_volume": "free_chamber_volume",
    }
    typical_range = (0.001, 0.05)

    @staticmethod
    def compute_loss_fraction(
        chamber_pressure: float,
        mass_fraction_of_condensed_phase: float,
        expansion_ratio: float,
        throat_diameter: float,
        free_chamber_volume: float,
    ) -> float:
        """
        Return the two-phase flow loss fraction.

        Args:
            chamber_pressure: Chamber pressure [Pa].
            mass_fraction_of_condensed_phase: Mass fraction of the condensed phase.
            expansion_ratio: Nozzle expansion ratio.
            throat_diameter: Throat diameter [m].
            free_chamber_volume: Free chamber volume [m^3].

        Returns:
            Two-phase flow loss fraction in [0, 1].
        """
        chamber_pressure_psi = conversions.convert_pa_to_psi(chamber_pressure)
        throat_diameter_inch = conversions.convert_meter_to_inch(throat_diameter)
        characteristic_length_inch = conversions.convert_meter_to_inch(
            free_chamber_volume / geometric.get_circle_area(throat_diameter)
        )

        particle_size_um: float = TwoPhaseFlowLoss._average_particle_size(
            chamber_pressure_psi,
            mass_fraction_of_condensed_phase,
            throat_diameter_inch,
            characteristic_length_inch,
        )

        if mass_fraction_of_condensed_phase >= 0.09:
            c_4 = 0.5
            if throat_diameter_inch < 1.0:
                c_3, c_5, c_6 = 9.0, 1.0, 1.0
            elif throat_diameter_inch < 2.0:
                c_3, c_5, c_6 = 9.0, 1.0, 0.8
            else:
                if particle_size_um < 4.0:
                    c_3, c_5, c_6 = 13.4, 0.8, 0.8
                elif particle_size_um <= 8.0:
                    c_3, c_5, c_6 = 10.2, 0.8, 0.4
                else:
                    c_3, c_5, c_6 = 7.58, 0.8, 0.33
        else:  # mass_fraction_of_condensed_phase < 0.09
            c_4 = 1.0
            if throat_diameter_inch < 1.0:
                c_3, c_5, c_6 = 30.0, 1.0, 1.0
            elif throat_diameter_inch < 2.0:
                c_3, c_5, c_6 = 30.0, 1.0, 0.8
            else:
                if particle_size_um < 4.0:
                    c_3, c_5, c_6 = 44.5, 0.8, 0.8
                elif particle_size_um <= 8.0:
                    c_3, c_5, c_6 = 34.0, 0.8, 0.4
                else:
                    c_3, c_5, c_6 = 25.2, 0.8, 0.33

        numerator = (mass_fraction_of_condensed_phase**c_4) * (particle_size_um**c_5)
        denominator = (
            (chamber_pressure_psi**0.15)
            * (expansion_ratio**0.08)
            * (throat_diameter_inch**c_6)
        )

        return 0.01 * c_3 * numerator / denominator

    @staticmethod
    def _average_particle_size(
        chamber_pressure_psi: float,
        mass_fraction_of_condensed_phase: float,
        throat_diameter_inch: float,
        characteristic_length_inch: float,
    ) -> float:
        """
        Return the two-phase flow average particle size [um].

        Combines theories of particle growth by condensation in the chamber and
        collisions in the nozzle.

        Args:
            chamber_pressure_psi: Chamber pressure [psi].
            mass_fraction_of_condensed_phase: Mass fraction of the condensed phase.
            throat_diameter_inch: Throat diameter [in].
            characteristic_length_inch: Characteristic length [in].

        Returns:
            Two-phase flow average particle size [um].
        """
        return (
            0.454
            * chamber_pressure_psi ** (1 / 3)
            * mass_fraction_of_condensed_phase ** (1 / 3)
            * (1 - np.exp(-0.004 * characteristic_length_inch))
            * (1 + 0.045 * throat_diameter_inch)
        )
