"""
Estimates the losses in a motor using the Machwave library.
"""

from itertools import product
from textwrap import dedent

import pandas as pd

import machwave.core.conversions as conversions
import machwave.core.geometric as geometric
import machwave.models.nozzle_losses.components.spp1975 as spp1975

CHAMBER_PRESSURES = (
    150,
    300,
    600,
    1000,
)  # in psi
THROAT_DIAMETERS = (
    1,
    1.5,
    2,
    3,
)  # in inches
MASS_FRACTIONS_OF_CONDENSED_PHASE = (
    0.1,
    0.2,
    0.32,
)  # dimensionless mass fraction
EXPANSION_RATIOS = (
    4,
    6,
    8,
)  # dimensionless
CHARACTERISTIC_LENGTHS = (
    200,
    400,
    600,
    700,
)  # in inches

"""Two-phase flow correction losses"""

records: list[dict[str, float]] = []

for P_ch, d_t, x_c, eps, l_star in product(
    CHAMBER_PRESSURES,
    THROAT_DIAMETERS,
    MASS_FRACTIONS_OF_CONDENSED_PHASE,
    EXPANSION_RATIOS,
    CHARACTERISTIC_LENGTHS,
):
    d_p_um = spp1975.TwoPhaseFlowLoss._average_particle_size(
        chamber_pressure_psi=P_ch,
        mass_fraction_of_condensed_phase=x_c,
        throat_diameter_inch=d_t,
        characteristic_length_inch=l_star,
    )
    throat_diameter_m = conversions.convert_inch_to_meter(d_t)
    # Free chamber volume that yields the swept characteristic length L*.
    free_chamber_volume = conversions.convert_inch_to_meter(
        l_star
    ) * geometric.get_circle_area(throat_diameter_m)
    two_phase_loss = spp1975.TwoPhaseFlowLoss.loss_fraction_formula(
        chamber_pressure=conversions.convert_psi_to_pa(P_ch),
        mass_fraction_of_condensed_phase=x_c,
        expansion_ratio=eps,
        throat_diameter=throat_diameter_m,
        free_chamber_volume=free_chamber_volume,
    )

    records.append(
        {
            "P_ch (psi)": P_ch,
            "d_t (in)": d_t,
            "x_c (mass fraction)": x_c,
            "ε": eps,
            "l* (in)": l_star,
            "d_p (µm)": round(d_p_um, 2),
            "η_2φ (fraction)": round(two_phase_loss, 5),
        }
    )

df = pd.DataFrame(records)

print(
    dedent(
        """
        Two-phase flow loss fractions & particle size
        ---------------------------------------------
        """
    ).strip()
)
print(df.to_string(index=False, justify="center"))
