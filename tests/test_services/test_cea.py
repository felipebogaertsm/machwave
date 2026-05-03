"""Tests for RocketCEAService and create_cea_service factory function.

Tests all three ways of creating/using the service:
1. Via factory with solid propellant
2. Via factory with biliquid propellant
3. Direct instantiation with CEA_Obj

Also validates that returned parameter values are physically reasonable.
"""

import pytest
from rocketcea.cea_obj import CEA_Obj

from machwave.services.cea import (
    RocketCEAService,
    create_cea_service,
    generate_card_string,
)


class TestCreateCEAServiceSolidPropellant:
    """Test creating service via factory with solid propellant."""

    def test_standard_solid_propellant(self):
        """Test factory with standard solid propellant."""
        service = create_cea_service(propellant_name="AP")

        assert service is not None
        assert isinstance(service, RocketCEAService)
        assert service.cea_obj is not None
        assert service.oxidizer_to_fuel_ratio is None

        # Test property values
        chamber_pressure = 3e6
        expansion_ratio = 8.0

        temp = service.get_adiabatic_flame_temperature(chamber_pressure)
        assert 2000 < temp < 4000, f"Unexpected temperature: {temp} K"

        mw_c, k_c = service.get_chamber_properties(chamber_pressure, expansion_ratio)
        assert 0.01 < mw_c < 0.1, f"Unexpected chamber MW: {mw_c} kg/mol"
        assert 1.0 < k_c < 1.5, f"Unexpected chamber k: {k_c}"

        mw_e, k_e = service.get_exhaust_properties(chamber_pressure, expansion_ratio)
        assert 0.01 < mw_e < 0.1, f"Unexpected exhaust MW: {mw_e} kg/mol"
        assert 1.0 < k_e < 1.5, f"Unexpected exit k: {k_e}"

        isp_f, isp_s = service.get_specific_impulse(chamber_pressure, expansion_ratio)
        assert 150 < isp_f < 400, f"Unexpected frozen Isp: {isp_f} s"
        assert 150 < isp_s < 400, f"Unexpected shifting Isp: {isp_s} s"

        qsi_c, qsi_e = service.get_condensed_phase_fractions(
            chamber_pressure, expansion_ratio
        )
        assert 0 <= qsi_c <= 1, f"Unexpected chamber qsi: {qsi_c}"
        assert 0 <= qsi_e <= 1, f"Unexpected exhaust qsi: {qsi_e}"

    def test_custom_solid_propellant(self):
        """Test factory with custom solid propellant card."""
        card = generate_card_string(
            [
                {
                    "name": "KNO3",
                    "formula": {"K": 1.0, "N": 1.0, "O": 3.0},
                    "weight_percent": 65.0,
                    "heat_of_formation": -118200.0,
                    "temperature": 298.15,
                    "density": 2.109,
                },
                {
                    "name": "Sucrose",
                    "formula": {"C": 12.0, "H": 22.0, "O": 11.0},
                    "weight_percent": 35.0,
                    "heat_of_formation": -531900.0,
                    "temperature": 298.15,
                    "density": 1.587,
                },
            ]
        )

        service = create_cea_service(
            propellant_name="TEST_KNSU_SERVICE", card_string=card
        )

        assert isinstance(service, RocketCEAService)

        # Validate KNSU properties
        chamber_pressure = 3e6
        expansion_ratio = 8.0

        temp = service.get_adiabatic_flame_temperature(chamber_pressure)
        # KNSU typically 1600-1800 K
        assert 1500 < temp < 2000, f"KNSU temp out of range: {temp} K"

        mw_c, k_c = service.get_chamber_properties(chamber_pressure, expansion_ratio)
        # KNSU has relatively high MW due to condensed species
        assert 0.035 < mw_c < 0.045, f"KNSU MW out of range: {mw_c} kg/mol"
        assert 1.1 < k_c < 1.2, f"KNSU k out of range: {k_c}"

        isp_f, isp_s = service.get_specific_impulse(chamber_pressure, expansion_ratio)
        # KNSU typical Isp 150-170 s
        assert 140 < isp_f < 180, f"KNSU Isp out of range: {isp_f} s"

        qsi_c, qsi_e = service.get_condensed_phase_fractions(
            chamber_pressure, expansion_ratio
        )
        # KNSU has significant condensed phase (K2CO3)
        assert qsi_c > 0.2, f"KNSU should have significant condensed phase: {qsi_c}"


