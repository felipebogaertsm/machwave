from typing import Callable

from rocketsolver.models.atmosphere import Atmosphere
from rocketsolver.models.atmosphere.atm_1976 import Atmosphere1976


def test_atmosphere1976_up_to_karman_line(
    test_atmosphere_up_to_karman_line: Callable[[Atmosphere], None]
) -> None:
    test_atmosphere_up_to_karman_line(atmosphere=Atmosphere1976())
