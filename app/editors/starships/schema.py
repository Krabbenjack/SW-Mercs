"""Shared field definitions for the editor, generator and JSON validation."""
from dataclasses import dataclass

VERSION = 1
DIRECTIONS = ("Front", "Rear", "Port", "Starboard", "Turret")
# FFG Age of Rebellion, Core Rulebook p. 236: relative size and mass.
# Labels are UI shorthand, not mandatory hull types or length thresholds.
MIN_SHIP_SILHOUETTE = 3
SILHOUETTE_CLASSES = {
    0: ("Tiny", "Small objects, astromech droids"),
    1: ("Personal", "Adult humanoids"),
    2: ("Small Vehicle", "Speeder bikes, small vehicles"),
    3: ("Starfighter", "X-Wing, TIE Fighter, Y-Wing"),
    4: ("Transport", "Light freighters, shuttles"),
    5: ("Corvette / light frigate", "Corvettes, Lancer-class frigate"),
    6: ("Frigate", "Nebulon-B frigate"),
    7: ("Heavy Cruiser", "Dreadnought-class, Interdictor"),
    8: ("Destroyer", "Imperial I-class Star Destroyer"),
    9: ("Battlecruiser", "Praetor II-class battlecruiser"),
    10: ("Massive", "Largest ships and stations"),
}
WEAPON_SIZE_CLASSES = {
    1: ("Light", "Light laser / ion cannon", "Light fighters"),
    2: ("Medium", "Medium laser cannon / proton torpedo launcher", "X-Wing, Y-Wing"),
    3: ("Heavy", "Heavy laser cannon / heavy missile launcher", "Gunships, armed freighters"),
    4: ("Capital Light", "Light turbolaser / medium naval gun", "Corvettes, frigates"),
    5: ("Capital Heavy", "Heavy turbolaser battery / heavy ion cannon", "Cruisers, Star Destroyers"),
    6: ("Super Heavy", "Super-heavy naval gun", "Super Star Destroyers, fortress stations"),
}


def size_label(size):
    return f"{size} · {WEAPON_SIZE_CLASSES[size][0]}" if size in WEAPON_SIZE_CLASSES else "Unclassified"


def default_weapon_limit(record):
    """Provisional game-design defaults, overridable for each hull."""
    exceptions = {2001: 1, 9012: 6}
    return exceptions.get(record["id"], {
        "starfighters": 2, "imperial_starfighters": 2, "gunships": 3, "shuttles": 2,
        "freighters_light_medium": 3, "freighters_heavy_logistics": 3,
        "corvettes_patrol": 4, "frigates_cruisers": 4, "capital_ships": 5,
        "defense_platforms": 5, "industrial_research": 4,
    }.get(record["category"], 2))


def effective_weapon_limit(record):
    value = record.get("combat", {}).get("max_weapon_size_class")
    return default_weapon_limit(record) if value is None else value
OBJECT_FOLDERS = {"starships": "ships", "stations": "stations", "cargo_containers": "containers"}


@dataclass(frozen=True)
class Field:
    key: str
    label: str
    kind: str = "text"
    unit: str = ""


