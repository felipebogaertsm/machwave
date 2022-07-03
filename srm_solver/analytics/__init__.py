# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from abc import ABC
from dataclasses import dataclass

from .test_data import TestData
from operations import Operation
from simulations import Simulation
from utils.strings import convert_string_to_snake_case


@dataclass
class Analyze(ABC):
    operation: Operation
    simulation: Simulation
    test_data: TestData


class AnalyzeSRMOperation(Analyze):
    pass
