from lib.chains import _faction_of, _range, allocate_ids
from lib.leveling import is_leveling_zone
from lib.state_store import FACTION_BY_SIDE
from lib.series import missing_members, series_groups, _subsequence
from lib import wowhead

CLASS_BY_SLUG = {
    "warrior": 1,
    "paladin": 2,
    "hunter": 3,
    "rogue": 4,
    "priest": 5,
    "death-knight": 6,
    "shaman": 7,
    "mage": 8,
    "warlock": 9,
    "monk": 10,
    "druid": 11,
}


def place_class_quests(state, class_zone, selection=None):
    class_key = f"{class_zone['continent']}/{class_zone['slug']}"
    class_zone["constant"] = _constant_name(class_zone["slug"])
    quest_ids = list(class_zone.get("quest_ids") or [])
    saved_ids = _detach(state, class_key, selection)
    class_id = CLASS_BY_SLUG.get(class_zone["slug"])
    old_file = class_zone.pop("lua_file", None)
    class_zone.pop("category_id", None)
    class_zone.pop("ui_map_id", None)
    grouped, leftovers = _series_groups(quest_ids, state["quests"])
    quest_ids = list(dict.fromkeys(quest_ids + [item for series in grouped for item in series]))
    previous = [key for key, zone in state["zones"].items() if any(
        token.startswith(key + "|") for token in saved_ids
    )]

    homes = {}
    unplaced = []
    for series in grouped:
        home = _home(series, state["quests"], state)
        if home is None:
            unplaced.extend(series)
            continue
        homes.setdefault(home, []).append(series)
    loose = {}
    for quest_id in leftovers:
        home = _home([quest_id], state["quests"], state)
        if home is None:
            unplaced.append(quest_id)
            continue
        loose.setdefault(home, []).append(quest_id)

    placed = []
    for zone_key in sorted(set(homes) | set(loose)):
        zone = state["zones"][zone_key]
        _ensure_shell(zone, zone_key)
        for series in homes.get(zone_key, []):
            _append_chain(class_zone, zone, zone_key, series, class_id, saved_ids, state["quests"], other=False)
        for faction, bucket in _by_faction(loose.get(zone_key, []), state["quests"]).items():
            if bucket:
                _append_chain(class_zone, zone, zone_key, bucket, class_id, saved_ids, state["quests"], other=True, faction=faction)
        allocate_ids(state, zone)
        placed.append(zone_key)

    for quest_id in quest_ids:
        if quest_id in unplaced:
            state["quests"].setdefault(str(quest_id), {})["zone"] = class_key
            state["quests"][str(quest_id)]["placement_pending"] = True
            continue
        for zone_key in placed:
            quests_there = {
                item
                for chain in state["zones"][zone_key].get("chains") or []
                if quest_id in chain.get("quests", [])
                for item in chain["quests"]
            }
            if quest_id in quests_there:
                state["quests"][str(quest_id)]["zone"] = zone_key
                state["quests"][str(quest_id)]["chain_zone"] = zone_key
                state["quests"][str(quest_id)].pop("placement_pending", None)
                break

    class_zone["chains"] = []
    class_zone["quest_ids"] = unplaced
    class_zone["placed_into"] = placed
    class_zone["affected_zones"] = sorted(set(previous + placed))
    for key in previous:
        old = state["zones"][key]
        if not old.get("chains") and not old.get("quest_ids") and not old.get("chains_locked"):
            old.pop("category_id", None)
            retired = old.pop("lua_file", None)
            if retired:
                old["remove_lua"] = retired
    if old_file and old_file.replace("\\", "/").startswith("Zones/"):
        class_zone["remove_lua"] = old_file

    if class_zone.get("continent") == "classes" and not class_id:
        print(f"{class_key}: classe desconhecida, as cadeias entram sem restrição de classe.")
    for zone_key in placed:
        count = sum(1 for chain in state["zones"][zone_key].get("chains") or [] if chain.get("from_class") == class_key)
        print(f"{class_key}: {count} cadeias em {zone_key}")
    if unplaced:
        print(f"{class_key}: sem zona de início: {unplaced}")
    return placed


