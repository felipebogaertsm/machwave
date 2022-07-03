# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from abc import ABC, abstractmethod


class Operation(ABC):
    @abstractmethod
    def iterate(self, *args, **kwargs):
        pass

    @abstractmethod
    def print_results(self, *args, **kwargs):
        pass
