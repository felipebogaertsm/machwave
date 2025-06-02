"""
Estimates the kinetics‐related losses in a motor using the Machwave library.
"""

from itertools import product
from textwrap import dedent

import pandas as pd

from machwave.core.losses import get_kinetics_percentage_loss

CHAMBER_PRESSURES_PSI = (
    150,
    300,
    600,
    1000,
)  # in psi

# Pairs of (I_sp_th_frozen [s], I_sp_th_shifting [s])
ISP_TH_PAIRS = (
    (151.4, 153.5),
    (250.0, 260.0),
    (270.0, 285.0),
)  # seconds

records: list[dict[str, float]] = []

for P_ch, (i_sp_frozen, i_sp_shifting) in product(
    CHAMBER_PRESSURES_PSI,
    ISP_TH_PAIRS,
):
    eta_kin = get_kinetics_percentage_loss(
        i_sp_th_frozen=i_sp_frozen,
        i_sp_th_shifting=i_sp_shifting,
        chamber_pressure_psi=P_ch,
    )

    records.append(
        {
            "P_ch (psi)": P_ch,
            "Isp_frozen (s)": i_sp_frozen,
            "Isp_shifting (s)": i_sp_shifting,
            "η_kin (%)": round(eta_kin, 3),
        }
    )

df = pd.DataFrame(records)

print(
    dedent(
        """
        Kinetics percentage losses
        --------------------------
        """
    ).strip()
)
print(df.to_string(index=False, justify="center"))
