import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from machwave.common.arrays import replace_array_values


def _create_plot_2d_frame(
    face_map: np.ndarray,
) -> tuple[go.Heatmap, go.Contour, go.Contour]:
    """Create a 2D frame with a heatmap and contour lines of a segment face.

    Args:
        face_map: 2D NumPy array representing the face map.

    Returns:
        List of Plotly traces.
    """
    return (
        go.Heatmap(
            z=face_map,
            colorscale=[
                [0, "rgb(255, 255, 255)"],  # -1 mapped white
                [0.5, "rgb(200, 200, 200)"],  # 0 mapped to white
                [1, "rgb(100, 100, 100)"],  # 1 mapped to dark bluish grey
            ],
            zmin=-1,
            zmax=1,
            showscale=False,
        ),
        go.Contour(  # burn area contour
            name="Burn front",
            z=replace_array_values(face_map, -1, 0),
            contours=dict(
                start=-1,
                end=1,
                size=1,
                coloring="none",
                showlines=True,
            ),
            line=dict(
                color="red",
                width=3,
            ),
            showscale=False,
        ),
        go.Contour(  # inhibited area contour
            name="Inhibitor",
            z=replace_array_values(face_map, 1, 0),
            contours=dict(
                start=-1,
                end=1,
                size=1,
                coloring="none",
                showlines=True,
            ),
            line=dict(
                color="black",
                width=3,
            ),
            showscale=False,
        ),
    )


def plot_2d_face_map(
    face_map: np.ndarray,
) -> go.Figure:
    """Plot a 2D face map with a heatmap and contour lines.

    Args:
        face_map: 2D NumPy array representing the face map.

    Returns:
        Plotly Figure object.
    """
    fig = go.Figure()

    fig.add_traces(_create_plot_2d_frame(face_map))

    fig.update_layout(
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            scaleanchor="y",
            scaleratio=1,
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            scaleanchor="x",
            scaleratio=1,
        ),
        template="none",
        title="Axial Plane Cross-Sectional View",
    )

    return fig


def plot_2d_face_map_animated(
    face_maps: np.ndarray,
    web_distances: np.typing.NDArray[np.float64],
) -> go.Figure:
    """
    Plots an animated 2D face map with heatmaps and contour lines.

    Args:
        face_maps: A 3D NumPy array representing the face maps. The first dimension corresponds to the frames.
        web_distances: An array or list of web distances corresponding to each face map frame.

    Returns:
        A Plotly Figure object with the animation.

    Raises:
        ValueError: If the number of frames does not match the number of face maps.
    """
    num_frames = web_distances.shape[0]

    if num_frames != face_maps.shape[0]:
        raise ValueError("The number of frames must match the number of face maps.")

    initial_face_map = face_maps[0]

    fig = go.Figure()
    fig.add_traces(_create_plot_2d_frame(initial_face_map))

    frames = []
    steps = []
    for i, face_map in enumerate(face_maps):
        frame = go.Frame(
            data=_create_plot_2d_frame(face_map),
            name=str(i),
        )
        frames.append(frame)

        step = dict(
            args=[
                [str(i)],
                dict(
                    mode="immediate",
                    frame=dict(duration=500, redraw=True),
                    transition=dict(duration=0),
                ),
            ],
            label=(f"{web_distances[i]:.1e}"),
            method="animate",
        )
        steps.append(step)

    fig.frames = frames

    fig.update_layout(
        sliders=[
            dict(
                active=0,
                steps=steps,
                currentvalue=dict(
                    prefix=(
                        "Web Distance (m): " if web_distances is not None else "Frame: "
                    ),
                    visible=True,
                    xanchor="right",
                ),
                pad=dict(t=50),
            )
        ],
        updatemenus=[
            dict(
                type="buttons",
                buttons=[
                    dict(
                        label="Play",
                        method="animate",
                        args=[
                            None,
                            dict(
                                frame=dict(duration=500, redraw=True),
                                fromcurrent=True,
                                transition=dict(duration=100),
                            ),
                        ],
                    ),
                    dict(
                        label="Pause",
                        method="animate",
                        args=[
                            [None],
                            dict(
                                frame=dict(duration=0, redraw=False),
                                mode="immediate",
                                transition=dict(duration=0),
                            ),
                        ],
                    ),
                ],
                direction="right",
                showactive=False,
                x=0.1,
                xanchor="left",
                y=1,
                yanchor="top",
            )
        ],
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            scaleanchor="y",
            scaleratio=1,
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            scaleanchor="x",
            scaleratio=1,
        ),
        template="none",
        title="Axial Plane Cross-Sectional View",
    )

    return fig


