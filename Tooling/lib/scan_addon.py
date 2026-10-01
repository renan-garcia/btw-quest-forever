import re

from lib.paths import ADDON

KNOWN_ZONES = {
    "ElwynnForest": {
        "key": "eastern-kingdoms/elwynn-forest",
        "area_id": 12,
        "ui_map_id": 1429,
        "locale_key": "ELWYNN_FOREST",
    },
}


def _blocks(text):
    return re.findall(r"\[(\d+)\] = \{(.*?)\n    \},", text, re.S)


def _lua_string(body, field):
    match = re.search(rf'{field} = "(.*)"', body)
    return match.group(1) if match else None


def _locale_map(path):
    if not path.exists():
        return {}
    return {int(quest_id): name for quest_id, name in re.findall(r'\[(\d+)\] = \{\s*name = "(.*)"', path.read_text(encoding="utf-8"))}


def _chains(text):
    ids = {name: int(chain_id) for name, chain_id in re.findall(r"Chain\.(\w+) = (\d+)", text)}
    chains = []
    pattern = re.compile(
        r'AddChain\(Chain\.(\w+), L\["([^"]+)"\], \{([^}]+)\}, (\d+), (\d+), (\d+), (true|false)(?:, (false|"[^"]+"))?\)'
    )
    for name, locale_key, quests, range_min, range_max, required, complete_all, faction in pattern.findall(text):
        if not faction:
            faction_id = "Alliance"
        elif faction == "false":
            faction_id = None
        else:
            faction_id = faction.strip('"')
        chains.append({
            "constant": name,
            "locale_key": locale_key,
            "id": ids.get(name),
            "quests": [int(part) for part in quests.split(",")],
            "range": [int(range_min), int(range_max)],
            "required_level": int(required),
            "complete_all": complete_all == "true",
            "faction": faction_id,
        })
    return chains


def _npc_blocks(text):
    found = {}
    for npc_id, body in _blocks(text):
        locations = {}
        for map_id, x, y in re.findall(r"\[(\d+)\] = \{\s*\{\s*x = ([\d.]+),\s*y = ([\d.]+),", body):
            locations.setdefault(map_id, []).append({"x": float(x), "y": float(y)})
        found[npc_id] = {
            "name_en": _lua_string(body, "name"),
            "locations": locations,
            "in_addon": True,
        }
    return found


def scan(state):
    quests_text = (ADDON / "Database" / "Quests.lua").read_text(encoding="utf-8")
    names_pt = _locale_map(ADDON / "Database" / "Quests.ptBR.lua")
    npc_pt = _locale_map(ADDON / "Database" / "NPCs.ptBR.lua")
    constants = {
        name: int(category_id)
        for name, category_id in re.findall(r"(\w+) = (\d+)", (ADDON / "Defines.lua").read_text(encoding="utf-8"))
    }

    chain_owner = {}
    for constant, known in KNOWN_ZONES.items():
        lua_file = f"{constant}.lua"
        path = ADDON / lua_file
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        chains = _chains(text)
        quest_ids = []
        for chain in chains:
            for quest_id in chain["quests"]:
                if quest_id not in quest_ids:
                    quest_ids.append(quest_id)
                chain_owner[quest_id] = known["key"]
        zone = state["zones"].get(known["key"], {})
        zone.update({
            "continent": known["key"].split("/", 1)[0],
            "slug": known["key"].split("/", 1)[1],
            "area_id": known["area_id"],
            "ui_map_id": known["ui_map_id"],
            "locale_key": known["locale_key"],
            "constant": constant,
            "category_id": constants.get(constant),
            "lua_file": lua_file,
            "chains_locked": True,
            "chains": chains,
            "quest_ids": quest_ids,
        })
        state["zones"][known["key"]] = zone

    for quest_id, body in _blocks(quests_text):
        numeric_id = int(quest_id)
        source = re.search(r'type = "npc",\s*id = (\d+)', body)
        faction = re.search(r'id = "(Alliance|Horde)"', body)
        current = state["quests"].get(quest_id, {})
        current.update({
            "zone": chain_owner.get(numeric_id) or current.get("zone"),
            "name_en": _lua_string(body, "name"),
            "name_pt": names_pt.get(numeric_id) or current.get("name_pt"),
            "level": int(re.search(r"level = (\d+)", body).group(1)) if re.search(r"level = (\d+)", body) else current.get("level"),
            "required_level": int(re.search(r"requiredLevel = (\d+)", body).group(1)) if re.search(r"requiredLevel = (\d+)", body) else current.get("required_level"),
            "side": {"Alliance": 1, "Horde": 2}.get(faction.group(1) if faction else None, current.get("side")),
            "source": {"type": "npc", "id": int(source.group(1))} if source else current.get("source"),
            "series_known": numeric_id in chain_owner or current.get("series_known", False),
            "in_addon": True,
        })
        state["quests"][quest_id] = current

    npcs = _npc_blocks((ADDON / "Database" / "NPCs.lua").read_text(encoding="utf-8"))
    for npc_id, npc in npcs.items():
        npc["name_pt"] = npc_pt.get(int(npc_id))
        state["npcs"][npc_id] = npc

    locales = (ADDON / "Localization.lua").read_text(encoding="utf-8")
    locales_pt = (ADDON / "Localization.ptBR.lua").read_text(encoding="utf-8")
    for zone in state["zones"].values():
        key = zone.get("locale_key")
        if not key:
            continue
        match = re.search(rf'L\["{key}"\] = "(.*)"', locales)
        match_pt = re.search(rf'L\["{key}"\] = "(.*)"', locales_pt)
        if match:
            zone["name_en"] = match.group(1)
        if match_pt:
            zone["name_pt"] = match_pt.group(1)
        for chain in zone.get("chains") or []:
            chain_key = chain.get("locale_key")
            match = re.search(rf'L\["{chain_key}"\] = "(.*)"', locales)
            match_pt = re.search(rf'L\["{chain_key}"\] = "(.*)"', locales_pt)
            if match:
                chain["name_en"] = match.group(1)
            if match_pt:
                chain["name_pt"] = match_pt.group(1)
    return state
