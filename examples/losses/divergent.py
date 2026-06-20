"""
Estimates the divergent-nozzle losses for a range of half-angles using
the Machwave library.
"""

from textwrap import dedent

import pandas as pd

import machwave.models.nozzle_losses.components.divergent as divergent

DIVERGENT_ANGLES = (
    0.0,
    2.0,
    4.0,
    6.0,
    8.0,
    10.0,
    12.0,
    15.0,
    20.0,
    24.0,
)

records: list[dict[str, float]] = []

for angle in DIVERGENT_ANGLES:
    divergent_loss = divergent.DivergentLoss.loss_fraction_formula(
        divergent_angle=angle
    )

    records.append(
        {
            "θ_half (deg)": angle,
            "η_div (fraction)": round(divergent_loss, 5),
        }
    )

df = pd.DataFrame(records)

print(
    dedent(
        """
        Nozzle Divergent Half-Angle vs. Loss Fraction
        ---------------------------------------------
        """
    ).strip()
)
print(df.to_string(index=False, justify="center"))
