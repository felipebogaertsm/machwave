import pytest

from tests.factories import CombustionChamberFactory


class TestCombustionChamberValidation:
    @pytest.mark.parametrize("inner_diameter", [0.0, -1e-3])
    def test_non_positive_inner_diameter(self, inner_diameter):
        with pytest.raises(ValueError, match="inner_diameter"):
            CombustionChamberFactory.build(inner_diameter=inner_diameter)

    @pytest.mark.parametrize("internal_length", [0.0, -0.1])
    def test_non_positive_internal_length(self, internal_length):
        with pytest.raises(ValueError, match="internal_length"):
            CombustionChamberFactory.build(internal_length=internal_length)
