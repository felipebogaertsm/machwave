# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from abc import ABC
from dataclasses import dataclass

import pandas as pd
import numpy as np


@dataclass
class TestData(ABC):
    """
    :param pd.DataFrame data: Dataframe with the experimental data obtained
        from the test. Its columns will depend on the type of operation being
        analyzed.
    :rtype: None
    """

    data: pd.DataFrame

    def get_from_df(self, column_name: str) -> np.array:
        return self.data[column_name].to_numpy()


class SRMTestData(TestData):
    def get_thrust(self, col_name="Thrust") -> np.array:
        return self.get_from_df(col_name)

    def get_time(self, col_name="Time") -> np.array:
        return self.get_from_df(col_name)

    def get_pressure(self, col_name="Pressure") -> np.array:
        return self.get_from_df(col_name)

    def get_temperatures(self, col_name_startswith="Temperature") -> np.array:
        """
        :param str col_name_startswith: The name that the column starts with
        :return: An array of temperatures captured by each thermopar.
        :rtype: np.array
        """
        col_names = self.data.columns.values().tolist()
        temperature_col_names = [
            col_name
            for col_name in col_names
            if col_name.startswith(col_name_startswith)
        ]

        temperatures = np.array([])

        for name in temperature_col_names:
            temperatures = np.append(temperatures, self.get_from_df(name))

        return temperatures
