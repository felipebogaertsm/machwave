from typing import Callable

import pytest

from machwave.models.atmosphere import Atmosphere, Atmosphere1976WindPowerLaw


@pytest.fixture()
def test_atmosphere_up_to_karman_line() -> Callable[[Atmosphere], None]:
    def test(atmosphere: Atmosphere) -> None:
        pressure_at_sea_level = atmosphere.get_pressure(y_amsl=0)
        assert pressure_at_sea_level == pytest.approx(101325, rel=1e-3)

        heights = [0, 5e3, 10e3, 20e3, 30e3, 50e3, 70e3, 100e3]  # 0 up to 100 km

        for i in heights:
            height = float(i)

            # Test density:
            density = atmosphere.get_density(y_amsl=height)
            assert density >= 0
            # Test gravity:
            gravity = atmosphere.get_gravity(y_amsl=height)
            assert gravity >= 0
            # Test pressure:
            pressure = atmosphere.get_pressure(y_amsl=height)
            assert pressure >= 0
            # Test sonic velocity:
            sonic_v = atmosphere.get_sonic_velocity(y_amsl=height)
            assert sonic_v >= 0
            # Test wind velocity:
            wind_v = atmosphere.get_wind_velocity(y_amsl=height)
            assert len(wind_v) == 2
            # Test viscosity:
            viscosity = atmosphere.get_viscosity(y_amsl=height)
            assert viscosity >= 0

    return test


@pytest.fixture()
def atmosphere1976withwindpowerlaw() -> Atmosphere1976WindPowerLaw:
    return Atmosphere1976WindPowerLaw(v_ref=7, z_ref=10, alpha=0.1, direction_deg=60)
