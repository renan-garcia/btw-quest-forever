import re

from lib.leveling import is_leveling_zone
from lib.paths import ADDON

_PUNCT = re.compile(r"[,.?:;!'\"\-()]")
TOC_FILES = ("BtWQuestsForever.toc", "BtWQuestsForever_Camelot.toc")


def write_search_indexes(state):
    items = _items(state)
    _write_index("enUS", items, "en")
    _write_index("ptBR", items, "pt")
    _ensure_toc()


def _items(state):
    found = []
    for zone in state["zones"].values():
        if not is_leveling_zone(zone) or not zone.get("category_id"):
            continue
        zone_en = zone.get("name_en") or zone.get("constant") or ""
        zone_pt = zone.get("name_pt") or zone_en
        category_restrictions = _category_restrictions(zone)
        found.append({
            "en": zone_en,
            "pt": zone_pt,
            "type": "category",
            "link": f"btwquests:category:{int(zone['category_id'])}",
            "path_en": "Forever",
            "path_pt": "Forever",
            "restrictions": category_restrictions,
        })
        zone_path_en = f"Forever > {zone_en}" if zone_en else "Forever"
        zone_path_pt = f"Forever > {zone_pt}" if zone_pt else "Forever"
        for chain in zone.get("chains") or []:
            if not chain.get("id"):
                continue
            chain_en = chain.get("name_en") or chain.get("constant") or ""
            chain_pt = chain.get("name_pt") or chain_en
            chain_restrictions = _chain_restrictions(chain)
            found.append({
                "en": chain_en,
                "pt": chain_pt,
                "type": "chain",
                "link": f"btwquests:chain:{int(chain['id'])}",
                "path_en": zone_path_en,
                "path_pt": zone_path_pt,
                "restrictions": chain_restrictions,
            })
            chain_path_en = f"{zone_path_en} > {chain_en}" if chain_en else zone_path_en
            chain_path_pt = f"{zone_path_pt} > {chain_pt}" if chain_pt else zone_path_pt
            for quest_id in chain.get("quests") or []:
                quest = state["quests"].get(str(quest_id)) or {}
                quest_en = quest.get("name_en") or ""
                quest_pt = quest.get("name_pt") or quest_en
                if not quest_en and not quest_pt:
                    continue
                found.append({
                    "en": quest_en or quest_pt,
                    "pt": quest_pt or quest_en,
                    "type": "quest",
                    "link": f"btwquests:chain:{int(chain['id'])}",
                    "path_en": chain_path_en,
                    "path_pt": chain_path_pt,
                    "restrictions": quest.get("restrictions") or chain_restrictions,
                    "scroll_to": int(quest_id),
                })
    return found


def _category_restrictions(zone):
    factions = {chain.get("faction") for chain in zone.get("chains") or [] if chain.get("faction")}
    if len(factions) == 1:
        return [{"type": "faction", "id": next(iter(factions))}]
    return []


def _chain_restrictions(chain):
    restrictions = []
    if chain.get("faction"):
        restrictions.append({"type": "faction", "id": chain["faction"]})
    if chain.get("class_id"):
        restrictions.append({"type": "class", "id": int(chain["class_id"])})
    if chain.get("race_id"):
        restrictions.append({"type": "race", "id": chain["race_id"]})
    return restrictions


def _write_index(locale, items, field):
    lines = [
        f'if GetLocale() ~= "{locale}" then',
        "    return",
        "end",
        "",
        "local i = {",
    ]
    buckets = {}
    for index, item in enumerate(items, start=1):
        name = item[field] or item["en"] or item["pt"]
        lines.append("    {")
        lines.append(f"        name = {_lua(name)},")
        lines.append(f"        type = {_lua(item['type'])},")
        lines.append(f"        link = {_lua(item['link'])},")
        lines.append(f"        path = {_lua(item['path_' + field])},")
        if item.get("scroll_to"):
            lines.append(f"        scrollTo = {{ type = \"quest\", id = {item['scroll_to']} }},")
            lines.append(f"        tooltip = {_lua('quest:' + str(item['scroll_to']))},")
        if item.get("restrictions"):
            lines.extend(_restrictions(item["restrictions"], "        "))
        lines.append("    },")
        for prefix in _prefixes(name):
            buckets.setdefault(prefix, []).append(index)
    lines.append("}")
    lines.append("")
    lines.append("BtWQuestsDatabase:AddSearchBuckets({")
    for prefix in sorted(buckets):
        refs = ", ".join(f"i[{index}]" for index in buckets[prefix])
        lines.append(f"    [{_lua(prefix)}] = {{ {refs} }},")
    lines.append("})")
    lines.append("")
    path = ADDON / "Database" / f"Index.{locale}.lua"
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def _prefixes(name):
    text = _PUNCT.sub("", (name or "").lower())
    if not text:
        return []
    if len(text) <= 3:
        return [text]
    return [text[index:index + 3] for index in range(len(text) - 2)]


def _restrictions(restrictions, indent):
    if len(restrictions) == 1:
        lines = [f"{indent}restrictions = {{"]
        lines.extend(_restriction_fields(restrictions[0], indent + "    "))
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
    lines = [f"{indent}type = {_lua(item['type'])},"]
    if "id" in item:
        value = item["id"]
        rendered = str(value) if isinstance(value, int) else _lua(value)
        lines.append(f"{indent}id = {rendered},")
    if item.get("ids"):
        parts = [str(value) if isinstance(value, int) else _lua(value) for value in item["ids"]]
        lines.append(f"{indent}ids = {{ {', '.join(parts)} }},")
    return lines


def _lua(value):
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


def _ensure_toc():
    for name in TOC_FILES:
        path = ADDON / name
        text = path.read_text(encoding="utf-8")
        if "Database/Index.ptBR.lua" in text:
            continue
        text = text.replace(
            "Database/Index.enUS.lua\n",
            "Database/Index.enUS.lua\nDatabase/Index.ptBR.lua\n",
        )
        path.write_text(text, encoding="utf-8", newline="\n")
