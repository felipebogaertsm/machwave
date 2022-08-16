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
class Analyze(ABC):
    """
    :param pd.DataFrame data: Dataframe with the experimental data obtained
        from the test. Its columns will depend on the type of operation being
        analyzed.
    :rtype: None
    """

    data: pd.DataFrame

    def get_from_df(self, column_name: str) -> np.ndarray:
        return self.data[column_name].to_numpy()