class TestCreateCEAServiceBiliquidPropellant:
    """Test creating service via factory with biliquid propellant."""

    def test_standard_biliquid_propellant(self):
        """Test factory with standard biliquid propellant."""
        service = create_cea_service(
            oxidizer_name="LOX", fuel_name="RP1", oxidizer_to_fuel_ratio=2.5
        )

        assert isinstance(service, RocketCEAService)
        assert service.oxidizer_to_fuel_ratio == 2.5

        # Validate LOX/RP1 properties
        chamber_pressure = 3e6
        expansion_ratio = 8.0

        temp = service.get_adiabatic_flame_temperature(chamber_pressure)
        # LOX/RP1 typically 3400-3700 K
        assert 3200 < temp < 3800, f"LOX/RP1 temp out of range: {temp} K"

        mw_c, k_c = service.get_chamber_properties(chamber_pressure, expansion_ratio)
        # LOX/RP1 MW around 22-24 g/mol
        assert 0.020 < mw_c < 0.030, f"LOX/RP1 MW out of range: {mw_c} kg/mol"
        assert 1.1 < k_c < 1.2, f"LOX/RP1 k out of range: {k_c}"

        isp_f, isp_s = service.get_specific_impulse(chamber_pressure, expansion_ratio)
        # LOX/RP1 typical Isp 280-320 s
        assert 270 < isp_f < 330, f"LOX/RP1 Isp out of range: {isp_f} s"
        assert 280 < isp_s < 340, f"LOX/RP1 shifting Isp out of range: {isp_s} s"

        # Test tank densities (biliquid specific)
        ox_dens, fuel_dens = service.get_tank_densities()
        # Note: CEA returns densities in g/cm³
        # LOX density ~1.14 g/cm³, RP1 ~0.54 g/cm³ (at boiling point)
        assert 0.8 < ox_dens < 1.3, f"LOX density out of range: {ox_dens} g/cm³"
        assert 0.5 < fuel_dens < 0.9, f"RP1 density out of range: {fuel_dens} g/cm³"

    def test_lox_lh2_high_performance(self):
        """Test LOX/LH2 high-performance propellant."""
        service = create_cea_service(
            oxidizer_name="LOX",
            fuel_name="LH2",
            oxidizer_to_fuel_ratio=5.5,  # Near optimal O/F
        )

        chamber_pressure = 3e6
        expansion_ratio = 8.0

        temp = service.get_adiabatic_flame_temperature(chamber_pressure)
        # LOX/LH2 lower temp than LOX/RP1
        assert 2500 < temp < 3500, f"LOX/LH2 temp out of range: {temp} K"

        mw_c, k_c = service.get_chamber_properties(chamber_pressure, expansion_ratio)
        # LOX/LH2 has very low MW (mostly H2O)
        assert 0.010 < mw_c < 0.020, f"LOX/LH2 MW out of range: {mw_c} kg/mol"
        assert 1.10 < k_c < 1.30, f"LOX/LH2 k out of range: {k_c}"

        isp_f, isp_s = service.get_specific_impulse(chamber_pressure, expansion_ratio)
        # LOX/LH2 highest Isp of chemical propellants
        assert 380 < isp_f < 450, f"LOX/LH2 Isp out of range: {isp_f} s"

    def test_custom_oxidizer_and_fuel(self):
        """Test factory with custom oxidizer and fuel."""
        ox_card = """name CustomN2O4  N 2 O 4  wt%=100.0
h,cal=-4676.0  t(k)=298.15  rho,g/cc=1.443"""

        fuel_card = """name CustomMMH  C 1 H 6 N 2  wt%=100.0
h,cal=12800.0  t(k)=298.15  rho,g/cc=0.866"""

        service = create_cea_service(
            oxidizer_name="CUSTOM_N2O4_TEST_2",
            oxidizer_card_string=ox_card,
            fuel_name="CUSTOM_MMH_TEST_2",
            fuel_card_string=fuel_card,
            oxidizer_to_fuel_ratio=1.65,
        )

        assert isinstance(service, RocketCEAService)
        assert service.oxidizer_to_fuel_ratio == 1.65

        # Validate properties are reasonable
        chamber_pressure = 3e6
        temp = service.get_adiabatic_flame_temperature(chamber_pressure)
        # N2O4/MMH typically ~2300-2800 K
        assert 2200 < temp < 2900, f"Custom propellant temp out of range: {temp} K"


