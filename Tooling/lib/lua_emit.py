import re

from lib.paths import ADDON
from lib.state_store import restrictions_for
from lib.uimap import BUTTON_IMAGE_BY_UI_MAP, UI_MAP_BY_AREA
from lib.leveling import is_leveling_zone

TOC_FILES = ("BtWQuestsForever.toc", "BtWQuestsForever_Camelot.toc")


def _lua_number(value):
    return f"{float(value):.4f}".rstrip("0").rstrip(".")


def lua_string(value):
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


def _restriction_block(restrictions, indent):
    if len(restrictions) == 1:
        item = restrictions[0]
        lines = [f"{indent}restrictions = {{"]
        lines.extend(_restriction_fields(item, indent + "    "))
        lines.append(f"{indent}}},")
        return lines
    lines = [f"{indent}restrictions = {{"]
    for item in restrictions:
        lines.append(f"{indent}    {{")
        lines.extend(_restriction_fields(item, indent + "        "))
        lines.append(f"{indent}    }},")
    lines.append(f"{indent}}},")
    return lines


def _restriction_fields(item, indent):
    lines = [f"{indent}type = {lua_string(item['type'])},"]
    if "id" in item:
        value = item["id"]
        rendered = value if isinstance(value, int) else lua_string(value)
        lines.append(f"{indent}id = {rendered},")
    if "ids" in item:
        parts = []
        for value in item["ids"]:
            parts.append(str(value) if isinstance(value, int) else lua_string(value))
        lines.append(f"{indent}ids = {{ {', '.join(parts)} }},")
    return lines


def _quest_restrictions(quest):
    if "reqrace" in quest or "reqclass" in quest or "side" in quest:
        return restrictions_for(quest.get("side"), quest.get("reqclass") or 0, quest.get("reqrace") or 0)
    return quest.get("restrictions") or []


def write_quests(state):
    lines = ["BtWQuestsDatabase:AddQuestsTable({"]
    pt_lines = [
        'if GetLocale() ~= "ptBR" then',
        "    return",
        "end",
        "",
        "BtWQuestsDatabase:UpdateQuestsTable({",
    ]
    for quest_id in sorted((int(item) for item in state["quests"]), key=int):
        quest = state["quests"][str(quest_id)]
        quest["in_addon"] = bool(quest.get("name_en"))
        if not quest.get("name_en"):
            continue
        lines.append(f"    [{quest_id}] = {{")
        lines.append(f"        name = {lua_string(quest['name_en'])},")
        if quest.get("level") is not None:
            lines.append(f"        level = {int(quest['level'])},")
        if quest.get("required_level") is not None:
            lines.append(f"        requiredLevel = {int(quest['required_level'])},")
        restrictions = _quest_restrictions(quest)
        if restrictions:
            lines.extend(_restriction_block(restrictions, "        "))
        source = quest.get("source")
        if source and source.get("type") == "coords" and source.get("mapID") is not None:
            lines.extend([
                "        source = {",
                '            type = "coords",',
                f"            mapID = {int(source['mapID'])},",
                f"            x = {_lua_number(source['x'])},",
                f"            y = {_lua_number(source['y'])},",
                "        },",
            ])
        elif source and source.get("id"):
            lines.extend([
                "        source = {",
                f"            type = {lua_string(source.get('type') or 'npc')},",
                f"            id = {int(source['id'])},",
                "        },",
            ])
        lines.append("    },")
        name_pt = quest.get("name_pt") or ""
        if name_pt and not (name_pt.startswith("[") and name_pt.endswith("]")):
            pt_lines.extend([
                f"    [{quest_id}] = {{",
                f"        name = {lua_string(quest['name_pt'])},",
                "    },",
            ])
    lines.append("})")
    pt_lines.append("})")
    _write(ADDON / "Database" / "Quests.lua", lines)
    _write(ADDON / "Database" / "Quests.ptBR.lua", pt_lines)


