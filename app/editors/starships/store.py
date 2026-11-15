"""File-backed catalog with stable IDs, validation and atomic JSON writes."""
from copy import deepcopy
import json
import math
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from app.shared.paths import DATA_DIR
from .schema import (VERSION, DIRECTIONS, OBJECT_FOLDERS, blank_record, sections_for, visibility_groups,
                     WEAPON_SIZE_CLASSES, effective_weapon_limit, size_label, MIN_SHIP_SILHOUETTE)


class CatalogError(ValueError):
    pass


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise CatalogError(f"Cannot read {path}: {exc}") from exc


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def atomic_write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temp = Path(stream.name)
            stream.write(payload)
        os.replace(temp, path)
    finally:
        if temp is not None and temp.exists():
            temp.unlink()


def write_batch(files):
    """Validate/serialize first; restore original files on a write failure."""
    payloads = {path: json_bytes(value) for path, value in files.items()}
    originals = {path: path.read_bytes() if path.exists() else None for path in files}
    written = []
    try:
        for path, payload in payloads.items():
            atomic_write(path, payload)
            written.append(path)
    except OSError:
        for path in reversed(written):
            if originals[path] is None:
                path.unlink(missing_ok=True)
            else:
                atomic_write(path, originals[path])
        raise


class CatalogStore:
    def __init__(self, data_dir=DATA_DIR, seed=True):
        self.data_dir = Path(data_dir)
        self.enum_path = self.data_dir / "ships" / "starship_master_enum.json"
        self.enum = read_json(self.enum_path)
        self.goods = {item["id"]: item["name"] for item in
                      read_json(self.data_dir / "goods" / "goods.json")["goods"]}
        self.facilities = {item: item.replace("_", " ").title() for category in
                           read_json(self.data_dir / "facilities" / "facility_flags.json")["categories"].values()
                           for item in category}
        self.entries = self._index(self.enum)
        self.weapon_dir = self.data_dir / "components" / "weapons"
        if seed:
            self.seed_missing()

    @staticmethod
    def _index(enum):
        result = {}
        for object_type, categories in enum.items():
            if object_type not in OBJECT_FOLDERS:
                raise CatalogError(f"Unknown object type: {object_type}")
            for category, entries in categories.items():
                if not category.replace("_", "").isalnum():
                    raise CatalogError(f"Invalid category: {category}")
                for key, name in entries.items():
                    record_id = int(key)
                    if record_id <= 0 or record_id in result:
                        raise CatalogError(f"Duplicate or invalid ID: {key}")
                    result[record_id] = (object_type, category, name)
        return result

    def path(self, object_type, category, record_id):
        if object_type == "weapons" and category == "weapons":
            return self.weapon_dir / f"{record_id}.json"
        if object_type not in self.enum or category not in self.enum[object_type]:
            raise CatalogError(f"Unknown category: {object_type}/{category}")
        return self.data_dir / OBJECT_FOLDERS[object_type] / category / f"{record_id}.json"

    def seed_missing(self):
        files = {}
        for record_id, (object_type, category, name) in self.entries.items():
            path = self.path(object_type, category, record_id)
            if not path.exists():
                files[path] = blank_record(object_type, category, record_id, name)
        write_batch(files)
        return len(files)

    def weapon_entries(self):
        entries = {}
        for path in sorted(self.weapon_dir.glob("*.json")):
            if not path.stem.isdecimal() or int(path.stem) <= 0:
                raise CatalogError(f"Invalid weapon filename: {path.name}")
            record = read_json(path)
            record_id = int(path.stem)
            if record.get("id") != record_id or record.get("object_type") != "weapons":
                raise CatalogError(f"Weapon identity does not match {path.name}")
            entries[record_id] = ("weapons", "weapons", record["name"])
        return entries

    def listing(self, weapons=False):
        return self.weapon_entries() if weapons else dict(self.entries)

    def read(self, record_id, weapons=False):
        entries = self.listing(weapons)
        if record_id not in entries:
            raise CatalogError(f"Unknown ID: {record_id}")
        object_type, category, name = entries[record_id]
        record = read_json(self.path(object_type, category, record_id))
        if (record.get("id"), record.get("object_type"), record.get("category"), record.get("name")) != (
                record_id, object_type, category, name):
            raise CatalogError(f"Identity mismatch for {record_id}")
        return self.normalize(record)

    def resolve_weapon_loadout(self, record_id):
        """Return mount data joined to current weapon definitions without duplicating stats on disk."""
        record = self.read(record_id)
        mounts = record.get("combat", {}).get("weapons")
        if mounts is None:
            return None
        return [dict(mount, component=self.read(mount["weapon_id"], weapons=True)) for mount in mounts]

    def allocate(self, object_type, category):
        if object_type == "weapons":
            return max(self.weapon_entries(), default=0) + 1
        ids = [key for key, value in self.entries.items() if value[:2] == (object_type, category)]
        if not ids:
            raise CatalogError("Unknown or empty category")
        block = 1000 if object_type == "starships" else 100
        start = min(ids) // block * block
        for record_id in range(max(ids) + 1, start + block):
            if record_id not in self.entries:
                return record_id
        raise CatalogError("No free ID in this category")

    def references(self, kind):
        if kind in ("goods", "goods_list", "materials"):
            return self.goods
        if kind == "facility":
            return self.facilities
        if kind == "containers":
            return {key: value[2] for key, value in self.entries.items() if value[0] == "cargo_containers"}
        if kind == "weapons":
            return {key: value[2] for key, value in self.weapon_entries().items()}
        return {}

    def weapon_sizes(self):
        return {key: self.read(key, weapons=True)["weapon"]["size_class"]
                for key in self.weapon_entries()}

    def validate_loadout_sizes(self, mounts, limit, previous=None, sizes=None):
        """Preserve unchanged legacy unclassified mounts, but never add new ones."""
        if not mounts:
            return
        sizes = self.weapon_sizes() if sizes is None else sizes
        legacy = list(previous or [])
        for mount in mounts:
            weapon_id = mount["weapon_id"]
            size = sizes.get(weapon_id)
            if size is None:
                if mount in legacy:
                    legacy.remove(mount)
                    continue
                raise CatalogError(f"Weapon {weapon_id} needs a size class before assignment.")
            if size > limit:
                raise CatalogError(f"Weapon {weapon_id} ({size_label(size)}) exceeds the ship limit ({size_label(limit)}).")

    @staticmethod
    def _number(value, integer=False):
        if type(value) is int:
            return value >= 0
        return not integer and type(value) is float and math.isfinite(value) and value >= 0

    def _validate_field(self, field, value):
        if value is None:
            return
        kind = field.kind
        ok = False
        if kind in ("text", "long"):
            ok = isinstance(value, str)
        elif kind in ("number", "int"):
            ok = self._number(value, kind == "int")
        elif kind == "silhouette":
            ok = type(value) is int and value >= MIN_SHIP_SILHOUETTE
        elif kind in ("size_class", "size_limit"):
            ok = type(value) is int and value in WEAPON_SIZE_CLASSES
        elif kind == "bool":
            ok = type(value) is bool
        elif kind in ("goods", "facility"):
            ok = isinstance(value, str) and value in self.references(kind)
        elif kind in ("strings", "containers", "goods_list"):
            refs = self.references(kind)
            value_type = int if kind == "containers" else str
            ok = isinstance(value, list) and all(type(item) is value_type and
                (bool(item.strip()) if kind == "strings" else item in refs) for item in value)
            ok = ok and len(set(value)) == len(value)
        elif kind == "materials":
            ok = isinstance(value, list) and all(
                isinstance(row, dict) and set(row) == {"goods_id", "quantity"} and
                isinstance(row["goods_id"], str) and row["goods_id"] in self.goods and
                self._number(row["quantity"]) for row in value)
        elif kind == "weapons":
            refs = self.references(kind)
            ok = isinstance(value, list) and all(
                isinstance(row, dict) and set(row) == {"weapon_id", "quantity", "direction", "ammunition_capacity"} and
                type(row["weapon_id"]) is int and row["weapon_id"] in refs and
                self._number(row["quantity"], True) and row["quantity"] > 0 and
                row["direction"] in DIRECTIONS and (row["ammunition_capacity"] is None or
                self._number(row["ammunition_capacity"], True)) for row in value)
        if not ok:
            raise CatalogError(f"Invalid value for {field.label}: {value!r}")

    def normalize(self, incoming, base=None):
        """Merge provided fields into base; omitted fields stay unchanged."""
        if not isinstance(incoming, dict):
            raise CatalogError("A record must be a JSON object")
        identity = {key: incoming.get(key, (base or {}).get(key)) for key in
                    ("id", "name", "object_type", "category")}
        record_id, name, object_type, category = (identity[key] for key in
                                                  ("id", "name", "object_type", "category"))
        if type(record_id) is not int or record_id <= 0 or not isinstance(name, str) or not name.strip():
            raise CatalogError("ID must be a positive integer and name must not be empty")
        if not isinstance(object_type, str) or not isinstance(category, str):
            raise CatalogError("Object type and category are required")
        self.path(object_type, category, record_id)
        if incoming.get("schema_version", VERSION) != VERSION:
            raise CatalogError("Unsupported schema version")
        if base and any(identity[key] != base[key] for key in ("id", "object_type", "category")):
            raise CatalogError("Existing IDs cannot change object type/category")
        record = blank_record(object_type, category, record_id, name.strip())
        if base:
            record.update(deepcopy(base))
            record["name"] = name.strip()
        groups = visibility_groups(record)
        if "field_visibility" in incoming:
            overrides = incoming["field_visibility"]
            if (not groups or not isinstance(overrides, dict) or set(overrides) - set(groups)
                    or any(type(value) is not bool for value in overrides.values())):
                raise CatalogError("Invalid field visibility overrides")
            record["field_visibility"] = dict(record.get("field_visibility", {}), **overrides)
        unknown = set(incoming) - set(record)
        if unknown:
            raise CatalogError(f"Unknown fields: {', '.join(sorted(unknown))}")
        for section, (_, fields) in sections_for(object_type).items():
            supplied = incoming.get(section, {})
            if not isinstance(supplied, dict) or set(supplied) - {field.key for field in fields}:
                raise CatalogError(f"Invalid/unknown fields in {section}")
            record[section].update(supplied)
            for field in fields:
                self._validate_field(field, record[section][field.key])
        return record

    def prepare(self, incoming, weapons=False):
        entries = self.listing(weapons)
        result, seen = [], set()
        for value in incoming:
            if not isinstance(value, dict) or type(value.get("id")) is not int:
                raise CatalogError("Each record needs an integer ID")
            record_id = value["id"]
            if record_id in seen:
                raise CatalogError(f"Duplicate imported ID: {record_id}")
            seen.add(record_id)
            base = self.read(record_id, weapons) if record_id in entries else None
            record = self.normalize(value, base)
            if (record["object_type"] == "weapons") != weapons:
                raise CatalogError("Import weapons and ship/station/container records separately")
            if not weapons and record_id not in entries:
                ids = [key for key, item in self.entries.items()
                       if item[:2] == (record["object_type"], record["category"])]
                block = 1000 if record["object_type"] == "starships" else 100
                if not ids or record_id // block != min(ids) // block:
                    raise CatalogError(f"ID {record_id} is outside its category range")
            if not weapons and "combat" in record:
                self.validate_loadout_sizes(record["combat"]["weapons"], effective_weapon_limit(record),
                                            (base or {}).get("combat", {}).get("weapons"))
            result.append(record)
        if weapons:
            self._validate_weapon_size_updates(result)
        return result

    def _validate_weapon_size_updates(self, records):
        # A catalog edit must not silently invalidate equipment on other hulls.
        existing = self.weapon_sizes()
        changed = {record["id"]: record["weapon"]["size_class"] for record in records
                   if record["id"] in existing and record["weapon"]["size_class"] != existing[record["id"]]}
        if not changed:
            return
        for ship_id, (kind, _, name) in self.entries.items():
            if kind == "cargo_containers":
                continue
            ship = self.read(ship_id)
            limit = effective_weapon_limit(ship)
            for mount in ship["combat"]["weapons"] or []:
                if mount["weapon_id"] not in changed:
                    continue
                size = changed[mount["weapon_id"]]
                if size is None or size > limit:
                    raise CatalogError(f"Weapon {mount['weapon_id']} is installed on {name} (limit {size_label(limit)}). "
                                       "Adjust its equipment before changing this weapon size.")

    def save(self, incoming, weapons=False):
        records = self.prepare(incoming, weapons)
        enum = deepcopy(self.enum)
        files = {}
        for record in records:
            object_type, category, record_id = (record[key] for key in ("object_type", "category", "id"))
            files[self.path(object_type, category, record_id)] = record
            if not weapons:
                enum[object_type][category][str(record_id)] = record["name"]
        if enum != self.enum:
            files[self.enum_path] = enum
        write_batch(files)
        self.enum = enum
        self.entries = self._index(enum)
        return records

    def import_files(self, paths, weapons=False):
        values = []
        for path in paths:
            data = read_json(path)
            if isinstance(data, dict) and "records" in data:
                data = data["records"]
                if not isinstance(data, list):
                    raise CatalogError("records must be a JSON array")
            values.extend(data if isinstance(data, list) else [data])
        if not values:
            raise CatalogError("No records in import")
        return self.prepare(values, weapons)

    def export(self, path, record_ids, weapons=False):
        if Path(path).resolve().is_relative_to(self.data_dir.resolve()):
            raise CatalogError("Export outside the data directory to protect the catalog.")
        records = [self.read(record_id, weapons) for record_id in record_ids]
        if not records:
            raise CatalogError("No records to export")
        atomic_write(Path(path), json_bytes(records[0] if len(records) == 1 else {"records": records}))