def rehome_foreign(state, zone):
    key = f"{zone['continent']}/{zone['slug']}"
    foreign = []
    kept = []
    grouped, leftovers = series_groups(zone.get("quest_ids") or [], state["quests"])
    for series in grouped + [[item] for item in leftovers]:
        home = _home(series, state["quests"], state)
        if home != key:
            foreign.extend(series)
        else:
            kept.extend(series)
            for quest_id in series:
                state["quests"][str(quest_id)]["chain_zone"] = key
                state["quests"][str(quest_id)].pop("placement_pending", None)
    zone["quest_ids"] = list(dict.fromkeys(kept))
    shadow = {
        "continent": zone.get("continent"),
        "slug": zone.get("slug"),
        "constant": zone.get("constant"),
        "quest_ids": list(dict.fromkeys(foreign)),
    }
    placed = place_class_quests(state, shadow)
    # Dados insuficientes continuam pendentes na zona de origem, sem cadeia parcial.
    zone["quest_ids"].extend(item for item in shadow["quest_ids"] if item not in zone["quest_ids"])
    zone["affected_zones"] = sorted(set(zone.get("affected_zones", []) + shadow["affected_zones"]))
    current = zone.setdefault("placed_into", [])
    for key in placed or []:
        if key not in current:
            current.append(key)
    return placed


def _append_chain(class_zone, zone, zone_key, quest_ids, class_id, saved_ids, quests, other, faction=None):
    if not other and any(chain.get("quests") == list(quest_ids) and chain.get("class_id") == class_id
                         for chain in zone.get("chains") or []):
        return
    prefix = class_zone["constant"]
    taken = {chain["constant"] for chain in zone.get("chains") or []}
    if other:
        suffix = {None: "Neutral", "Alliance": "Alliance", "Horde": "Horde"}[faction]
        constant = f"Class{prefix}Other{suffix}"
        locale_key = f"{prefix}_{zone['constant']}_Other{suffix}"
        name_en = "Other quests" if faction else "Neutral quests"
        name_pt = "Outras missões" if faction else "Missões neutras"
        complete_all = True
    else:
        constant = f"Class{prefix}{quest_ids[0]}"
        if constant in taken:
            constant = f"{constant}To{quest_ids[-1]}"
        locale_key = f"{prefix}_{zone['constant']}_{quest_ids[0]}"
        first = quests[str(quest_ids[0])]
        name_en = first.get("name_en") or constant
        name_pt = first.get("name_pt") or name_en
        faction = _faction_of(quest_ids, quests)
        complete_all = False
    low, high, required = _range(quest_ids, quests)
    chain_id = saved_ids.get(f"{zone_key}|{constant}")
    records = saved_ids.get("__series__", [])
    if chain_id is None:
        match = next((record for record in records
                      if record.get("faction") == faction and record.get("class_id") == class_id
                      and (record["quests"] == list(quest_ids) or
                           (not other and not record.get("complete_all") and _subsequence(record["quests"], quest_ids)))), None)
        if match:
            chain_id = match.get("id")
    records[:] = [record for record in records if record.get("id") != chain_id]
    chain = {
        "constant": constant,
        "locale_key": locale_key,
        "id": chain_id,
        "quests": list(quest_ids),
        "range": [low, high],
        "required_level": required,
        "complete_all": complete_all,
        "faction": faction,
        "class_id": class_id,
        "from_class": f"{class_zone['continent']}/{class_zone['slug']}",
        "name_en": name_en,
        "name_pt": name_pt,
    }
    zone.setdefault("chains", []).append(chain)