def write_npcs(state):
    lines = ["BtWQuestsDatabase:AddNPCsTable({"]
    pt_lines = [
        'if GetLocale() ~= "ptBR" then',
        "    return",
        "end",
        "",
        "BtWQuestsDatabase:UpdateNPCsTable({",
    ]
    for npc_id in sorted((int(item) for item in state["npcs"]), key=int):
        npc = state["npcs"][str(npc_id)]
        locations = npc.get("locations") or {}
        npc["in_addon"] = bool(npc.get("name_en"))
        if not npc.get("name_en"):
            continue
        lines.append(f"    [{npc_id}] = {{")
        lines.append(f"        name = {lua_string(npc['name_en'])},")
        lines.append("        locations = {")
        for map_id in sorted(locations, key=int):
            lines.append(f"            [{int(map_id)}] = {{")
            for point in locations[map_id]:
                lines.extend([
                    "                {",
                    f"                    x = {_lua_number(point['x'])},",
                    f"                    y = {_lua_number(point['y'])},",
                    "                },",
                ])
            lines.append("            },")
        lines.extend(["        },", "    },"])
        if npc.get("name_pt") and not (npc["name_pt"].startswith("[") and npc["name_pt"].endswith("]")):
            pt_lines.extend([
                f"    [{npc_id}] = {{",
                f"        name = {lua_string(npc['name_pt'])},",
                "    },",
            ])
    lines.append("})")
    pt_lines.append("})")
    _write(ADDON / "Database" / "NPCs.lua", lines)
    _write(ADDON / "Database" / "NPCs.ptBR.lua", pt_lines)


def write_zone(zone):
    constant = zone["constant"]
    lines = [
        "local L = BtWQuests.L",
        "local Database = BtWQuests.Database",
        "local EXPANSION_ID = BtWQuests.Constant.Expansions.Forever",
        f"local CATEGORY_ID = BtWQuests.Constant.Category.Forever.{constant}",
        f"local Chain = BtWQuests.Constant.Chain.Forever.{constant}",
        "local AddChain = BtWQuests.ForeverBuilder.AddChain",
        "",
    ]
    for chain in zone.get("chains") or []:
        lines.append(f"Chain.{chain['constant']} = {int(chain['id'])}")
    lines.append("")
    for chain in zone.get("chains") or []:
        lines.append(chain_call(chain))
    lines.extend([
        "",
        "Database:AddCategory(CATEGORY_ID, {",
        f"    name = {_category_name(zone)},",
        "    expansion = EXPANSION_ID,",
    ])
    texture = _button_texture(zone)
    if texture:
        lines.extend([
            "    buttonImage = {",
            f"        texture = {texture},",
            "        texCoords = {0, 1, 0, 1},",
            "    },",
        ])
    restrictions = _category_restrictions(zone)
    if restrictions:
        lines.extend(_restriction_block(restrictions, "    "))
    lines.append("    items = {")
    for chain in zone.get("chains") or []:
        lines.extend([
            "        {",
            '            type = "chain",',
            f"            id = Chain.{chain['constant']},",
            "        },",
        ])
    lines.extend(["    },", "})", ""])
    path = ADDON / zone["lua_file"]
    path.parent.mkdir(parents=True, exist_ok=True)
    _write(path, lines)


def write_registers(state):
    zones = [zone for zone in state["zones"].values() if zone.get("category_id") and zone.get("constant")]
    zones.sort(key=lambda zone: zone["category_id"])
    _patch_defines(zones)
    _patch_general(zones)
    _patch_toc(zones)
    _patch_locales(zones)


def _patch_defines(zones):
    path = ADDON / "Defines.lua"
    text = path.read_text(encoding="utf-8")
    categories = ",\n".join(f"    {zone['constant']} = {int(zone['category_id'])}" for zone in zones)
    chains = ",\n".join(f"    {zone['constant']} = {{}}" for zone in zones)
    text = re.sub(
        r"BtWQuests\.Constant\.Category\.Forever = \{.*?\n\}",
        "BtWQuests.Constant.Category.Forever = {\n" + (categories + ",\n" if categories else "") + "}",
        text,
        count=1,
        flags=re.S,
    )
    text = re.sub(
        r"BtWQuests\.Constant\.Chain\.Forever = \{.*?\n\}",
        "BtWQuests.Constant.Chain.Forever = {\n" + (chains + ",\n" if chains else "") + "}",
        text,
        count=1,
        flags=re.S,
    )
    path.write_text(text, encoding="utf-8", newline="\n")


def _patch_general(zones):
    items = []
    for zone in zones:
        items.extend([
            "    {",
            '        type = "category",',
            f"        id = BtWQuests.Constant.Category.Forever.{zone['constant']},",
            "    },",
        ])
    text = "\n".join([
        "local Database = BtWQuests.Database",
        "local EXPANSION_ID = BtWQuests.Constant.Expansions.Forever",
        "",
        "Database:AddExpansionItems(EXPANSION_ID, {",
        *items,
        "})",
        "",
    ])
    (ADDON / "General.lua").write_text(text, encoding="utf-8", newline="\n")


