from abc import ABC
from typing import Callable, Optional

import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter


from . import FMMGrainSegment
from .. import GrainSegment2D
from rocketsolver.services.math.geometric import (
    get_circle_area,
    get_contours,
    get_length,
)


class FMMGrainSegment2D(FMMGrainSegment, GrainSegment2D, ABC):
    """
    Fast Marching Method (FMM) implementation for 2D grain segment.

    This class was inspired by the Andrew Reilley's software openMotor, in
    particular the fmm module.
    openMotor's repository can be accessed at:
    https://github.com/reilleya/openMotor
    """

    def __init__(
        self,
        length: float,
        outer_diameter: float,
        spacing: float,
        inhibited_ends: Optional[int] = 0,
        map_dim: Optional[int] = 1000,
    ) -> None:

        # "Cache" variables:
        self.face_area_interp_func = None

        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            spacing=spacing,
            inhibited_ends=inhibited_ends,
            map_dim=map_dim,
        )

    def get_maps(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Returns a tuple, containing map_x in index 0 and map_y in index 1.
        """
        if self.maps is None:
            self.maps = np.meshgrid(
                np.linspace(-1, 1, self.map_dim),
                np.linspace(-1, 1, self.map_dim),
            )

        return self.maps

    def get_mask(self) -> np.ndarray:
        if self.mask is None:
            map_x, map_y = self.get_maps()
            self.mask = (map_x ** 2 + map_y ** 2) > 1

        return self.mask

    def get_contours(self, web_distance: float) -> np.ndarray:
        map_dist = self.normalize(web_distance)
        return get_contours(self.get_regression_map(), map_dist)

    def get_port_area(self, web_distance: float) -> float | np.ndarray:
        face_area = self.get_face_area(web_distance)
        return get_circle_area(self.outer_diameter) - face_area

    def get_face_area_interp_func(self) -> Callable[[float], float]:
        """
        :return: A function that interpolates the face area in function of
            the (normalized) web thickness.
        :rtype: Callable[[float], float]
        """

        if self.face_area_interp_func is None:
            regression_map = self.get_regression_map()
            max_dist = np.amax(regression_map)

            face_area = []
            web_distance_normalized = []
            valid = np.logical_not(self.get_mask())

            for i in range(int(max_dist * self.map_dim) + 2):
                web_distance_normalized.append(i / self.map_dim)

                face_area.append(
                    self.map_to_area(
                        np.count_nonzero(
                            np.logical_and(
                                regression_map > (web_distance_normalized[-1]),
                                valid,
                            )
                        )
                    )
                )

            face_area = savgol_filter(face_area, 31, 5)
            self.face_area_interp_func = interp1d(
                web_distance_normalized, face_area
            )

        return self.face_area_interp_func

    def get_face_area(self, web_distance: float) -> float:
        """
        NOTE: Still needs to implement control for when web thickness is over.
        """
        map_distance = self.normalize(web_distance)
        return self.get_face_area_interp_func()(map_distance)

    def get_core_perimeter(self, web_distance: float) -> float:
        """
        Gets core perimeter in function of the web thickness traveled.
        """
        contours = self.get_contours(web_distance)

        return np.sum(
            [
                self.map_to_length(get_length(contour, self.map_dim))
                for contour in contours
            ]
        )

    def get_core_area(self, web_distance: float) -> float:
        """
        Calculates the core area in function of the web thickness traveled.
        """
        return self.get_core_perimeter(web_distance) * self.get_length(
            web_distance
        )

    def plot_masked_face(self, web_distance: Optional[float] = 0) -> go.Figure:
        face_map = self.get_face_map(web_distance=web_distance)

        fig = go.Figure(
            data=go.Heatmap(
                z=face_map,
                colorscale=[
                    [0, "rgb(50,50,50)"],
                    [1, "rgb(200,200,200)"],
                ],
            )
        )

        fig.show()

        return fig

    def plot_contours(
        self, number_of_contours: Optional[float] = 1
    ) -> go.Figure:
        fig = go.Figure()

        for contour_index in range(number_of_contours):
            wt = self.get_web_thickness()
            web_fraction = contour_index / number_of_contours
            contours = self.get_contours(web_distance=wt * web_fraction)

            for contour in contours:
                x = np.array([item[0] for item in contour])
                y = np.array([item[1] for item in contour])

                color_level = 255 * (1 - web_fraction)

                fig.add_traces(
                    go.Scatter(
                        x=x,
                        y=y,
                        mode="lines",
                        name=f"{contour_index}",
                        line=dict(
                            color=f"rgb({color_level},{0},{0})",
                        ),
                    )
                )

        fig.show()

        return fig