F = Field
GENERAL = (
    F("manufacturer", "Manufacturer"), F("role", "Role"),
    F("factions", "Factions", "strings"), F("legality", "Legality"),
    F("description", "Description", "long"), F("image", "Image path"),
)
TECHNICAL = (
    F("length_m", "Length", "number", "m"), F("silhouette", "Silhouette", "silhouette"),
    F("sublight_mglt", "Sublight speed", "number", "MGLT"),
    F("atmospheric_speed_kmh", "Atmospheric speed", "number", "km/h"),
    F("acceleration", "Acceleration", "number", "game value"),
    F("maneuverability", "Maneuverability", "number", "game value"),
    F("hyperdrive_class", "Hyperdrive class", "number", "multiplier (0 = none)"),
    F("backup_hyperdrive_class", "Backup hyperdrive class", "number", "multiplier (0 = none)"),
    F("atmospheric_capability", "Atmospheric capability", "bool"),
    F("landing_capability", "Landing capability", "bool"),
    F("sensor_range_km", "Sensor range", "number", "km"),
    F("communication_system", "Communication system"),
    F("tractor_beams", "Tractor beams", "int"),
)
CREW = tuple(F(key, label, "int") for key, label in (
    ("minimum_crew", "Minimum crew"), ("standard_crew", "Standard crew"),
    ("pilots", "Pilots"), ("officers", "Officers"), ("gunners", "Gunners"),
    ("engineers", "Engineers"), ("support_personnel", "Support personnel"),
    ("passenger_capacity", "Passenger capacity"), ("troop_capacity", "Troop capacity"),
    ("consumables_days", "Consumables (days)"),
))
COMBAT = (
    F("hull", "Hull strength", "number"), F("armor", "Armor", "number"),
    F("shields", "Shield strength", "number"), F("shield_recharge_rate", "Shield recharge rate", "number"),
    F("max_weapon_size_class", "Maximum weapon size", "size_limit"),
    F("weapons", "Weapon systems", "weapons"), F("countermeasures", "Countermeasures"),
    F("electronic_warfare", "Electronic warfare"),
)
CARGO = (
    F("internal_cargo_cu", "Internal cargo capacity", "number", "CU"),
    F("external_cargo_cu", "External cargo capacity", "number", "CU"),
    F("container_slots", "Container slots", "int"),
    F("compatible_containers", "Compatible containers", "containers"),
    F("loading_rate_cu_h", "Loading rate", "number", "CU/h"),
    F("fuel_capacity", "Fuel capacity", "number", "goods units"),
    F("fuel_type", "Fuel type", "goods"),
    F("fuel_consumption_sublight", "Sublight fuel consumption", "number", "units/h"),
    F("fuel_consumption_hyperspace", "Hyperspace fuel consumption", "number", "units/HSU"),
    F("fuel_consumption_idle", "Idle fuel consumption", "number", "units/h"),
)
HANGAR = (
    F("starfighter_capacity", "Starfighter capacity", "int"),
    F("shuttle_capacity", "Shuttle capacity", "int"),
    F("hangar_capacity", "Hangar capacity", "number", "game value"),
    F("repair_capability", "Repair capability", "bool"),
)
ECONOMY = (
    F("purchase_price", "Purchase price", "number", "credits"),
    F("construction_cost", "Construction cost", "number", "credits"),
    F("construction_days", "Construction time", "number", "days"),
    F("required_facility", "Required facility", "facility"),
    F("construction_materials", "Construction materials", "materials"),
    F("technology_requirements", "Technology requirements", "strings"),
    F("market_availability", "Market availability"),
)
MAINTENANCE = (
    F("maintenance_interval_days", "Maintenance interval", "number", "days"),
    F("maintenance_duration_hours", "Maintenance duration", "number", "hours"),
    F("maintenance_cost", "Maintenance cost", "number", "credits"),
    F("maintenance_materials", "Maintenance materials", "materials"),
    F("maintenance_personnel", "Maintenance personnel", "int"),
    F("required_maintenance_facility", "Required maintenance facility", "facility"),
    F("operating_costs", "Operating costs", "number", "credits/day"),
    F("reliability", "Reliability", "number", "game value"),
    F("service_life_years", "Service life", "number", "years"),
)
STATION = (
    F("energy_production", "Energy production", "number", "game value"),
    F("storage_capacity_cu", "Storage capacity", "number", "CU"),
    F("docking_berths", "Docking berths", "int"),
    F("population_capacity", "Personnel / population capacity", "int"),
    F("production_capacity", "Production capacity", "number", "game value"),
    F("repair_capacity", "Repair capacity", "number", "game value"),
    F("special_function", "Special function"),
)
CONTAINER = (
    F("cargo_capacity_cu", "Cargo capacity", "number", "CU"),
    F("maximum_weight_t", "Maximum weight", "number", "t"),
    F("empty_weight_t", "Empty weight", "number", "t"),
    F("length_m", "Length", "number", "m"), F("width_m", "Width", "number", "m"),
    F("height_m", "Height", "number", "m"),
    F("allowed_goods", "Allowed goods", "goods_list"),
    F("refrigeration", "Refrigeration", "bool"), F("pressurization", "Pressurization", "bool"),
    F("hazardous_goods", "Hazardous goods", "bool"),
)
WEAPON = (
    F("weapon_type", "Weapon type"), F("size_class", "Weapon size class", "size_class"),
    F("damage", "Damage", "number", "game value"),
    F("range_km", "Range", "number", "km"), F("rate_of_fire", "Rate of fire", "number", "shots/s"),
    F("projectile_speed_km_s", "Projectile speed", "number", "km/s"),
    F("ammunition_type", "Ammunition type"), F("description", "Description", "long"),
)

