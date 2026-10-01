from lib.state_store import FACTION_BY_SIDE
from lib.series import missing_members, series_groups


def _faction_of(quest_ids, quests):
    sides = {quests[str(quest_id)].get("side") for quest_id in quest_ids}
    sides.discard(None)
    if sides == {1}:
        return "Alliance"
    if sides == {2}:
        return "Horde"
    return None


def _range(quest_ids, quests):
    levels = [quests[str(quest_id)].get("level") or 1 for quest_id in quest_ids]
    required = [quests[str(quest_id)].get("required_level") or 1 for quest_id in quest_ids]
    return min(levels), max(levels), min(required)


def _listed_here(zone, quests, quest_id, quest_ids):
    if quest_id not in quest_ids and str(quest_id) not in quests:
        return False
    quest = quests.get(str(quest_id)) or {}
    if quest.get("placement_pending"):
        return False
    if quest.get("chain_zone"):
        return quest["chain_zone"] == f"{zone['continent']}/{zone['slug']}"
    zone_id = quest.get("quest_zone_id")
    own = zone.get("area_id")
    if zone.get("new_region"):
        return not zone_id or zone_id == own
    if zone_id and own and zone_id != own:
        return False
    return quest_id in quest_ids or str(quest_id) in quests


def group_chains(zone, quests):
    preserved = [chain for chain in (zone.get("chains") or []) if chain.get("from_class")]
    if zone.get("chains_locked") and zone.get("chains"):
        return zone["chains"]

    parked = {quest_id for chain in preserved for quest_id in chain.get("quests") or []}
    quest_ids = [quest_id for quest_id in (zone.get("quest_ids") or []) if quest_id not in parked]
    candidates, leftovers = series_groups(quest_ids, quests)
    grouped = [series for series in candidates if not missing_members(series, quests)
               and all(item not in parked and _listed_here(zone, quests, item, quest_ids) for item in series)]
    leftovers = [item for item in leftovers if _listed_here(zone, quests, item, quest_ids)]
    old_ids = {tuple(chain["quests"]): chain.get("id") for chain in zone.get("chains") or []}
    by_faction = {"Alliance": [], "Horde": [], None: []}
    for quest_id in leftovers:
        faction = FACTION_BY_SIDE.get(quests[str(quest_id)].get("side"))
        by_faction[faction].append(quest_id)

    chains = []
    for index, series in enumerate(grouped, start=1):
        low, high, required = _range(series, quests)
        first = quests[str(series[0])]
        chains.append({
            "id": old_ids.get(tuple(series)),
            "constant": f"Series{index}",
            "locale_key": f"{zone['constant']}_{index}",
            "quests": series,
            "range": [low, high],
            "required_level": required,
            "complete_all": False,
            "faction": _faction_of(series, quests),
            "name_en": first.get("name_en") or f"Series {index}",
            "name_pt": first.get("name_pt") or first.get("name_en"),
        })

    labels = {
        "Alliance": ("Other", "Outras missões"),
        "Horde": ("OtherHorde", "Outras missões"),
        None: ("Neutral", "Missões neutras"),
    }
    for faction, bucket in by_faction.items():
        if not bucket:
            continue
        bucket.sort(key=lambda quest_id: ((quests[str(quest_id)].get("level") or 0), quest_id))
        low, high, required = _range(bucket, quests)
        suffix, pt_name = labels[faction]
        chains.append({
            "id": old_ids.get(tuple(bucket)),
            "constant": suffix,
            "locale_key": f"{zone['constant']}_{suffix}",
            "quests": bucket,
            "range": [low, high],
            "required_level": required,
            "complete_all": True,
            "faction": faction,
            "name_en": "Other quests" if faction else "Neutral quests",
            "name_pt": pt_name,
        })
    return chains + preserved


def allocate_ids(state, zone):
    if zone.get("category_id") and all(chain.get("id") for chain in zone.get("chains") or []):
        return
    used_categories = [item.get("category_id") or 16000 for item in state["zones"].values()]
    zone.setdefault("category_id", max(used_categories) + 1)
    used_chains = [
        chain["id"]
        for item in state["zones"].values()
        for chain in (item.get("chains") or [])
        if chain.get("id")
    ]
    next_id = ((max(used_chains or [160100]) // 100) + 1) * 100 + 1
    for chain in zone["chains"]:
        if not chain.get("id"):
            chain["id"] = next_id
            next_id += 1