class TestDirectRocketCEAServiceInstantiation:
    """Test direct instantiation of RocketCEAService with CEA_Obj."""

    def test_direct_instantiation_solid(self):
        """Test direct instantiation with solid propellant CEA_Obj."""
        # Manually create CEA object
        cea_obj = CEA_Obj(propName="AP")

        # Direct instantiation
        service = RocketCEAService(cea_obj=cea_obj, oxidizer_to_fuel_ratio=None)

        assert isinstance(service, RocketCEAService)
        assert service.cea_obj is cea_obj
        assert service.oxidizer_to_fuel_ratio is None

        # Verify it works
        temp = service.get_adiabatic_flame_temperature(3e6)
        assert temp > 2000

    def test_direct_instantiation_biliquid(self):
        """Test direct instantiation with biliquid CEA_Obj."""
        # Manually create CEA object for biliquid
        cea_obj = CEA_Obj(oxName="LOX", fuelName="RP1")

        # Direct instantiation with O/F ratio
        service = RocketCEAService(cea_obj=cea_obj, oxidizer_to_fuel_ratio=2.5)

        assert isinstance(service, RocketCEAService)
        assert service.cea_obj is cea_obj
        assert service.oxidizer_to_fuel_ratio == 2.5

        # Verify it works
        temp = service.get_adiabatic_flame_temperature(3e6)
        assert 3200 < temp < 3800

    def test_direct_instantiation_custom_propellant(self):
        """Test direct instantiation after manual propellant registration."""
        from rocketcea.cea_obj import add_new_propellant

        # Manually register propellant
        card = generate_card_string(
            [
                {
                    "name": "TestComp",
                    "formula": {"K": 1.0, "N": 1.0, "O": 3.0},
                    "weight_percent": 100.0,
                    "heat_of_formation": -118200.0,
                    "temperature": 298.15,
                    "density": 2.109,
                }
            ]
        )
        add_new_propellant("MANUAL_REG_TEST", card)

        # Manually create CEA object
        cea_obj = CEA_Obj(propName="MANUAL_REG_TEST")

        # Direct instantiation
        service = RocketCEAService(cea_obj=cea_obj)

        assert isinstance(service, RocketCEAService)
        # KNO3 alone won't burn, so CEA may return 0 or low temp
        # Just check service was created successfully
        assert service.cea_obj is not None


