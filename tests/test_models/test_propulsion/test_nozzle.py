import pytest

import machwave.core.geometric as geometric

from tests.factories import NozzleFactory


@pytest.fixture
def nozzle():
    """1 inch throat, expansion ratio 4."""
    return NozzleFactory.build(
        inlet_diameter=50.8e-3,
        throat_diameter=25.4e-3,
        divergent_angle=20,
        convergent_angle=45,
        expansion_ratio=4,
    )


class TestNozzleGeometry:
    def test_throat_area(self, nozzle):
        assert nozzle.get_throat_area() == pytest.approx(5.0670747910e-4, rel=1e-9)

    def test_throat_area_formula(self, nozzle):
        """Throat area = pi / 4 * D ** 2."""
        assert nozzle.get_throat_area() == pytest.approx(5.0670747910e-4, rel=1e-9)

    def test_outlet_diameter_uses_throat_not_inlet(self, nozzle):
        """outlet_diameter must be throat_diameter * √ε, not inlet_diameter * √ε."""
        assert nozzle.outlet_diameter == pytest.approx(50.8e-3, rel=1e-9)

    def test_outlet_diameter_larger_than_throat(self, nozzle):
        assert nozzle.outlet_diameter > nozzle.throat_diameter

    def test_outlet_area_equals_expansion_ratio_times_throat_area(self, nozzle):
        """A_exit / A_throat = ε by definition."""
        A_exit = geometric.get_circle_area(nozzle.outlet_diameter)
        assert A_exit == pytest.approx(2.0268299164e-3, rel=1e-6)

    def test_outlet_diameter_scales_with_expansion_ratio(self):
        """Doubling expansion ratio should increase exit diameter by √2."""
        n1 = NozzleFactory.build(divergent_angle=15, expansion_ratio=4)
        n2 = NozzleFactory.build(divergent_angle=15, expansion_ratio=8)
        assert n1.outlet_diameter == pytest.approx(50.8e-3, rel=1e-6)
        assert n2.outlet_diameter == pytest.approx(7.1842048969e-2, rel=1e-6)

    def test_outlet_diameter_independent_of_inlet_diameter(self):
        """Two nozzles with same throat but different inlets → same exit diameter."""
        n1 = NozzleFactory.build(inlet_diameter=50e-3, divergent_angle=15)
        n2 = NozzleFactory.build(inlet_diameter=70e-3, divergent_angle=15)
        assert n1.outlet_diameter == pytest.approx(50.8e-3, rel=1e-9)
        assert n2.outlet_diameter == pytest.approx(50.8e-3, rel=1e-9)

    def test_stores_angles(self, nozzle):
        assert nozzle.divergent_angle == 20
        assert nozzle.convergent_angle == 45

    def test_stores_expansion_ratio(self, nozzle):
        assert nozzle.expansion_ratio == 4

    def test_default_boundary_layer_coefficients(self, nozzle):
        """Default c_1/c_2 are for a thick-walled steel nozzle."""
        assert nozzle.c_1 == pytest.approx(0.00506, rel=1e-3)
        assert nozzle.c_2 == pytest.approx(0.0, abs=1e-9)

    def test_custom_boundary_layer_coefficients(self):
        """Ordinary nozzle coefficients can be overridden."""
        n = NozzleFactory.build(c_1=0.003650, c_2=0.000937)
        assert n.c_1 == pytest.approx(0.003650, rel=1e-3)
        assert n.c_2 == pytest.approx(0.000937, rel=1e-3)

    def test_default_discharge_coefficient(self, nozzle):
        """Throat discharge coefficient defaults to 1.0 (ideal nozzle)."""
        assert nozzle.discharge_coefficient == pytest.approx(1.0, rel=1e-9)

    def test_custom_discharge_coefficient(self):
        """Throat discharge coefficient can be overridden."""
        n = NozzleFactory.build(discharge_coefficient=0.95)
        assert n.discharge_coefficient == pytest.approx(0.95, rel=1e-9)
