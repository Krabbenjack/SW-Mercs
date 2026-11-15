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

Ship and station Technical tabs include `technical.silhouette`, an independent relative size/mass rating from the FFG Star Wars Age of Rebellion Core Rulebook (p. 236). The editor offers 0–10 and custom integers 11 or higher, plus Unknown (null). The help table uses approximate labels and examples; the book does not define fixed lengths or require one silhouette per hull type. For instance, the Lancer frigate is 5 (p. 278), Nebulon-B is 6 and Dreadnought is 7 (p. 279), Imperial I is 8 (p. 282), and Praetor II is 9 (p. 283). This field does not change the maximum weapon size, existing cargo or hangar values. Older JSON files without the field remain valid and are treated as Unknown.

The General tab offers optional field groups. Small craft (starfighters, gunships and shuttles) default to reduced external cargo controls; fighters also hide expanded crew and troop fields. Passenger capacity remains available for every ship. Hangar and repair fields can be enabled on any ship or station. Existing populated groups are visible by default, and explicit per-record display overrides are saved in the optional `field_visibility` map. These booleans only control the editor display: hidden statistics are preserved, and no capabilities are assumed from the category.

Weapons are referenced by ID with quantity, direction (Front, Rear, Port, Starboard, Turret) and optional ammunition capacity.

In the Combat tab, **Equipment · Open weapon catalog** opens a searchable popup. Drag weapons from the catalog into the ship equipment table (or double-click / use Add selected weapon). Each mount has its own count, firing direction and optional ammo capacity. Apply loadout updates the unsaved ship form; Cancel leaves the form unchanged. Save persists the record.

Weapon size is independent of damage and quantity. Set `weapon.size_class` in Component Database and `combat.max_weapon_size_class` in the ship or station Combat tab. Both have a **?** button with the full guide:

| ID | Class | Example | Typical carriers |
|---:|---|---|---|
| 1 | Light | Light laser / ion cannon | Light fighters |
| 2 | Medium | Medium laser cannon / proton torpedo launcher | X-Wing, Y-Wing |
| 3 | Heavy | Heavy laser cannon / heavy missile launcher | Gunships, armed freighters |
| 4 | Capital Light | Light turbolaser | Corvettes, frigates |
| 5 | Capital Heavy | Heavy turbolaser battery | Cruisers, Star Destroyers |
| 6 | Super Heavy | Super-heavy naval gun | Super Star Destroyers, fortress stations |

An omitted or null hull limit uses an automatic game-design default: fighter/shuttle 2 (TIE/LN 1), gunship/freighter 3, corvette/frigate/light cruiser 4, capital ship 5 (Executor 6), defense station 5, industrial station 4. Each hull may override the default. Cargo containers have no weapon limit field. Larger and unclassified weapons remain visible but disabled in the equipment catalog; only compatible sizes can be added by any interaction. Save and import enforce the same limit, including changes to the limit or referenced weapon definition. Old records missing the new keys still load; unchanged legacy unclassified mounts remain readable and saveable, but new mounts require a classified weapon.

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