class TestServiceParameterValidation:
    """Test that service returns physically reasonable parameter values."""

    @pytest.fixture
    def lox_rp1_service(self):
        """LOX/RP1 service fixture."""
        return create_cea_service(
            oxidizer_name="LOX", fuel_name="RP1", oxidizer_to_fuel_ratio=2.5
        )

    def test_temperature_pressure_relationship(self, lox_rp1_service):
        """Test that temperature increases with pressure."""
        pressures = [1e6, 3e6, 7e6]
        temps = [lox_rp1_service.get_adiabatic_flame_temperature(p) for p in pressures]

        # Temperature should increase with pressure
        assert temps[1] > temps[0], "Temp should increase with pressure"
        assert temps[2] > temps[1], "Temp should increase with pressure"

    def test_isp_expansion_ratio_relationship(self, lox_rp1_service):
        """Test that Isp increases with expansion ratio."""
        expansion_ratios = [4.0, 8.0, 16.0]
        isps = [
            lox_rp1_service.get_specific_impulse(3e6, eps)[0]
            for eps in expansion_ratios
        ]

        # Isp should increase with expansion ratio
        assert isps[1] > isps[0], "Isp should increase with expansion ratio"
        assert isps[2] > isps[1], "Isp should increase with expansion ratio"

        # Isp gains should diminish (law of diminishing returns)
        gain_1 = isps[1] - isps[0]
        gain_2 = isps[2] - isps[1]
        assert gain_2 < gain_1, "Isp gains should diminish with higher expansion"

    def test_frozen_vs_shifting_isp(self, lox_rp1_service):
        """Test relationship between frozen and shifting Isp."""
        chamber_pressure = 3e6
        expansion_ratio = 8.0

        isp_frozen, isp_shifting = lox_rp1_service.get_specific_impulse(
            chamber_pressure, expansion_ratio
        )

        # Shifting should be >= frozen (equilibrium allows more expansion)
        assert isp_shifting >= isp_frozen, "Shifting Isp should be >= frozen Isp"

        # Difference should be reasonable (typically 5-10%)
        diff_pct = (isp_shifting - isp_frozen) / isp_frozen * 100
        assert 0 <= diff_pct <= 20, f"Isp difference too large: {diff_pct:.1f}%"

    def test_chamber_vs_exhaust_properties(self, lox_rp1_service):
        """Test relationship between chamber and exhaust properties."""
        chamber_pressure = 3e6
        expansion_ratio = 8.0

        mw_c, k_c = lox_rp1_service.get_chamber_properties(
            chamber_pressure, expansion_ratio
        )
        mw_e, k_e = lox_rp1_service.get_exhaust_properties(
            chamber_pressure, expansion_ratio
        )

        # Molecular weights should be similar (within 20%)
        mw_diff_pct = abs(mw_e - mw_c) / mw_c * 100
        assert mw_diff_pct < 20, f"MW difference too large: {mw_diff_pct:.1f}%"

        # Exit k typically higher due to frozen composition
        assert k_e >= k_c * 0.95, "Exit k should be similar or higher"

    def test_parameter_consistency_across_calls(self, lox_rp1_service):
        """Test that repeated calls return consistent values."""
        chamber_pressure = 3e6

        temps = [
            lox_rp1_service.get_adiabatic_flame_temperature(chamber_pressure)
            for _ in range(5)
        ]

        # All calls should return identical values
        assert all(abs(t - temps[0]) < 0.01 for t in temps), "Results not consistent"


class TestServiceEdgeCases:
    """Test service behavior at extreme conditions."""

    def test_very_low_pressure(self):
        """Test service at very low chamber pressure."""
        service = create_cea_service(
            oxidizer_name="LOX", fuel_name="RP1", oxidizer_to_fuel_ratio=2.5
        )

        # 0.1 MPa (1 bar)
        temp = service.get_adiabatic_flame_temperature(1e5)
        assert temp > 0, "Should handle low pressure"

        # Properties should still be reasonable
        mw, k = service.get_chamber_properties(1e5, 8.0)
        assert 0.01 < mw < 0.05
        assert 1.0 < k < 1.5

    def test_very_high_pressure(self):
        """Test service at very high chamber pressure."""
        service = create_cea_service(
            oxidizer_name="LOX", fuel_name="RP1", oxidizer_to_fuel_ratio=2.5
        )

        # 20 MPa (200 bar)
        temp = service.get_adiabatic_flame_temperature(2e7)
        assert temp > 0, "Should handle high pressure"

    def test_extreme_expansion_ratios(self):
        """Test service with extreme expansion ratios."""
        service = create_cea_service(
            oxidizer_name="LOX", fuel_name="RP1", oxidizer_to_fuel_ratio=2.5
        )

        # Very low expansion ratio (subsonic)
        isp_low, _ = service.get_specific_impulse(3e6, 2.0)
        assert isp_low > 0

        # Very high expansion ratio (vacuum)
        isp_high, _ = service.get_specific_impulse(3e6, 50.0)
        assert isp_high > isp_low, "Higher expansion should give higher Isp"


