"""Regression coverage for spatial system map data and facility placement."""
import json
from pathlib import Path

from app.editors.starmap.system_map import distance_au, environment_at, allowed_placements, grid_cell
from app.shared.paths import DATA_DIR


def test_distance_uses_physical_scale():
    assert distance_au((0, 0), (3, 4), 0.1) == 0.5
    assert distance_au((0, 0), (3, 4), 1) == 5


def test_sparse_environment_defaults_to_deep_space():
    assert environment_at({"objects": []}, 500, 500) == "deep_space"


def test_planetary_surface_facility_does_not_become_orbital():
    data = {"objects": [
        {"kind": "facility", "placement": "surface", "x": 4, "y": 2,
         "influence_cells": 0},
    ]}
    assert environment_at(data, 4, 2) == "deep_space"


def test_planet_orbit_environment():
    data = {"objects": [
        {"kind": "planet", "x": 3, "y": 4, "influence_cells": 1},
    ]}
    assert environment_at(data, 3, 4) == "orbital"
    assert environment_at(data, 10, 10) == "deep_space"


def test_all_facilities_have_placement_policy():
    flags = json.loads((DATA_DIR / "facilities" / "facility_flags.json").read_text(encoding="utf-8"))
    policy = json.loads((DATA_DIR / "facilities" / "facility_placements.json").read_text(encoding="utf-8"))
    expected = {name for ids in flags["categories"].values() for name in ids}
    assert expected == set(policy["placements"])
    for facility_id in expected:
        modes = allowed_placements(facility_id)
        assert modes
        assert set(modes) <= {"surface", "orbit", "deep_space"}


def test_grid_cell_ids_and_subcell_offsets():
    assert grid_cell(0.25, 0.75, 0.1, 5.0) == ("5151", 0.25, 0.75)
    assert grid_cell(-0.75, -0.25, 0.1, 5.0) == ("5050", 0.25, 0.75)
    assert grid_cell(0.25, 0.75, 0.2, 5.0)[0] == "2626"


def test_grid_cell_border_coordinate_width():
    cell_id, _, _ = grid_cell(0, 0, 0.00001, 5.0)
    assert cell_id == "500001500001"
