import machwave.montecarlo as montecarlo
import machwave.simulation as simulation


class _Leaf:
    def __init__(self) -> None:
        self.value = montecarlo.MonteCarloParameter(1.0, spread=0.5)


class _Container:
    def __init__(self) -> None:
        self.items = [_Leaf() for _ in range(3)]
        self.keyed = {"a": _Leaf(), "b": _Leaf()}
        self.raw_list = [montecarlo.MonteCarloParameter(2.0, spread=0.5)]
        self.raw_dict = {"c": montecarlo.MonteCarloParameter(3.0, spread=0.5)}


def _generate(parameter: object) -> object:
    mc = montecarlo.MonteCarloSimulation(
        [parameter], 1, simulation.InternalBallisticsSimulation
    )
    return mc.generate_scenario()[0]


def test_generate_scenario_randomizes_every_list_item() -> None:
    scenario = _generate(_Container())

    for leaf in scenario.items:
        assert not isinstance(leaf.value, montecarlo.MonteCarloParameter)
    assert not isinstance(scenario.raw_list[0], montecarlo.MonteCarloParameter)


def test_generate_scenario_randomizes_dictionary_values() -> None:
    scenario = _generate(_Container())

    for leaf in scenario.keyed.values():
        assert not isinstance(leaf.value, montecarlo.MonteCarloParameter)
    assert not isinstance(scenario.raw_dict["c"], montecarlo.MonteCarloParameter)


def test_generate_scenario_walks_dictionary_cycles_once() -> None:
    container = _Container()
    container.links = {"left": container, "right": container}
    mc = montecarlo.MonteCarloSimulation(
        [container], 1, simulation.InternalBallisticsSimulation
    )

    scenario = mc.generate_scenario()[0]

    assert not isinstance(scenario.items[0].value, montecarlo.MonteCarloParameter)
    assert len(mc._object_store) < 100
