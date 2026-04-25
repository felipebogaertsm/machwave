"""
Estimates the losses in a motor using the Machwave library.
"""

from itertools import product
from textwrap import dedent

import pandas as pd

from machwave.core import losses

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
    d_p_um = losses._get_two_phase_phase_loss_particle_size(
        chamber_pressure_psi=P_ch,
        xi=x_c,
        throat_diameter_inch=d_t,
        characteristic_length_inch=l_star,
    )
    eta_2p = 100 * (0.012 + 0.83 * eps**-0.35) * x_c
    eta_2p = losses.get_two_phase_flow_percentage_loss(
        chamber_pressure_psi=P_ch,
        mass_fraction_of_condensed_phase=x_c,
        expansion_ratio=eps,
        throat_diameter_inch=d_t,
        characteristic_length_inch=l_star,
    )

    records.append(
        {
            "P_ch (psi)": P_ch,
            "d_t (in)": d_t,
            "x_c (mass fraction)": x_c,
            "ε": eps,
            "l* (in)": l_star,
            "d_p (µm)": round(d_p_um, 2),
            "η_2φ (%)": round(eta_2p, 3),
        }
    )

df = pd.DataFrame(records)

print(
    dedent(
        """
        Two-phase flow percentage losses & particle size
        -----------------------------------------------
        """
    ).strip()
)
print(df.to_string(index=False, justify="center"))
