"""
Visualize a finocyl grain segment in 3D with Plotly.

Renders the port (the perforation through the propellant) as a solid surface so
the central bore, the radial fins, and the tapered transition into the plain
cylindrical section are all visible, wrapped by a translucent casing for
context. The port surface is extracted from the FMM face map with marching
cubes. Pass a non-zero web distance to inspect a partially regressed grain.
"""

import numpy as np
import plotly.graph_objects as go
from skimage import measure

import machwave.models.grain.geometries as grain_geometries


def build_finocyl_figure(
    segment: grain_geometries.FinocylGrainSegment,
    web_distance: float = 0.0,
) -> go.Figure:
    """Return a 3D Plotly figure of the segment's port and casing."""
    face_map = segment.get_face_map(web_distance=web_distance)

    port = face_map == 0
    # Drop the end-face slices so the bore renders as an open channel rather
    # than being capped by full-diameter disks.
    port[0] = False
    port[-1] = False

    padded = np.pad(
        port.astype(np.float64), pad_width=1, mode="constant", constant_values=0.0
    )
    vertices, faces, _, _ = measure.marching_cubes(padded, level=0.5)

    n_z, n_y, n_x = face_map.shape
    radius = segment.outer_diameter / 2
    axial = (vertices[:, 0] - 1) / (n_z - 1) * segment.length
    transverse_y = -radius + (vertices[:, 1] - 1) / (n_y - 1) * (2 * radius)
    transverse_x = -radius + (vertices[:, 2] - 1) / (n_x - 1) * (2 * radius)

    port_mesh = go.Mesh3d(
        x=transverse_x,
        y=transverse_y,
        z=axial,
        i=faces[:, 0],
        j=faces[:, 1],
        k=faces[:, 2],
        color="rgb(255, 140, 0)",
        flatshading=True,
        lighting=dict(
            ambient=0.35, diffuse=0.9, specular=0.3, roughness=0.5, fresnel=0.2
        ),
        lightposition=dict(x=10000, y=10000, z=15000),
        name="Port",
    )

    fig = go.Figure(data=[_casing_surface(radius, segment.length), port_mesh])
    fig.update_layout(
        title="Finocyl Grain Segment - Port and Casing",
        scene=dict(
            xaxis_title="x [m]",
            yaxis_title="y [m]",
            zaxis_title="axial z [m]",
            aspectmode="data",
            camera=dict(eye=dict(x=1.6, y=1.6, z=0.9)),
        ),
        template="none",
    )
    return fig


def _casing_surface(radius: float, length: float) -> go.Surface:
    """Return a translucent cylinder marking the casing (outer diameter)."""
    angle = np.linspace(0.0, 2 * np.pi, 80)
    axial = np.array([0.0, length])
    angle_grid, axial_grid = np.meshgrid(angle, axial)
    return go.Surface(
        x=radius * np.cos(angle_grid),
        y=radius * np.sin(angle_grid),
        z=axial_grid,
        colorscale=[[0, "rgb(160, 160, 160)"], [1, "rgb(160, 160, 160)"]],
        opacity=0.12,
        showscale=False,
        name="Casing",
    )


def main():
    finocyl_segment = grain_geometries.FinocylGrainSegment(
        length=120e-3,
        outer_diameter=80e-3,
        core_diameter=24e-3,
        number_of_fins=6,
        fin_length=16e-3,
        fin_width=6e-3,
        finned_length=70e-3,
        transition_length=15e-3,
    )

    build_finocyl_figure(finocyl_segment).show()


if __name__ == "__main__":
    main()
