# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from abc import ABC

from .test_data import TestData
from operations import Operation
from simulations import Simulation


class Analyze(ABC):
    def __init__(
        self,
        operation: Operation,
        simulation: Simulation,
        test_data: TestData,
    ) -> None:
        self.operation = operation
        self.simulation = simulation
        self.test_data = test_data


class AnalyzeSRMOperation(Analyze):
    pass
