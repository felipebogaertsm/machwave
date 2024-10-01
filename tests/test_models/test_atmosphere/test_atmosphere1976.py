from typing import Callable

from machwave.models.atmosphere import Atmosphere
from machwave.models.atmosphere.atm_1976 import Atmosphere1976


def test_atmosphere1976_up_to_karman_line(
    test_atmosphere_up_to_karman_line: Callable[[Atmosphere], None]
) -> None:
    test_atmosphere_up_to_karman_line(atmosphere=Atmosphere1976())


def test_atmosphere1976windpowerlaw_up_to_karman_line(
    test_atmosphere_up_to_karman_line: Callable[[Atmosphere], None],
    atmosphere1976withwindpowerlaw: Atmosphere1976,
) -> None:
    test_atmosphere_up_to_karman_line(
        atmosphere=atmosphere1976withwindpowerlaw
    )
