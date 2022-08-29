# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from abc import ABC, abstractmethod

from rocketsolver.operations import Operation


class SimulationParameters(ABC):
    """
    Class that stores simulation parameters and that should always be passed
    to the corresponding simulation. Every Simulation class should also have
    a SimulationParameters class associated with it.

    Examples of simulation parameters:
    - time step for an time-based iterative simulation
    - initial elevation, in case of a rocket launch
    - igniter pressure, in case of an internal ballistic simulation
    """

    pass


class Simulation(ABC):
    """
    The Simulation class stores simulation parameters, arguments and runs the
    main loop of an iterative simulation.

    NOTE: Instances of this class shall not store any simulation state.
    Storing and analyzing simulation data should be done only by the
    Operation class.
    """

    def __init__(self, params: SimulationParameters) -> None:
        """
        :param SimulationParameters params: Object containing every parameter
            needed for a certain simulation to execute. Example:
            A Rocket launch needs to know the initial elevation of the launch
            base in order to determine the air density.
        :returns: None
        :rtype: None
        """
        self.params = params

    @abstractmethod
    def run(self) -> list[Operation]:
        """
        Runs the simulation. In most cases, contains a loop that iterates over
        time or distance.

        :returns: A list of instances of the Operation class.
        :rtype: list[Operation]
        """
        pass

    @abstractmethod
    def print_results(self, *args, **kwargs):
        """
        Prints the results of the simulation, by calling the print_results
        method inside the Operation class instances of the simulation.
        """
        pass