SHIP_SECTIONS = {
    "general": ("General", GENERAL), "technical": ("Technical", TECHNICAL),
    "crew": ("Crew", CREW), "combat": ("Combat", COMBAT), "cargo": ("Cargo", CARGO),
    "hangar": ("Hangar", HANGAR), "economy": ("Economy", ECONOMY),
    "maintenance": ("Maintenance", MAINTENANCE),
}


def sections_for(object_type):
    if object_type == "weapons":
        return {"weapon": ("Weapon", WEAPON)}
    if object_type == "cargo_containers":
        return {"general": SHIP_SECTIONS["general"], "container": ("Container", CONTAINER),
                "economy": SHIP_SECTIONS["economy"], "maintenance": SHIP_SECTIONS["maintenance"]}
    if object_type == "stations":
        sections = dict(SHIP_SECTIONS)
        # Stations have no assumed propulsion/landing or fuel requirements.
        sections["technical"] = ("Technical", tuple(f for f in TECHNICAL if f.key in
                                  {"length_m", "silhouette", "sensor_range_km", "communication_system", "tractor_beams"}))
        sections["cargo"] = ("Cargo", CARGO[:5])
        sections["station"] = ("Station", STATION)
        return sections
    return SHIP_SECTIONS


def blank_record(object_type, category, record_id, name):
    record = {"schema_version": VERSION, "id": record_id, "name": name,
              "object_type": object_type, "category": category}
    for section, (_, fields) in sections_for(object_type).items():
        record[section] = {field.key: None for field in fields}
    return record


def visibility_groups(record):
    """Presentation defaults only; never infer or delete ship statistics."""
    kind, category = record["object_type"], record["category"]
    if kind not in ("starships", "stations"):
        return {}
    fighter = category in ("starfighters", "imperial_starfighters")
    small = fighter or category in ("gunships", "shuttles")
    groups = {
        "expanded_crew": ("Expanded crew", not fighter,
                          (("crew", "officers"), ("crew", "engineers"), ("crew", "support_personnel"))),
        "troops": ("Troop transport", not fighter, (("crew", "troop_capacity"),)),
        "external_cargo": ("External cargo / containers", not small,
                           tuple(("cargo", key) for key in
                                 ("external_cargo_cu", "container_slots", "compatible_containers", "loading_rate_cu_h"))),
        "hangar": ("Hangar", False, tuple(("hangar", key) for key in
                                         ("starfighter_capacity", "shuttle_capacity", "hangar_capacity"))),
        "repair": ("Repair facilities", False, (("hangar", "repair_capability"),)),
        "armed": ("Weapons", kind == "starships" or category == "defense_platforms",
                  (("combat", "max_weapon_size_class"), ("combat", "weapons"))),
        "shielded": ("Shields", True, (("combat", "shields"), ("combat", "shield_recharge_rate"))),
        "tractor_beams": ("Tractor beams", not small, (("technical", "tractor_beams"),)),
    }
    if kind == "starships":
        groups["hyperdrive"] = ("Hyperdrive", True, (("technical", "hyperdrive_class"),
                                                   ("technical", "backup_hyperdrive_class")))
    return groups


def group_is_visible(record, group):
    _, default, fields = visibility_groups(record)[group]
    override = record.get("field_visibility", {}).get(group)
    if override is not None:
        return override
    return default or any(record.get(section, {}).get(key) is not None for section, key in fields)
