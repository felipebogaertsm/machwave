from __future__ import annotations

from typing import Any

import machwave.common.fluid_state as fluid_state_models


class FluidStateFactory:
    @classmethod
    def build(cls, **overrides: Any) -> fluid_state_models.FluidState:
        kwargs: dict[str, Any] = dict(
            fluid_name="N2O",
            pressure=50e5,
            temperature=293.0,
            density=743.0,
        )
        kwargs.update(overrides)
        return fluid_state_models.FluidState(**kwargs)