def _patch_toc(zones):
    wanted = ["ZoneBuilder.lua"]
    wanted.extend(zone["lua_file"].replace("\\", "/") for zone in zones)
    wanted_set = set(wanted)
    for name in TOC_FILES:
        path = ADDON / name
        lines = path.read_text(encoding="utf-8").splitlines()
        body = [
            line for line in lines
            if line not in wanted_set and not (line.startswith("Zones/") and line.endswith(".lua"))
        ]
        if "General.lua" not in body:
            raise RuntimeError(f"{name} não tem General.lua")
        index = body.index("General.lua")
        body[index:index] = wanted
        path.write_text("\n".join(body) + "\n", encoding="utf-8", newline="\n")


def _patch_locales(zones):
    keys = {}
    for zone in zones:
        keys[zone["locale_key"]] = (zone.get("name_en") or zone["constant"], zone.get("name_pt") or zone.get("name_en") or zone["constant"])
        for chain in zone.get("chains") or []:
            if chain.get("locale_key"):
                keys[chain["locale_key"]] = (chain.get("name_en") or chain["locale_key"], chain.get("name_pt") or chain.get("name_en") or chain["locale_key"])
    _merge_locale(ADDON / "Localization.lua", {key: value[0] for key, value in keys.items()})
    _merge_locale(ADDON / "Localization.ptBR.lua", {key: value[1] for key, value in keys.items()})


def _merge_locale(path, keys):
    text = path.read_text(encoding="utf-8")
    for key, value in keys.items():
        line = f'L["{key}"] = {lua_string(value)}'
        pattern = rf'L\["{re.escape(key)}"\] = ".*"'
        if re.search(pattern, text):
            text = re.sub(pattern, line, text, count=1)
        else:
            text = text.rstrip() + "\n" + line + "\n"
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8", newline="\n")


def chain_call(chain, qualified=False):
    name = "BtWQuests.ForeverBuilder.AddChain" if qualified else "AddChain"
    quests = ", ".join(str(quest_id) for quest_id in chain["quests"])
    faction = "nil" if not chain.get("faction") else lua_string(chain["faction"])
    complete = "true" if chain.get("complete_all") else "false"
    low, high = chain["range"]
    class_id = "nil" if not chain.get("class_id") else str(int(chain["class_id"]))
    race_id = _lua_race(chain.get("race_id"))
    return (
        f'{name}(Chain.{chain["constant"]}, CATEGORY_ID, L["{chain["locale_key"]}"], '
        f"{{ {quests} }}, {low}, {high}, {int(chain['required_level'])}, {complete}, {faction}, {class_id}, {race_id})"
    )


def _lua_race(race_id):
    if not race_id:
        return "nil"
    if isinstance(race_id, int):
        return str(race_id)
    return lua_string(race_id)


def _button_texture(zone):
    if zone.get("new_region") and not zone.get("ui_map_id"):
        return None
    map_id = zone.get("ui_map_id") or UI_MAP_BY_AREA.get(zone.get("area_id"))
    if not map_id:
        return None
    return BUTTON_IMAGE_BY_UI_MAP.get(int(map_id))


def _category_name(zone):
    if zone.get("new_region"):
        if zone.get("ui_map_id"):
            return f"BtWQuests.GetMapName({int(zone['ui_map_id'])})"
        return f'L["{zone["locale_key"]}"]'
    map_id = zone.get("ui_map_id") or UI_MAP_BY_AREA.get(zone.get("area_id"))
    if map_id:
        return f"BtWQuests.GetMapName({int(map_id)})"
    return f'L["{zone["locale_key"]}"]'


def _category_restrictions(zone):
    restrictions = []
    factions = {chain.get("faction") for chain in zone.get("chains") or [] if chain.get("faction")}
    if len(factions) == 1:
        restrictions.append({"type": "faction", "id": next(iter(factions))})
    shared_class = _shared_class(zone)
    if shared_class:
        restrictions.append({"type": "class", "id": shared_class})
    shared_race = _shared_race(zone)
    if shared_race is not None:
        restrictions.append({"type": "race", "id": shared_race})
    return restrictions


def _shared_race(zone):
    races = {chain.get("race_id") for chain in zone.get("chains") or []}
    if len(races) == 1:
        race_id = next(iter(races))
        if race_id:
            return race_id
    return None