def plot_3d_face_map_animated(
    face_maps: np.ndarray,
    web_distances: np.typing.NDArray[np.float64],
) -> go.Figure:
    """Plot an animated 3D face map with longitudinal and axial views.

    Displays two side-by-side subplots animated over web distance:

    - **Longitudinal cross-section** (left): a center-cut along the grain
      axis, showing how regression progresses along the grain length.
      Useful for inspecting inhibited-end effects.
    - **Axial cross-section** (right): the face view at the grain midpoint,
      showing the port geometry.

    Args:
        face_maps: 4D array of shape
            ``(n_steps, normalized_length, map_dim, map_dim)`` with values
            -1 (outside), 0 (burned), 1 (propellant).
        web_distances: 1D array of web distances [m] for each step.

    Returns:
        Plotly Figure with animation slider and play/pause controls.

    Raises:
        ValueError: If the first dimension of *face_maps* does not match
            the length of *web_distances*.
    """
    n_steps = web_distances.shape[0]
    if n_steps != face_maps.shape[0]:
        raise ValueError("The number of frames must match the number of face maps.")

    n_z = face_maps.shape[1]
    map_dim = face_maps.shape[2]
    mid_z = n_z // 2
    mid_y = map_dim // 2

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=[
            "Longitudinal Cross-Section",
            "Axial Cross-Section (mid-length)",
        ],
    )

    # --- initial traces ---
    longitudinal_0 = face_maps[0, :, mid_y, :]
    face_0 = face_maps[0, mid_z, :, :]

    for trace in _create_plot_2d_frame(longitudinal_0):
        fig.add_trace(trace, row=1, col=1)

    for trace in _create_plot_2d_frame(face_0):
        fig.add_trace(trace, row=1, col=2)

    n_traces = 6  # 3 per subplot

    # --- frames ---
    frames = []
    steps = []
    for i in range(n_steps):
        longitudinal = face_maps[i, :, mid_y, :]
        face = face_maps[i, mid_z, :, :]

        data = list(_create_plot_2d_frame(longitudinal))
        data.extend(_create_plot_2d_frame(face))

        frames.append(
            go.Frame(
                data=data,
                traces=list(range(n_traces)),
                name=str(i),
            )
        )

        steps.append(
            dict(
                args=[
                    [str(i)],
                    dict(
                        mode="immediate",
                        frame=dict(duration=500, redraw=True),
                        transition=dict(duration=0),
                    ),
                ],
                label=f"{web_distances[i]:.1e}",
                method="animate",
            )
        )

    fig.frames = frames

    fig.update_layout(
        sliders=[
            dict(
                active=0,
                steps=steps,
                currentvalue=dict(
                    prefix="Web Distance (m): ",
                    visible=True,
                    xanchor="right",
                ),
                pad=dict(t=50),
            )
        ],
        updatemenus=[
            dict(
                type="buttons",
                buttons=[
                    dict(
                        label="Play",
                        method="animate",
                        args=[
                            None,
                            dict(
                                frame=dict(duration=500, redraw=True),
                                fromcurrent=True,
                                transition=dict(duration=100),
                            ),
                        ],
                    ),
                    dict(
                        label="Pause",
                        method="animate",
                        args=[
                            [None],
                            dict(
                                frame=dict(duration=0, redraw=False),
                                mode="immediate",
                                transition=dict(duration=0),
                            ),
                        ],
                    ),
                ],
                direction="right",
                showactive=False,
                x=0.1,
                xanchor="left",
                y=1,
                yanchor="top",
            )
        ],
        template="none",
        title="Grain Regression - 3D View",
    )

    fig.update_xaxes(showgrid=False, zeroline=False, row=1, col=1)
    fig.update_yaxes(showgrid=False, zeroline=False, row=1, col=1)
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        scaleanchor="y2",
        scaleratio=1,
        row=1,
        col=2,
    )
    fig.update_yaxes(
        showgrid=False,
        zeroline=False,
        row=1,
        col=2,
    )

    return fig