class TestRegistryIsolation:
    """Repeated calls with the same user-facing propellant name but different
    cards must not clobber each other in RocketCEA's process-global registry.

    Without name-mangling the second registration silently wins and both
    services return identical properties.
    """

    def _kno3_sucrose_card(self, kno3_pct: float) -> str:
        return generate_card_string(
            [
                {
                    "name": "KNO3",
                    "formula": {"K": 1.0, "N": 1.0, "O": 3.0},
                    "weight_percent": kno3_pct,
                    "heat_of_formation": -118200.0,
                    "temperature": 298.15,
                    "density": 2.109,
                },
                {
                    "name": "Sucrose",
                    "formula": {"C": 12.0, "H": 22.0, "O": 11.0},
                    "weight_percent": 100.0 - kno3_pct,
                    "heat_of_formation": -531900.0,
                    "temperature": 298.15,
                    "density": 1.587,
                },
            ]
        )

    def test_same_name_different_cards_keep_distinct_properties(self):
        shared_name = "REGISTRY_ISOLATION_PROBE"

        service_a = create_cea_service(
            propellant_name=shared_name, card_string=self._kno3_sucrose_card(65.0)
        )
        service_b = create_cea_service(
            propellant_name=shared_name, card_string=self._kno3_sucrose_card(80.0)
        )

        chamber_pressure = 3e6
        expansion_ratio = 8.0

        temp_a = service_a.get_adiabatic_flame_temperature(chamber_pressure)
        temp_b = service_b.get_adiabatic_flame_temperature(chamber_pressure)
        isp_a, _ = service_a.get_specific_impulse(chamber_pressure, expansion_ratio)
        isp_b, _ = service_b.get_specific_impulse(chamber_pressure, expansion_ratio)

        assert abs(temp_a - temp_b) > 5.0, (
            f"Adiabatic flame temperatures should differ between distinct "
            f"compositions registered under the same name; got "
            f"{temp_a:.2f} K vs {temp_b:.2f} K"
        )
        assert abs(isp_a - isp_b) > 0.5, (
            f"Specific impulses should differ between distinct compositions "
            f"registered under the same name; got {isp_a:.3f} s vs {isp_b:.3f} s"
        )

    def test_same_name_custom_oxidizer_keeps_distinct_properties(self):
        shared_ox_name = "REGISTRY_ISOLATION_OX"
        fuel_card = (
            "name CustomMMH  C 1 H 6 N 2  wt%=100.0\n"
            "h,cal=12800.0  t(k)=298.15  rho,g/cc=0.866"
        )

        ox_card_a = (
            "name CustomOxA  N 2 O 4  wt%=100.0\n"
            "h,cal=-4676.0  t(k)=298.15  rho,g/cc=1.443"
        )
        # Different heat of formation -> different combustion temperature.
        ox_card_b = (
            "name CustomOxB  N 2 O 4  wt%=100.0\n"
            "h,cal=2000.0  t(k)=298.15  rho,g/cc=1.443"
        )

        service_a = create_cea_service(
            oxidizer_name=shared_ox_name,
            oxidizer_card_string=ox_card_a,
            fuel_name="REGISTRY_ISOLATION_FUEL_A",
            fuel_card_string=fuel_card,
            oxidizer_to_fuel_ratio=1.65,
        )
        service_b = create_cea_service(
            oxidizer_name=shared_ox_name,
            oxidizer_card_string=ox_card_b,
            fuel_name="REGISTRY_ISOLATION_FUEL_B",
            fuel_card_string=fuel_card,
            oxidizer_to_fuel_ratio=1.65,
        )

        temp_a = service_a.get_adiabatic_flame_temperature(3e6)
        temp_b = service_b.get_adiabatic_flame_temperature(3e6)

        assert abs(temp_a - temp_b) > 5.0, (
            f"Adiabatic flame temperatures should differ between oxidizers with "
            f"different heats of formation registered under the same name; got "
            f"{temp_a:.2f} K vs {temp_b:.2f} K"
        )


def test_generate_card_string_utility():
    """Test the generate_card_string utility function."""
    components = [
        {
            "name": "KNO3",
            "formula": {"K": 1.0, "N": 1.0, "O": 3.0},
            "weight_percent": 65.0,
            "heat_of_formation": -118200.0,
            "temperature": 298.15,
            "density": 2.109,
        },
        {
            "name": "Sucrose",
            "formula": {"C": 12.0, "H": 22.0, "O": 11.0},
            "weight_percent": 35.0,
            "heat_of_formation": -531900.0,
            "temperature": 298.15,
            "density": 1.587,
        },
    ]

    card = generate_card_string(components)

    # Verify card string format
    assert "name KNO3" in card
    assert "K 1.0 N 1.0 O 3.0" in card
    assert "wt%=65.0" in card
    assert "h,cal=-118200.0" in card
    assert "name Sucrose" in card
    assert "wt%=35.0" in card

    # Empty components should raise error
    with pytest.raises(ValueError, match="No components provided"):
        generate_card_string([])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
