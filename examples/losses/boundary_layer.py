"""
Estimates the boundary-layer losses in a motor using the Machwave library.
"""

from itertools import product
from textwrap import dedent

import pandas as pd

import machwave.core.conversions as conversions
import machwave.models.nozzle_losses.components.spp1975 as spp1975

CHAMBER_PRESSURES = (
    150,
    300,
    600,
    1000,
)  # in psi

THROAT_DIAMETERS = (
    1.0,
    1.5,
    2.0,
    3.0,
)  # in inches

EXPANSION_RATIOS = (
    4,
    6,
    8,
)  # dimensionless

TIMES = (
    0.5,
    1.0,
    2.0,
    4.0,
)  # in seconds

# Typical C1 and C2 pairs:
#   - Ordinary steel nozzle:    C1 = 0.003650, C2 = 0.000937
#   - Thick‐walled steel nozzle: C1 = 0.005060, C2 = 0.000000
C1_C2_VALUES = (
    (0.003650, 0.000937),
    (0.005060, 0.000000),
)

records: list[dict[str, float]] = []

for (
    P_ch,
    d_t,
    eps,
    t,
    (c1, c2),
) in product(
    CHAMBER_PRESSURES,
    THROAT_DIAMETERS,
    EXPANSION_RATIOS,
    TIMES,
    C1_C2_VALUES,
):
    boundary_layer_loss = spp1975.BoundaryLayerLoss.compute_loss_fraction(
        chamber_pressure=conversions.convert_psi_to_pa(P_ch),
        throat_diameter=conversions.convert_inch_to_meter(d_t),
        expansion_ratio=eps,
        time=t,
        c_1=c1,
        c_2=c2,
    )

    records.append(
        {
            "P_ch (psi)": P_ch,
            "d_t (in)": d_t,
            "ε": eps,
            "time (s)": t,
            "C1": c1,
            "C2": c2,
            "η_bl (fraction)": round(boundary_layer_loss, 5),
        }
    )

df = pd.DataFrame(records)

print(
    dedent(
        """
        Boundary-layer loss fractions
        -----------------------------
        """
    ).strip()
)
print(df.to_string(index=False, justify="center"))
