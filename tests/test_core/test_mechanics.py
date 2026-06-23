import numpy as np
import pytest

import machwave.core.mechanics as core_mechanics


class TestGetCenterOfGravity:
    def test_equal_masses_returns_arithmetic_mean(self):
        x = np.array([0.0, 2.0])
        y = np.array([0.0, 4.0])
        z = np.array([0.0, 6.0])
        result = core_mechanics.get_center_of_gravity(x, y, z)
        expected = np.array([3.0, 1.0, 2.0])
        np.testing.assert_allclose(result, expected)

    def test_none_masses_same_as_equal_masses(self):
        x = np.array([1.0, 3.0, 5.0])
        y = np.array([2.0, 4.0, 6.0])
        z = np.array([0.0, 1.0, 2.0])
        result_none = core_mechanics.get_center_of_gravity(x, y, z, masses=None)
        result_equal = core_mechanics.get_center_of_gravity(x, y, z, masses=np.ones(3))
        np.testing.assert_allclose(result_none, result_equal)

    def test_weighted_center_of_gravity(self):
        x = np.array([1.0, 3.0])
        y = np.array([2.0, 4.0])
        z = np.array([0.0, 2.0])
        masses = np.array([1.0, 3.0])
        result = core_mechanics.get_center_of_gravity(x, y, z, masses=masses)
        expected = np.array([1.5, 2.5, 3.5])
        np.testing.assert_allclose(result, expected)

    def test_single_element(self):
        x = np.array([3.0])
        y = np.array([7.0])
        z = np.array([2.0])
        result = core_mechanics.get_center_of_gravity(x, y, z)
        expected = np.array([2.0, 3.0, 7.0])
        np.testing.assert_allclose(result, expected)

    def test_single_element_with_mass(self):
        x = np.array([3.0])
        y = np.array([7.0])
        z = np.array([2.0])
        masses = np.array([5.0])
        result = core_mechanics.get_center_of_gravity(x, y, z, masses=masses)
        expected = np.array([2.0, 3.0, 7.0])
        np.testing.assert_allclose(result, expected)

    def test_output_order_is_z_x_y(self):
        """Return value must follow [z, x, y] convention."""
        x = np.array([1.0])
        y = np.array([2.0])
        z = np.array([3.0])
        result = core_mechanics.get_center_of_gravity(x, y, z)
        assert result[0] == pytest.approx(3.0)  # z
        assert result[1] == pytest.approx(1.0)  # x
        assert result[2] == pytest.approx(2.0)  # y

    def test_returns_ndarray(self):
        x = np.array([1.0, 2.0])
        y = np.array([1.0, 2.0])
        z = np.array([1.0, 2.0])
        result = core_mechanics.get_center_of_gravity(x, y, z)
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float64

    def test_mismatched_coordinates_raise_value_error(self):
        x = np.array([1.0, 2.0])
        y = np.array([1.0])
        z = np.array([1.0, 2.0])
        with pytest.raises(ValueError):
            core_mechanics.get_center_of_gravity(x, y, z)

    def test_mismatched_mass_array_raises_value_error(self):
        x = np.array([1.0, 2.0])
        y = np.array([1.0, 2.0])
        z = np.array([1.0, 2.0])
        masses = np.array([1.0])
        with pytest.raises(ValueError):
            core_mechanics.get_center_of_gravity(x, y, z, masses=masses)

    def test_zero_total_mass_raises_value_error(self):
        x = np.array([1.0, 2.0])
        y = np.array([1.0, 2.0])
        z = np.array([1.0, 2.0])
        masses = np.array([0.0, 0.0])
        with pytest.raises(ValueError):
            core_mechanics.get_center_of_gravity(x, y, z, masses=masses)