def _shared_class(zone):
    class_ids = {chain.get("class_id") for chain in zone.get("chains") or []}
    if len(class_ids) == 1:
        class_id = next(iter(class_ids))
        if class_id:
            return int(class_id)
    return None


def _write_one(zone):
    if zone.get("chains_locked"):
        append_class_chains(zone)
        return
    if zone.get("lua_file") and zone.get("category_id"):
        write_zone(zone)


def append_class_chains(zone):
    path = ADDON / zone["lua_file"]
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    # Retira também blocos cuja cadeia mudou para outra categoria.
    text = re.sub(r"-- class chains: [^\n]+\n.*?-- end class chains: [^\n]+\n?", "", text, flags=re.S)
    text = re.sub(r"        -- class item: [^\n]+\n.*?        -- end class item: [^\n]+\n?", "", text, flags=re.S)
    groups = {}
    for chain in zone.get("chains") or []:
        origin = chain.get("from_class")
        if origin:
            groups.setdefault(origin, []).append(chain)
    for origin, chains in groups.items():
        text = _upsert_block(
            text,
            f"-- class chains: {origin}",
            f"-- end class chains: {origin}",
            _class_call_block(origin, chains),
            "Database:AddCategory",
        )
        text = _upsert_block(
            text,
            f"        -- class item: {origin}",
            f"        -- end class item: {origin}",
            _class_item_block(origin, chains),
            "    },\n})",
        )
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8", newline="\n")


def _class_call_block(origin, chains):
    lines = [f"-- class chains: {origin}"]
    for chain in chains:
        lines.append(f"Chain.{chain['constant']} = {int(chain['id'])}")
        lines.append(chain_call(chain, qualified=True))
    lines.append(f"-- end class chains: {origin}")
    return "\n".join(lines)


def _class_item_block(origin, chains):
    lines = [f"        -- class item: {origin}"]
    for chain in chains:
        lines.extend([
            "        {",
            '            type = "chain",',
            f"            id = Chain.{chain['constant']},",
            "        },",
        ])
    lines.append(f"        -- end class item: {origin}")
    return "\n".join(lines)


def _upsert_block(text, begin, end, block, anchor):
    pattern = re.compile(rf"{re.escape(begin)}.*?{re.escape(end)}\n?", re.S)
    if pattern.search(text):
        return pattern.sub(block + "\n", text, count=1)
    index = text.rfind(anchor) if anchor.startswith("    },") else text.find(anchor)
    if index < 0 and "\n" in anchor:
        crlf = anchor.replace("\n", "\r\n")
        index = text.rfind(crlf) if anchor.startswith("    },") else text.find(crlf)
    if index < 0:
        raise RuntimeError(f"Não achei {anchor!r} para encaixar a cadeia de classe.")
    return text[:index] + block + "\n" + text[index:]


def _stamp_race_limits(state):
    from lib.state_store import race_ids

    for quest in state["quests"].values():
        if "reqrace" in quest or "reqclass" in quest or "side" in quest:
            quest["restrictions"] = restrictions_for(quest.get("side"), quest.get("reqclass") or 0, quest.get("reqrace") or 0)
    for zone in state["zones"].values():
        for chain in zone.get("chains") or []:
            found = set()
            open_race = False
            for quest_id in chain.get("quests") or []:
                quest = state["quests"].get(str(quest_id)) or {}
                ids = race_ids(quest.get("reqrace") or 0)
                if len(ids) == 1:
                    found.add(ids[0])
                else:
                    open_race = True
            chain["race_id"] = next(iter(found)) if not open_race and len(found) == 1 else None


def _remove_retired_lua(state):
    for zone in state["zones"].values():
        old = zone.get("remove_lua")
        if not old:
            continue
        path = ADDON / old
        if path.exists():
            path.unlink()
        zone.pop("remove_lua", None)


def emit(state, zone_key=None):
    _stamp_race_limits(state)
    _remove_retired_lua(state)
    write_quests(state)
    write_npcs(state)
    if isinstance(zone_key, (list, tuple)):
        keys = list(zone_key)
    elif zone_key:
        keys = [zone_key]
    else:
        keys = [
            key for key, zone in state["zones"].items()
            if zone.get("lua_file") and zone.get("category_id") and is_leveling_zone(zone)
        ]
    for key in keys:
        zone = state["zones"].get(key)
        if zone and is_leveling_zone(zone):
            _write_one(zone)
    write_registers(state)
    from lib.search_index import write_search_indexes
    write_search_indexes(state)


def _write(path, lines):
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
