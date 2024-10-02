import numpy as np
import plotly.graph_objects as go

from machwave.services.numpy import replace_array_values


def plot_2d_face_map(
    face_map: np.ndarray,
) -> go.Figure:
    """
    Plots a 2D face map with a heatmap and contour lines.

    Args:
        face_map (np.ndarray): A 2D NumPy array representing the face map.

    Returns:
        go.Figure: A Plotly Figure object.
    """
    fig = go.Figure()

    fig.add_traces(
        [
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
        ]
    )

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

    fig.show()

    return fig
