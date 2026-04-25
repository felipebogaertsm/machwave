"""
Estimates the divergent-nozzle losses for a range of half-angles using
the Machwave library.
"""

from textwrap import dedent

import pandas as pd

from machwave.core.compressible_flow.losses import (
    get_nozzle_divergent_percentage_loss,
)

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


def main() -> None:
    records: list[dict[str, float]] = []

    for angle in DIVERGENT_ANGLES:
        eta_div = get_nozzle_divergent_percentage_loss(divergent_angle=angle)

        records.append(
            {
                "θ_half (deg)": angle,
                "η_div (%)": round(eta_div, 3),
            }
        )

    df = pd.DataFrame(records)

    print(
        dedent(
            """
            Nozzle Divergent Half-Angle vs. Percentage Loss
            ---------------------------------------------
            """
        ).strip()
    )
    print(df.to_string(index=False, justify="center"))


if __name__ == "__main__":
    main()
