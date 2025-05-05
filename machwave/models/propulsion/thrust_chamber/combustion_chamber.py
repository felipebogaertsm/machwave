import numpy as np

from machwave.models.materials import Material
from machwave.models.propulsion.thermals import ThermalLiner
from machwave.services.math.geometric import get_cylinder_volume
from machwave.services.structural import bolted_joints, pressure_vessels


class CombustionChamber:
    def __init__(
        self,
        inner_diameter: float,
        outer_diameter: float,
        liner: ThermalLiner,
        length: float,
        casing_material: Material,
        bulkhead_material: Material,
    ) -> None:
        self.casing_inner_diameter = inner_diameter
        self.outer_diameter = outer_diameter
        self.liner = liner
        self.length = length
        self.casing_material = casing_material
        self.bulkhead_material = bulkhead_material

    @property
    def inner_diameter(self) -> float:
        return self.casing_inner_diameter - 2 * self.liner.thickness

    @property
    def inner_radius(self) -> float:
        return self.inner_diameter / 2

    @property
    def outer_radius(self) -> float:
        return self.outer_diameter / 2

    @property
    def casing_inner_radius(self) -> float:
        return self.inner_diameter / 2

    @property
    def empty_volume(self) -> float:
        return get_cylinder_volume(self.inner_diameter, self.length)

    def get_casing_safety_factor(self, chamber_pressure: float) -> float:
        """
        Calculates the safety factor of the casing.

        Args:
            chamber_pressure (float): The pressure inside the combustion chamber.
        Returns:
            float: The safety factor of the casing.
        """
        casing_burst_pressure = pressure_vessels.get_cylindrical_vessel_burst_pressure(
            inner_radius=self.inner_radius,
            outer_radius=self.outer_radius,
            material_yield_strength=self.casing_material.yield_strength,
        )

        return casing_burst_pressure / chamber_pressure


class BoltedCombustionChamber(CombustionChamber):
    """Combustion-chamber closed by a bolted flange/bulkhead interface."""

    def __init__(
        self,
        inner_diameter: float,
        outer_diameter: float,
        liner: ThermalLiner,
        length: float,
        casing_material: Material,
        bulkhead_material: Material,
        screw_material: Material,
        max_screw_count: int,
        screw_clearance_diameter: float,
        screw_diameter: float,
    ) -> None:
        super().__init__(
            inner_diameter,
            outer_diameter,
            liner,
            length,
            casing_material,
            bulkhead_material,
        )
        self.screw_material = screw_material
        self.max_screw_count = max_screw_count
        self.screw_clearance_diameter = screw_clearance_diameter
        self.screw_diameter = screw_diameter

        self.wall_thickness = (outer_diameter - inner_diameter) / 2

        # Allowable stresses (Pa)
        self._allow_shear_bolt = screw_material.ultimate_strength
        self._allow_shear_wall = casing_material.yield_strength / np.sqrt(3)
        self._allow_bearing_wall = casing_material.yield_strength
        self._allow_tension_wall = casing_material.yield_strength

    def _edge_angle(self) -> float:
        """Central angle bolt-to-inner-edge (deg)."""
        return np.rad2deg(
            np.asin((self.screw_clearance_diameter / 2) / (self.inner_diameter / 2))
        )

    @staticmethod
    def _pitch_angle(n_bolts: int) -> float:
        """Central angle between adjacent bolts (deg)."""
        return np.rad2deg(2 * np.pi / n_bolts)

    def _total_axial_load(self, chamber_pressure: float) -> float:
        """Total axial load on the flange (N)."""
        return chamber_pressure * np.pi * (self.inner_diameter / 2) ** 2

    def _load_per_bolt(self, n_bolts: int, chamber_pressure: float) -> float:
        """Axial load per bolt (N)."""
        return self._total_axial_load(chamber_pressure) / n_bolts

    def get_optimal_fasteners(
        self, chamber_pressure: float
    ) -> tuple[int, float, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Return bolt count with max governing safety factor.

        Args:
            chamber_pressure: Maximum expected chamber pressure (Pa).

        Returns:
            * index (int): zero-based index ⇒ `n_bolts = index + 1`.
            * governing_sf (float): Safety factor at that bolt count.
            * shear_sf (ndarray)
            * tear_sf (ndarray)
            * bearing_sf (ndarray)
            * tension_sf (ndarray)
        """
        m = self.max_screw_count
        shear_sf = np.zeros(m)
        tear_sf = np.zeros(m)
        bearing_sf = np.zeros(m)
        tension_sf = np.zeros(m)

        # Capacities independent of bolt count
        shear_cap = bolted_joints.get_max_shear_load(
            shank_diameter=self.screw_diameter,
            allowable_shear_stress=self._allow_shear_bolt,
        )
        tear_cap = bolted_joints.get_max_tearout_load_cylinder(
            edge_angle=self._edge_angle(),
            wall_thickness=self.wall_thickness,
            outer_diameter=self.outer_diameter,
            allowable_shear_stress=self._allow_shear_wall,
        )
        bearing_cap = bolted_joints.get_max_bearing_load(
            plate_thickness=self.wall_thickness,
            hole_diameter=self.screw_clearance_diameter,
            allowable_bearing_stress=self._allow_bearing_wall,
        )

        total_load = self._total_axial_load(chamber_pressure)

        for i, n in enumerate(range(1, m + 1)):
            F_bolt = total_load / n

            # Per-bolt modes
            shear_sf[i] = shear_cap / F_bolt
            tear_sf[i] = tear_cap / F_bolt
            bearing_sf[i] = bearing_cap / F_bolt

            # Net-section tension across the entire bolt row (global mode)
            tension_cap = bolted_joints.get_max_net_tension_load_cylinder(
                pitch_angle=self._pitch_angle(n),
                wall_thickness=self.wall_thickness,
                hole_diameter=self.screw_clearance_diameter,
                allowable_tensile_stress=self._allow_tension_wall,
                outer_diameter=self.outer_diameter,
                n_bolts_in_row=n,
            )
            tension_sf[i] = tension_cap / total_load

        governing_sf = np.min(
            np.vstack((shear_sf, tear_sf, bearing_sf, tension_sf)), axis=0
        )
        best_idx = int(np.argmax(governing_sf))

        return (
            best_idx,
            governing_sf[best_idx],
            shear_sf,
            tear_sf,
            bearing_sf,
            tension_sf,
        )
