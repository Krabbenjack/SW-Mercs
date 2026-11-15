# Starship and weapon catalogs

The Starship Editor handles class definitions, not individual vessels. There are initially 75 starships, 11 stations and 10 cargo containers. No statistics or faction assignments have been invented.

## Files

- `data/ships/starship_master_enum.json`: authoritative ID/name/category index, including stations and containers.
- `data/ships/<category>/<id>.json`: each ship class.
- `data/stations/<category>/<id>.json`: each station class.
- `data/containers/<category>/<id>.json`: each cargo container class.
- `data/components/weapons/<id>.json`: weapon definitions, with a separate ID namespace.

The generator `python tools/generate_starship_records.py` creates missing records from the enum without overwriting existing files. The same behavior runs when the editor opens.

## Schema

Each record has `schema_version: 1`, integer `id`, `name`, `object_type` and `category`. The remaining keys are grouped into the form tabs: general, technical, crew, combat, cargo, hangar, economy and maintenance. Station and container records have specialized sections; station propulsion/fuel and container combat/crew fields are omitted. Weapons have one `weapon` section. Field names and types are defined in `app/editors/starships/schema.py`.

Blank fields use JSON null. Explicit zero, false and empty lists are not unknown. A checked "Known / specified" list can be empty. No hyperdrive is expressed as class 0, not null.

The General tab offers optional field groups. Small craft (starfighters, gunships and shuttles) default to reduced external cargo controls; fighters also hide expanded crew and troop fields. Passenger capacity remains available for every ship. Hangar and repair fields can be enabled on any ship or station. Existing populated groups are visible by default, and explicit per-record display overrides are saved in the optional `field_visibility` map. These booleans only control the editor display: hidden statistics are preserved, and no capabilities are assumed from the category.

Weapons are referenced by ID with quantity, direction (Front, Rear, Port, Starboard, Turret) and optional ammunition capacity.

In the Combat tab, **Equipment · Open weapon catalog** opens a searchable popup. Drag weapons from the catalog into the ship equipment table (or double-click / use Add selected weapon). Each mount has its own count, firing direction and optional ammo capacity. Apply loadout updates the unsaved ship form; Cancel leaves the form unchanged. Save persists the record.

For example, after weapon 1 has been created:

```json
{
  "id": 1001,
  "combat": {
    "weapons": [
      {"weapon_id": 1, "quantity": 4, "direction": "Front", "ammunition_capacity": null}
    ]
  }
}
```

Goods and facilities reference the existing catalog IDs. Fuel capacity/consumption uses goods units, cargo uses CU. The cargo tab calculates the nominal total from internal and external capacity when both are known. If slots and the capacities of all compatible container classes are supplied, it also displays the possible fitted external cargo range (assuming all slots filled). Actual vessel loading is a future fleet feature.

## Read/write/import/export

- Existing IDs and category assignments remain stable. New records use an available ID in the chosen category block; renaming updates the enum together with the record.
- Save writes only the edited record (and the index if needed). Files use UTF-8, indented JSON and atomic replacement; batch writes restore prior files if a write fails.
- Import one or more JSON files; each can contain a single record, an array, or an object with a `records` array. Existing IDs can be updated with partial records, as in the example above. Missing fields keep their prior values; explicit null clears a value. New records must specify their identity and category.
- Ship/station/container and weapon imports are separate. Weapon definitions must exist before a ship can reference them. Invalid IDs, categories, fields, directions and references are rejected before writing. Updating existing IDs requires confirmation.
- Export current, filtered or all records. Export files must be outside the data directory, protecting catalog files from accidental overwrites.
- Save/discard/cancel is offered when switching records or databases, importing/exporting or closing with unsaved changes.

The Fleet Manager, balancing/weapon data population, detailed hangar and 3D hardpoint mechanics remain future work.
