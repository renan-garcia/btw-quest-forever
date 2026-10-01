LEVELING_CONTINENTS = frozenset({"eastern-kingdoms", "kalimdor"})
CAPITALS = frozenset({
    "stormwind-city",
    "ironforge",
    "undercity",
    "darnassus",
    "orgrimmar",
    "thunder-bluff",
})


def is_leveling_zone(zone):
    if zone.get("new_region"):
        return True
    return zone.get("continent") in LEVELING_CONTINENTS and zone.get("slug") not in CAPITALS


def retire_off_grid(state):
    from lib.class_place import place_class_quests

    for zone in list(state["zones"].values()):
        if is_leveling_zone(zone):
            continue
        lua_file = (zone.get("lua_file") or "").replace("\\", "/")
        if not zone.get("category_id") and not lua_file.startswith("Zones/"):
            continue
        place_class_quests(state, zone)
