# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Stores Recovery class and methods.
"""

from .events import RecoveryEvent


class Recovery:
    def __init__(self) -> None:
        self.events = []

    def add_event(self, recovery_event: RecoveryEvent) -> None:
        self.events.append(recovery_event)
