import pytest

import machwave.core.ideal_gas as ideal_gas

# Molar masses [kg/mol] of common gases, from standard reference tables.
M_AIR = 0.0289647
M_O2 = 0.0319988
M_N2 = 0.0280134
M_H2 = 0.00201588


@pytest.mark.parametrize(
    "mass, volume, temperature, molar_mass, expected_pressure",
    [
        # One mole in the standard molar volume (22.414 L/mol) at STP (273.15 K)
        # recovers 1 atm = 101325 Pa.
        (M_AIR, 0.0224140, 273.15, M_AIR, 101324.86),
        # One mole in the IUPAC molar volume (22.711 L/mol) at 273.15 K
        # recovers 1 bar = 100000 Pa.
        (M_AIR, 0.0227110, 273.15, M_AIR, 99999.80),
        # One mole in 24.789 L/mol at 25 °C (298.15 K) recovers 1 bar — the
        # IUPAC standard molar volume at 25 °C, 1 bar.
        (M_AIR, 0.0247890, 298.15, M_AIR, 100002.30),
        # Two moles of O2 in the standard molar volume at STP doubles the
        # pressure to 2 atm, confirming linear scaling with mass.
        (2 * M_O2, 0.0224140, 273.15, M_O2, 202649.72),
    ],
)
def test_get_pressure(mass, volume, temperature, molar_mass, expected_pressure):
    assert ideal_gas.get_pressure(
        mass, volume, temperature, molar_mass
    ) == pytest.approx(expected_pressure, rel=1e-5)


@pytest.mark.parametrize(
    "pressure, volume, temperature, molar_mass, expected_mass",
    [
        # Density of dry air at 0 °C, 1 atm: literature ~1.292 kg/m^3.
        (101325, 1.0, 273.15, M_AIR, 1.29226106),
        # Density of dry air at 15 °C, 1 atm: ISA sea-level value 1.225 kg/m^3.
        (101325, 1.0, 288.15, M_AIR, 1.22499083),
        # Density of oxygen at STP: literature ~1.429 kg/m^3.
        (101325, 1.0, 273.15, M_O2, 1.42762753),
        # Density of nitrogen at STP: literature ~1.2506 kg/m^3.
        (101325, 1.0, 273.15, M_N2, 1.24981878),
        # Density of hydrogen at STP: literature ~0.0899 kg/m^3.
        (101325, 1.0, 273.15, M_H2, 0.08993855),
    ],
)
def test_get_mass(pressure, volume, temperature, molar_mass, expected_mass):
    assert ideal_gas.get_mass(
        pressure, volume, temperature, molar_mass
    ) == pytest.approx(expected_mass, rel=1e-5)


@pytest.mark.parametrize(
    "pressure, volume, temperature, molar_mass",
    [
        (101325, 1.0, 273.15, M_AIR),
        (5_000_000, 0.05, 293.15, M_O2),
        (250_000, 2.5, 350.0, M_H2),
    ],
)
def test_pressure_and_mass_are_inverses(pressure, volume, temperature, molar_mass):
    """`get_mass` and `get_pressure` are inverse operations at fixed V, T, M."""
    mass = ideal_gas.get_mass(pressure, volume, temperature, molar_mass)
    assert ideal_gas.get_pressure(
        mass, volume, temperature, molar_mass
    ) == pytest.approx(pressure, rel=1e-12)
