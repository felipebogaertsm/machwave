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

def test_monte_carlo_simulation_reproducible_with_seeded_rng() -> None:
    import numpy as np

    param1 = montecarlo.MonteCarloParameter(100.0, spread=10.0, distribution="normal")
    param2 = montecarlo.MonteCarloParameter(50.0, spread=5.0, distribution="uniform")

    sim1 = montecarlo.MonteCarloSimulation(
        [param1, param2, _Container()], 3, simulation.InternalBallisticsSimulation, rng=np.random.default_rng(42)
    )
    scenarios1 = [sim1.generate_scenario() for _ in range(3)]

    sim2 = montecarlo.MonteCarloSimulation(
        [param1, param2, _Container()], 3, simulation.InternalBallisticsSimulation, rng=np.random.default_rng(42)
    )
    scenarios2 = [sim2.generate_scenario() for _ in range(3)]

    for sc1, sc2 in zip(scenarios1, scenarios2):
        assert sc1[0] == sc2[0]
        assert sc1[1] == sc2[1]
        for item1, item2 in zip(sc1[2].items, sc2[2].items):
            assert item1.value == item2.value
