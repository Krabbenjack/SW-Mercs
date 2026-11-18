"""Regression tests for the Stats sidebar navigation search."""
from types import SimpleNamespace

from app.editors.starmap.gui import find_system_body_matches


class Item:
    def __init__(self, system):
        self.system = system

    def get_system_data(self):
        return self.system


def test_search_finds_system_planet_and_moon():
    moon = SimpleNamespace(name="Luna")
    earth = SimpleNamespace(name="Earth", moons=[moon])
    sol = SimpleNamespace(name="Sol", planets=[earth])
    other = SimpleNamespace(name="Alderaan", planets=[])
    items = {"sol-id": Item(sol), "other-id": Item(other)}
    assert find_system_body_matches(items, "SOL") == [("sol-id", "System", "Sol", "Sol")]
    assert find_system_body_matches(items, "earth") == [("sol-id", "Planet", "Earth", "Sol")]
    assert find_system_body_matches(items, "lUnA") == [("sol-id", "Moon", "Luna", "Sol")]
    assert find_system_body_matches(items, "   ") == []
    assert find_system_body_matches(items, "unknown") == []
