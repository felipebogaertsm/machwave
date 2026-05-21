import numpy as np

import machwave.models.grain as grain
import machwave.models.grain.base as grain_base
import machwave.models.grain.fmm as grain_fmm


class WagonWheelGrainSegment(grain_fmm.FMMGrainSegment2D):
    """Wagon-wheel grain segment with a central core and radial spoke ports."""

    def __init__(
        self,
        length: float,
        outer_diameter: float,
        core_diameter: float,
        number_of_ports: int,
        port_inner_diameter: float,
        port_outer_diameter: float,
        port_angular_width: float,
        inhibited_surfaces: grain_base.InhibitedSurfaces | None = None,
        density_ratio: float = 1.0,
    ) -> None:
        """
        Initialize a wagon-wheel grain segment.

        Args:
            length: Segment length [m].
            outer_diameter: Outer diameter [m].
            core_diameter: Central core diameter [m].
            number_of_ports: Number of radial spoke ports (must be even).
            port_inner_diameter: Inner radial extent of each spoke port [m].
            port_outer_diameter: Outer radial extent of each spoke port [m].
            port_angular_width: Angular width of each spoke port [deg].
            inhibited_surfaces: Surfaces inhibited from burning.
            density_ratio: Ratio of real to ideal propellant density.
        """
        self.core_diameter = core_diameter
        self.number_of_ports = int(number_of_ports)
        self.port_inner_diameter = port_inner_diameter
        self.port_outer_diameter = port_outer_diameter
        self.port_angular_width = port_angular_width

        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            inhibited_surfaces=inhibited_surfaces,
            density_ratio=density_ratio,
        )

    def validate(self) -> None:
        """Validate wagon-wheel segment geometry."""
        super().validate()

        if not self.number_of_ports > 0:
            raise grain.GrainGeometryError(
                f"Number of ports must be positive, got {self.number_of_ports}"
            )
        if not self.number_of_ports < 12:
            raise grain.GrainGeometryError(
                f"Number of ports must be less than 12, got {self.number_of_ports}"
            )
        if not self.number_of_ports % 2 == 0:
            raise grain.GrainGeometryError(
                f"Number of ports must be even, got {self.number_of_ports}"
            )
        if not isinstance(self.number_of_ports, int):
            raise grain.GrainGeometryError(
                f"Number of ports must be an integer, got {type(self.number_of_ports).__name__}"
            )
        if not self.port_inner_diameter > self.core_diameter:
            raise grain.GrainGeometryError(
                f"Port inner diameter ({self.port_inner_diameter}) must be greater than "
                f"core diameter ({self.core_diameter})"
            )
        if not self.port_outer_diameter > self.port_inner_diameter:
            raise grain.GrainGeometryError(
                f"Port outer diameter ({self.port_outer_diameter}) must be greater than "
                f"port inner diameter ({self.port_inner_diameter})"
            )
        if not self.port_angular_width > 0:
            raise grain.GrainGeometryError(
                f"Port angular width must be positive, got {self.port_angular_width}"
            )
        max_angular_width = 360 / self.number_of_ports
        if not self.port_angular_width < max_angular_width:
            raise grain.GrainGeometryError(
                f"Port angular width ({self.port_angular_width}) must be less than "
                f"{max_angular_width} (360 / {self.number_of_ports})"
            )

    def get_initial_face_map(self) -> np.typing.NDArray[np.int_]:
        """NOTE: Still needs to correctly implement wagon wheel ports."""
        map_x, map_y = self.get_maps()
        core_map = self.get_empty_face_map()

        core_diameter_norm = self.normalize(self.core_diameter)
        port_inner_diameter_norm = self.normalize(self.port_inner_diameter)
        port_outer_diameter_norm = self.normalize(self.port_outer_diameter)

        radius = np.sqrt(map_x**2 + map_y**2)

        core_map[radius < core_diameter_norm / 2] = 0

        for port_index in range(int(self.number_of_ports)):
            displacement_angle = 2 * np.pi / self.number_of_ports * (port_index)

            theta_2 = np.deg2rad(self.port_angular_width / 2) + displacement_angle
            theta_1 = displacement_angle - np.deg2rad(self.port_angular_width / 2)

            map_x_y_arctan = np.arctan(map_y / map_x)

            core_map[
                (radius < port_outer_diameter_norm / 2)
                & (radius > port_inner_diameter_norm / 2)
                & (np.abs(map_x_y_arctan) < theta_2)
                & (np.abs(map_x_y_arctan) > theta_1)
            ] = 0

        return core_map
