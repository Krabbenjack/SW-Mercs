"""Catalog paths, round trips, validation and transactional write protection."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.shared.paths import DATA_DIR
from app.editors.starships.schema import blank_record
from app.editors.starships.store import CatalogStore, CatalogError, atomic_write, json_bytes


def temporary_catalog(root):
    data = Path(root) / "data"
    for relative in ("ships/starship_master_enum.json", "goods/goods.json",
                     "facilities/facility_flags.json"):
        dest = data / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(DATA_DIR / relative, dest)
    return CatalogStore(data)


class CatalogTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.store = temporary_catalog(self.root)

    def test_all_master_records(self):
        self.assertEqual(len(self.store.entries), 96)
        for record_id, identity in self.store.entries.items():
            record = self.store.read(record_id)
            self.assertEqual(record, blank_record(*identity[:2], record_id, identity[2]))
        self.assertEqual(self.store.seed_missing(), 0)
        self.assertTrue((self.store.data_dir / "ships/starfighters/1001.json").is_file())
        self.assertTrue((self.store.data_dir / "stations/defense_platforms/10001.json").is_file())
        self.assertTrue((self.store.data_dir / "containers/generic/11001.json").is_file())

    def test_partial_import_preserves_unknown_and_zero(self):
        self.store.save([{"id": 1001, "technical": {"length_m": 12.5, "hyperdrive_class": 0},
                          "general": {"factions": []}}])
        path = self.root / "partial.json"
        path.write_text(json.dumps({"id": 1001, "technical": {"sublight_mglt": 100}}))
        records = self.store.import_files([path])
        self.assertEqual(self.store.read(1001)["technical"]["sublight_mglt"], None)
        self.store.save(records)
        record = self.store.read(1001)
        self.assertEqual(record["technical"]["length_m"], 12.5)
        self.assertEqual(record["technical"]["hyperdrive_class"], 0)
        self.assertIsNone(record["technical"]["backup_hyperdrive_class"])
        self.assertEqual(record["general"]["factions"], [])
        self.assertEqual(record["technical"]["sublight_mglt"], 100)
        self.store.seed_missing()
        self.assertEqual(self.store.read(1001), record)

    def test_new_record_and_rename_are_indexed(self):
        record_id = self.store.allocate("starships", "starfighters")
        self.assertNotIn(record_id, self.store.entries)
        new = blank_record("starships", "starfighters", record_id, "Example")
        self.store.save([new])
        self.store.save([{"id": record_id, "name": "Example II"}])
        reopened = CatalogStore(self.store.data_dir)
        self.assertEqual(reopened.read(record_id)["name"], "Example II")
        self.assertEqual(reopened.entries[record_id][2], "Example II")

    def test_silhouette_roundtrip_and_validation(self):
        self.assertIsNone(self.store.read(1001)["technical"]["silhouette"])
        for record_id, silhouette in ((1001, 3), (10001, 12), (9007, 8), (3001, 0)):
            self.store.save([{"id": record_id, "technical": {"silhouette": silhouette}}])
            self.assertEqual(self.store.read(record_id)["technical"]["silhouette"], silhouette)
        for invalid in (-1, 3.0, 1.5, True, "3"):
            with self.assertRaises(CatalogError):
                self.store.save([{"id": 1001, "technical": {"silhouette": invalid}}])
        path = self.root / "silhouette.json"
        self.store.export(path, [1001, 10001])
        records = self.store.import_files([path])
        self.assertEqual([r["technical"]["silhouette"] for r in records], [3, 12])
        self.store.save([{"id": 1001, "technical": {"length_m": 12.5}}])
        self.assertEqual(self.store.read(1001)["technical"]["silhouette"], 3)
        self.store.save([{"id": 1001, "technical": {"silhouette": None}}])
        self.assertIsNone(self.store.read(1001)["technical"]["silhouette"])
        self.assertNotIn("technical", self.store.read(11001))

    def test_weapon_and_references(self):
        weapon = blank_record("weapons", "weapons", 1, "Medium laser")
        weapon["weapon"]["damage"] = 10
        weapon["weapon"]["size_class"] = 2
        self.store.save([weapon], weapons=True)
        loadout = [{"weapon_id": 1, "quantity": 4, "direction": "Front", "ammunition_capacity": None}]
        self.store.save([{"id": 1001, "combat": {"weapons": loadout},
                          "cargo": {"compatible_containers": [11001], "fuel_type": "coaxium_fuel"},
                          "economy": {"construction_materials": [{"goods_id": "alloys", "quantity": 2}]}}])
        self.assertEqual(self.store.read(1001)["combat"]["weapons"], loadout)
        self.assertEqual(self.store.read(1, True)["weapon"]["damage"], 10)
        self.assertEqual(self.store.resolve_weapon_loadout(1001)[0]["component"]["weapon"]["damage"], 10)
        self.store.save([{"id": 1, "weapon": {"damage": 20}}], weapons=True)
        self.assertEqual(self.store.resolve_weapon_loadout(1001)[0]["component"]["weapon"]["damage"], 20)
        for change in ({"weapon_id": 999}, {"direction": "Left"}, {"quantity": 0}):
            invalid = dict(loadout[0], **change)
            with self.assertRaises(CatalogError):
                self.store.save([{"id": 1001, "combat": {"weapons": [invalid]}}])
        with self.assertRaises(CatalogError):
            self.store.save([{"id": 1001, "cargo": {"compatible_containers": [1002]}}])

    def test_invalid_batch_cannot_write(self):
        before = self.store.read(1001)
        for invalid in ({"id": 1002, "technical": {"length_m": -1}},
                        {"id": 1002, "technical": {"length_m": float("nan")}},
                        {"id": 1002, "category": "capital_ships"},
                        {"id": 1002, "unexpected": "value"},
                        {"id": 1002, "cargo": {"fuel_type": "not_a_good"}}):
            with self.assertRaises(CatalogError):
                self.store.save([{"id": 1001, "name": "Should not change"}, invalid])
            self.assertEqual(self.store.read(1001), before)
        with self.assertRaises(CatalogError):
            self.store.save([{"id": 1001}, {"id": 1001}])

    def test_weapon_size_guards(self):
        from app.editors.starships.schema import effective_weapon_limit
        for ship_id, limit in ((1001, 2), (2001, 1), (5001, 3), (7001, 4), (9007, 5), (9012, 6)):
            self.assertEqual(effective_weapon_limit(self.store.read(ship_id)), limit)
        weapons = [blank_record("weapons", "weapons", i, f"Weapon {i}") for i in (1, 2, 3)]
        weapons[0]["weapon"]["size_class"] = 2
        weapons[1]["weapon"]["size_class"] = 5
        self.store.save(weapons, weapons=True)
        mount = {"weapon_id": 1, "quantity": 4, "direction": "Front", "ammunition_capacity": None}
        self.store.save([{"id": 1001, "combat": {"weapons": [mount]}}])
        for value in (0, 7, True, 2.0, "2"):
            with self.assertRaises(CatalogError):
                self.store.save([{"id": 1, "weapon": {"size_class": value}}], weapons=True)
            with self.assertRaises(CatalogError):
                self.store.save([{"id": 1001, "combat": {"max_weapon_size_class": value}}])
        for weapon_id in (2, 3):
            path = self.root / "invalid-loadout.json"
            path.write_bytes(json_bytes({"id": 1001, "combat": {"weapons": [dict(mount, weapon_id=weapon_id)]}}))
            with self.assertRaises(CatalogError):
                self.store.import_files([path])
            self.assertEqual(self.store.read(1001)["combat"]["weapons"], [mount])
        with self.assertRaises(CatalogError):
            self.store.save([{"id": 1001, "combat": {"max_weapon_size_class": 1}}])
        for size in (None, 5):
            with self.assertRaises(CatalogError):
                self.store.save([{"id": 1, "weapon": {"size_class": size}}], weapons=True)
        self.store.save([{"id": 9007, "combat": {"weapons": [mount, dict(mount, weapon_id=2)]}}])
        self.store.save([{"id": 1001, "combat": {"max_weapon_size_class": 5,
                                               "weapons": [dict(mount, weapon_id=2)]}}])
        self.assertEqual(effective_weapon_limit(self.store.read(1001)), 5)
        with self.assertRaises(CatalogError):
            self.store.save([{"id": 1001, "combat": {"max_weapon_size_class": None}}])

    def test_legacy_unclassified_mounts_preserved(self):
        weapon = blank_record("weapons", "weapons", 1, "Legacy")
        weapon["weapon"].pop("size_class")
        atomic_write(self.store.path("weapons", "weapons", 1), json_bytes(weapon))
        record = self.store.read(1001)
        record["combat"].pop("max_weapon_size_class")
        mount = {"weapon_id": 1, "quantity": 1, "direction": "Front", "ammunition_capacity": None}
        record["combat"]["weapons"] = [mount]
        atomic_write(self.store.path("starships", "starfighters", 1001), json_bytes(record))
        self.store.save([{"id": 1001, "general": {"manufacturer": "Test"}}])
        with self.assertRaises(CatalogError):
            self.store.save([{"id": 1001, "combat": {"weapons": [mount, mount]}}])
        self.store.save([{"id": 1, "weapon": {"size_class": 2}}], weapons=True)
        self.assertEqual(self.store.read(1001)["combat"]["weapons"], [mount])

    def test_export_and_import_batch(self):
        path = self.root / "export.json"
        self.store.export(path, [1001, 11001])
        self.assertEqual([x["id"] for x in self.store.import_files([path])], [1001, 11001])
        self.store.export(path, [1001])
        self.assertEqual(json.loads(path.read_text())["id"], 1001)
        with self.assertRaises(CatalogError):
            self.store.export(self.store.enum_path, [1001])

    def test_visibility_override_does_not_remove_values(self):
        self.store.save([{"id": 1001, "field_visibility": {"hangar": False},
                          "hangar": {"starfighter_capacity": 2}}])
        record = self.store.read(1001)
        self.assertEqual(record["hangar"]["starfighter_capacity"], 2)
        self.assertFalse(record["field_visibility"]["hangar"])
        self.store.save([{"id": 1001, "field_visibility": {"armed": True}}])
        self.assertEqual(self.store.read(1001)["field_visibility"], {"hangar": False, "armed": True})
        with self.assertRaises(CatalogError):
            self.store.save([{"id": 1001, "field_visibility": {"unknown": True}}])

    def test_rollback_on_failed_write(self):
        original = self.store.read(1001)
        writes = []
        def fail_second(path, payload):
            writes.append(path)
            if len(writes) == 2:
                raise OSError("Simulated write failure")
            atomic_write(path, payload)
        with patch("app.editors.starships.store.atomic_write", side_effect=fail_second):
            with self.assertRaises(OSError):
                self.store.save([{"id": 1001, "name": "changed"}, {"id": 1002, "name": "changed"}])
        self.assertEqual(self.store.read(1001), original)
        self.assertEqual(CatalogStore(self.store.data_dir).read(1001), original)


if __name__ == "__main__":
    unittest.main()
