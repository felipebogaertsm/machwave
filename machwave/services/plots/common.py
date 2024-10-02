import pandas as pd
import plotly.express as px


def plot_animated_chart(
    data: pd.DataFrame,
    x: str,
    y: str,
    animation_frame: str,
    animation_group: str | None = None,
    chart_type: str = "scatter",
    **kwargs,
):
    """
    Plots an animated chart using Plotly Express with a slider.

    Args:
        data (pd.DataFrame): DataFrame containing the data to plot.
        x (str): Column name for x-axis values.
        y (str): Column name for y-axis values.
        animation_frame (str): Column name to use for animation frames.
        animation_group (str, optional): Column to identify matching data points
            across frames. Defaults to None.
        chart_type (str, optional): Type of chart ('scatter', 'line', 'bar', etc.).
            Defaults to 'scatter'.
        **kwargs: Additional keyword arguments for the Plotly Express function.

    Returns:
        plotly.graph_objects.Figure: A Plotly Figure object with the animated chart.
    """
    plot_func = getattr(px, chart_type)

    fig = plot_func(
        data_frame=data,
        x=x,
        y=y,
        animation_frame=animation_frame,
        animation_group=animation_group,
        **kwargs,
    )

    fig.update_layout(
        sliders=[
            {
                "currentvalue": {
                    "prefix": f"{animation_frame}: ",
                    "visible": True,
                    "xanchor": "right",
                },
                "pad": {"t": 50},
            }
        ]
    )

    return fig


df = pd.DataFrame(
    {
        "date": [
            "2021-01",
            "2021-01",
            "2021-02",
            "2021-02",
            "2021-03",
            "2021-03",
        ],
        "company": [
            "Company A",
            "Company B",
            "Company A",
            "Company B",
            "Company A",
            "Company B",
        ],
        "price": [150, 200, 160, 210, 170, 220],
    }
)

# Plot animated line chart
fig = plot_animated_chart(
    data=df,
    x="company",
    y="price",
    animation_frame="date",
    chart_type="line",
    title="Stock Prices Over Time",
    labels={"price": "Stock Price", "company": "Company"},
)

fig.show()
