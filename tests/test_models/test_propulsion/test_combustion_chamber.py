import pytest

from tests.factories import CombustionChamberFactory


class TestCombustionChamberValidation:
    @pytest.mark.parametrize("casing_inner_diameter", [0.0, -1e-3])
    def test_non_positive_casing_inner_diameter(self, casing_inner_diameter):
        with pytest.raises(ValueError, match="casing_inner_diameter"):
            CombustionChamberFactory.build(casing_inner_diameter=casing_inner_diameter)

    @pytest.mark.parametrize("casing_outer_diameter", [70e-3, 60e-3])
    def test_outer_not_larger_than_inner(self, casing_outer_diameter):
        with pytest.raises(ValueError, match="casing_outer_diameter"):
            CombustionChamberFactory.build(
                casing_inner_diameter=70e-3,
                casing_outer_diameter=casing_outer_diameter,
            )

    @pytest.mark.parametrize("internal_length", [0.0, -0.1])
    def test_non_positive_internal_length(self, internal_length):
        with pytest.raises(ValueError, match="internal_length"):
            CombustionChamberFactory.build(internal_length=internal_length)

    def test_negative_liner_thickness(self):
        with pytest.raises(ValueError, match="thermal_liner_thickness"):
            CombustionChamberFactory.build(thermal_liner_thickness=-1e-3)

    @pytest.mark.parametrize("thermal_liner_thickness", [35e-3, 40e-3])
    def test_liner_leaves_no_open_bore(self, thermal_liner_thickness):
        with pytest.raises(ValueError, match="open bore"):
            CombustionChamberFactory.build(
                casing_inner_diameter=70e-3,
                thermal_liner_thickness=thermal_liner_thickness,
            )
