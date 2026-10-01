import json
from datetime import datetime, timezone

from lib.paths import STATE_FILE

FACTION_BY_SIDE = {1: "Alliance", 2: "Horde"}


def empty():
    return {
        "version": 1,
        "updated_at": None,
        "zones": {},
        "quests": {},
        "npcs": {},
        "summary": {},
    }


def load():
    if not STATE_FILE.exists():
        return empty()
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    for key, value in empty().items():
        state.setdefault(key, value)
    return state


def quest_gaps(quest):
    gaps = []
    if not quest.get("in_addon"):
        gaps.append("fora_do_addon")
    name_pt = quest.get("name_pt") or ""
    if not name_pt or name_pt.startswith("["):
        gaps.append("nome_pt")
    if not quest.get("source"):
        gaps.append("origem")
    if not quest.get("series_known"):
        gaps.append("serie")
    if quest.get("placement_pending"):
        gaps.append("categoria")
    return gaps


def npc_gaps(npc):
    gaps = []
    if not npc.get("in_addon"):
        gaps.append("fora_do_addon")
    if not npc.get("locations"):
        gaps.append("coordenada")
    name_pt = npc.get("name_pt") or ""
    if not name_pt or name_pt.startswith("["):
        gaps.append("nome_pt")
    return gaps


def zone_status(zone, quests):
    if zone.get("placed_into") and not zone.get("lua_file"):
        if not zone.get("placed_into"):
            return "pending"
        if zone.get("quest_ids"):
            return "partial"
        return "done"
    if not zone.get("lua_file"):
        return "pending"
    quest_ids = list(dict.fromkeys((zone.get("quest_ids") or []) + [
        quest_id for chain in zone.get("chains") or [] for quest_id in chain.get("quests") or []
    ]))
    if not quest_ids:
        return "pending"
    for quest_id in quest_ids:
        quest = quests.get(str(quest_id))
        if quest is None or quest_gaps(quest):
            return "partial"
    return "done"


def refresh_summary(state):
    for zone in state["zones"].values():
        zone["status"] = zone_status(zone, state["quests"])

    missing_source = []
    missing_pt = []
    missing_series = []
    outside = []
    for quest_id, quest in state["quests"].items():
        gaps = quest_gaps(quest)
        if "origem" in gaps:
            missing_source.append(int(quest_id))
        if "nome_pt" in gaps:
            missing_pt.append(int(quest_id))
        if "serie" in gaps:
            missing_series.append(int(quest_id))
        if "fora_do_addon" in gaps:
            outside.append(int(quest_id))

    npcs_missing = []
    for npc_id, npc in state["npcs"].items():
        if npc_gaps(npc):
            npcs_missing.append(int(npc_id))

    zones = state["zones"]
    state["summary"] = {
        "zones_total": len(zones),
        "zones_done": sum(1 for zone in zones.values() if zone.get("status") == "done"),
        "zones_partial": sum(1 for zone in zones.values() if zone.get("status") == "partial"),
        "zones_pending": sum(1 for zone in zones.values() if zone.get("status") == "pending"),
        "quests": len(state["quests"]),
        "quests_missing_source": sorted(missing_source),
        "quests_missing_pt": sorted(missing_pt),
        "quests_missing_series": sorted(missing_series),
        "quests_outside_addon": sorted(outside),
        "npcs": len(state["npcs"]),
        "npcs_with_gaps": sorted(npcs_missing),
    }
    return state["summary"]


def save(state):
    refresh_summary(state)
    state["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return state["summary"]


def restrictions_for(side, reqclass, reqrace):
    restrictions = []
    faction = FACTION_BY_SIDE.get(side)
    if faction:
        restrictions.append({"type": "faction", "id": faction})
    classes = class_ids(reqclass or 0)
    if classes:
        if len(classes) == 1:
            restrictions.append({"type": "class", "id": classes[0]})
        else:
            restrictions.append({"type": "class", "ids": classes})
    races = race_ids(reqrace or 0)
    if races:
        if len(races) == 1:
            restrictions.append({"type": "race", "id": races[0]})
        else:
            restrictions.append({"type": "race", "ids": races})
    return restrictions


CLASS_BITS = (
    (1, 1),
    (2, 2),
    (4, 3),
    (8, 4),
    (16, 5),
    (32, 6),
    (64, 7),
    (128, 8),
    (256, 9),
    (512, 10),
    (1024, 11),
    (2048, 12),
)

RACE_BITS = (
    (1, "Human"),
    (2, "Orc"),
    (4, "Dwarf"),
    (8, "NightElf"),
    (16, "Scourge"),
    (32, "Tauren"),
    (64, "Gnome"),
    (128, "Troll"),
    (256, "Goblin"),
    (512, "BloodElf"),
    (1024, "Draenei"),
    (2097152, "Worgen"),
    (4294967296, "Skyborne"),  # Celonato da Alta Ordem. UnitRace devolve "Skyborne"; 95 Aliança, 96 Horda.
)


def class_ids(mask):
    return [class_id for bit, class_id in CLASS_BITS if mask & bit]


def race_ids(mask):
    return [race for bit, race in RACE_BITS if mask & bit]