def _by_faction(quest_ids, quests):
    buckets = {"Alliance": [], "Horde": [], None: []}
    for quest_id in quest_ids:
        buckets[FACTION_BY_SIDE.get(quests[str(quest_id)].get("side"))].append(quest_id)
    for bucket in buckets.values():
        bucket.sort(key=lambda quest_id: ((quests[str(quest_id)].get("level") or 0), quest_id))
    return buckets


def _series_groups(quest_ids, quests):
    return series_groups(quest_ids, quests)


def _home(quest_ids, quests, state):
    if missing_members(quest_ids, quests):
        return None
    by_area = _zones_by_area(state)
    for quest_id in quest_ids:
        zone_id = (quests.get(str(quest_id)) or {}).get("quest_zone_id")
        if not zone_id:
            continue
        known = by_area.get(zone_id)
        if known:
            return known
        if zone_id > 0 and not _catalog_has_area(state, zone_id):
            return _ensure_new_region(state, zone_id)
    # Capitais/classes podem usar a origem física somente quando ela é inequívoca.
    areas = set()
    for quest_id in quest_ids:
        quest = quests.get(str(quest_id)) or {}
        starts = quest.get("start_areas")
        areas.update(starts if starts is not None else [quest.get("start_area")])
    areas.discard(None)
    return by_area.get(next(iter(areas))) if len(areas) == 1 else None


def _catalog_has_area(state, area_id):
    for zone in state["zones"].values():
        if zone.get("new_region"):
            continue
        if zone.get("area_id") == area_id:
            return True
    return False


def _ensure_new_region(state, area_id):
    key = f"new/{int(area_id)}"
    zone = state["zones"].get(key)
    if zone is None:
        title = _zone_title(area_id)
        zone = {
            "continent": "new",
            "slug": str(int(area_id)),
            "area_id": int(area_id),
            "name_pt": title,
            "name_en": title,
            "new_region": True,
            "status": "pending",
        }
        state["zones"][key] = zone
    zone["new_region"] = True
    zone.pop("ui_map_id", None)
    zone["constant"] = f"Zone{int(area_id)}"
    zone["locale_key"] = f"ZONE_{int(area_id)}"
    _ensure_shell(zone, key)
    return key


def _zone_title(area_id):
    try:
        title = wowhead.zone_title(area_id, locale="pt")
    except Exception as error:
        print(f"Zona {area_id} sem título no Wowhead ({error}).")
        title = None
    return title or f"Zona {area_id}"


def _zones_by_area(state):
    found = {}
    for key, zone in state["zones"].items():
        if not is_leveling_zone(zone):
            continue
        area = zone.get("area_id")
        if not isinstance(area, int) or area <= 0:
            continue
        current = found.get(area)
        if current is None or (zone.get("category_id") and not state["zones"][current].get("category_id")):
            found[area] = key
    return found


def _detach(state, class_key, selection=None):
    saved = {"__series__": []}
    for key, zone in state["zones"].items():
        if "chains" not in zone:
            continue
        kept = []
        for chain in zone.get("chains") or []:
            if chain.get("from_class") == class_key and (selection is None or set(chain.get("quests", [])) & set(selection)):
                saved[f"{key}|{chain.get('constant')}"] = chain.get("id")
                saved["__series__"].append(dict(chain))
                continue
            kept.append(chain)
        zone["chains"] = kept
    return saved


def _ensure_shell(zone, zone_key):
    slug = zone.get("slug") or zone_key.split("/", 1)[1]
    zone.setdefault("constant", _constant_name(slug))
    zone.setdefault("locale_key", _locale_key(zone["constant"]))
    if not zone.get("lua_file"):
        zone["lua_file"] = f"Zones/{zone['constant']}.lua"


def _constant_name(slug):
    parts = [part for part in slug.replace("-", " ").split() if part]
    return "".join(part[:1].upper() + part[1:] for part in parts)


def _locale_key(constant):
    import re
    return re.sub(r"(?<!^)([A-Z])", r"_\1", constant).upper()