class TestGetMomentOfInertiaTensor:
    def test_returns_3x3_ndarray(self):
        x = np.array([1.0, -1.0])
        y = np.array([0.0, 0.0])
        z = np.array([0.0, 0.0])
        result = core_mechanics.get_moment_of_inertia_tensor(x, y, z, element_mass=1.0)
        assert result.shape == (3, 3)
        assert result.dtype == np.float64

    def test_tensor_is_symmetric(self):
        x = np.array([1.0, 0.5, -0.5])
        y = np.array([0.0, 1.0, -1.0])
        z = np.array([0.5, -0.5, 0.5])
        result = core_mechanics.get_moment_of_inertia_tensor(x, y, z, element_mass=0.1)
        np.testing.assert_allclose(result, result.T)

    def test_single_point_on_x_axis(self):
        """Point at (x=1, y=0, z=0): Iyy and Izz = m, Ixx = 0."""
        x = np.array([1.0])
        y = np.array([0.0])
        z = np.array([0.0])
        result = core_mechanics.get_moment_of_inertia_tensor(x, y, z, element_mass=1.0)
        assert result[0, 0] == pytest.approx(1.0)
        assert result[1, 1] == pytest.approx(0.0)
        assert result[2, 2] == pytest.approx(1.0)

    def test_two_symmetric_points_on_z_axis(self):
        """Points at z=±1, all products of inertia zero."""
        x = np.array([0.0, 0.0])
        y = np.array([0.0, 0.0])
        z = np.array([1.0, -1.0])
        result = core_mechanics.get_moment_of_inertia_tensor(x, y, z, element_mass=1.0)
        assert result[1, 1] == pytest.approx(2.0)  # Ixx_physical
        assert result[2, 2] == pytest.approx(2.0)  # Iyy_physical
        assert result[0, 0] == pytest.approx(0.0)  # Izz_physical
        # All off-diagonals should be zero
        np.testing.assert_allclose(result[0, 1], 0.0, atol=1e-15)
        np.testing.assert_allclose(result[0, 2], 0.0, atol=1e-15)
        np.testing.assert_allclose(result[1, 2], 0.0, atol=1e-15)

    def test_products_of_inertia_sign(self):
        """Off-diagonal terms equal negative mass-weighted cross products."""
        x = np.array([2.0])
        y = np.array([3.0])
        z = np.array([0.0])
        m = 0.5
        result = core_mechanics.get_moment_of_inertia_tensor(x, y, z, element_mass=m)
        assert result[1, 2] == pytest.approx(-3.0)
        assert result[2, 1] == pytest.approx(-3.0)

    def test_diagonal_dominates_for_origin_points(self):
        """All points at origin => zero inertia tensor."""
        x = np.zeros(5)
        y = np.zeros(5)
        z = np.zeros(5)
        result = core_mechanics.get_moment_of_inertia_tensor(x, y, z, element_mass=1.0)
        np.testing.assert_allclose(result, np.zeros((3, 3)))

    def test_mismatched_coordinates_raise_value_error(self):
        x = np.array([1.0, 2.0])
        y = np.array([1.0])
        z = np.array([1.0, 2.0])
        with pytest.raises(ValueError):
            core_mechanics.get_moment_of_inertia_tensor(x, y, z, element_mass=1.0)

    def test_known_values_uniformly_distributed_ring(self):
        """4 unit masses equally spaced on the x-y plane at radius 1."""
        coords = np.array([1.0, 0.0, -1.0, 0.0])
        x = coords
        y = np.array([0.0, 1.0, 0.0, -1.0])
        z = np.zeros(4)
        result = core_mechanics.get_moment_of_inertia_tensor(x, y, z, element_mass=1.0)
        assert result[1, 1] == pytest.approx(2.0)  # Ixx_physical in [z,x,y] tensor
        assert result[2, 2] == pytest.approx(2.0)  # Iyy_physical
        assert result[0, 0] == pytest.approx(4.0)  # Izz_physical


class TestGetMomentOfInertiaTensorFromCentralMoments:
    def test_matches_per_element_path(self):
        """The moment form reproduces the per-element tensor for any cloud."""
        rng = np.random.default_rng(0)
        x, y, z = rng.normal(size=(3, 50))
        # Center on the cloud so the per-element path takes relative coordinates.
        x, y, z = x - x.mean(), y - y.mean(), z - z.mean()
        mass = 0.3

        per_element = core_mechanics.get_moment_of_inertia_tensor(x, y, z, mass)

        central = np.array(
            [
                [np.sum(x * x), np.sum(x * y), np.sum(x * z)],
                [np.sum(x * y), np.sum(y * y), np.sum(y * z)],
                [np.sum(x * z), np.sum(y * z), np.sum(z * z)],
            ]
        )
        from_moments = core_mechanics.get_moment_of_inertia_tensor_from_central_moments(
            central, mass
        )
        np.testing.assert_allclose(from_moments, per_element)

    def test_returns_symmetric_3x3(self):
        central = np.array([[2.0, 0.5, -0.3], [0.5, 1.0, 0.2], [-0.3, 0.2, 3.0]])
        result = core_mechanics.get_moment_of_inertia_tensor_from_central_moments(
            central, element_mass=1.0
        )
        assert result.shape == (3, 3)
        assert result.dtype == np.float64
        np.testing.assert_allclose(result, result.T)

    def test_products_of_inertia_are_negated_cross_moments(self):
        """Off-diagonals equal -mass * cross moment, axes [z, x, y]."""
        central = np.zeros((3, 3))
        central[0, 1] = central[1, 0] = 4.0  # x-y cross moment
        result = core_mechanics.get_moment_of_inertia_tensor_from_central_moments(
            central, element_mass=0.5
        )
        assert result[1, 2] == pytest.approx(-2.0)  # Ixy slot in [z, x, y]
        assert result[2, 1] == pytest.approx(-2.0)
