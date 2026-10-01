"""Séries completas: a ordem dos capítulos não depende da lista de uma zona."""


def series_groups(quest_ids, quests):
    candidates = {}
    for quest_id in quest_ids:
        series = tuple(dict.fromkeys(quests.get(str(quest_id), {}).get("series") or [quest_id]))
        if len(series) > 1:
            candidates[series] = series
    # Algumas páginas omitem o último capítulo. A versão completa prevalece.
    groups = [
        list(series) for series in candidates
        if not any(len(other) > len(series) and _subsequence(series, other) for other in candidates)
    ]
    used = {quest_id for series in groups for quest_id in series}
    return groups, [quest_id for quest_id in quest_ids if quest_id not in used]


def _subsequence(short, long):
    remaining = iter(long)
    return all(any(item == wanted for item in remaining) for wanted in short)


def missing_members(quest_ids, quests):
    return [
        quest_id for quest_id in quest_ids
        if not quests.get(str(quest_id), {}).get("name_en")
        or not quests.get(str(quest_id), {}).get("quest_zone_id")
        or not quests.get(str(quest_id), {}).get("series_known")
        or quests.get(str(quest_id), {}).get("fetch_error")
    ]
