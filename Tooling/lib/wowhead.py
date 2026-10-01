import json
import re
from html import unescape

from lib import http_cache

QUESTS_URL = "https://www.wowhead.com/forever/quests"


def _json_at(text, index):
    value, _ = json.JSONDecoder().raw_decode(text, index)
    return value


def _walk_zones(nodes, continent=None):
    found = []
    for node in nodes:
        children = node.get("categories") or []
        url = node.get("url") or ""
        if children:
            next_continent = url if continent is None else continent
            found.extend(_walk_zones(children, next_continent))
        elif continent and url:
            found.append({
                "continent": continent,
                "slug": url,
                "area_id": int(node["id"]),
                "key": f"{continent}/{url}",
            })
    return found


def zone_tree(refresh=False):
    html = http_cache.get(QUESTS_URL, refresh=refresh)
    marker = "Filter.init("
    start = html.find(marker)
    if start < 0:
        raise RuntimeError("Wowhead não trouxe a árvore de zonas.")
    data = _json_at(html, start + len(marker))
    return _walk_zones(data.get("categories") or [])


def _list_rows(html):
    index = html.find("new Listview")
    if index < 0:
        raise RuntimeError("Página sem lista de missões.")
    data_at = html.find("data:", index)
    rows = _json_at(html, data_at + len("data:"))
    window = html[index:data_at]
    truncated = "_truncated" in window
    return rows, truncated


def zone_quest_rows(continent, slug, locale="en", refresh=False):
    if locale == "pt":
        url = f"https://www.wowhead.com/forever/pt/quests/{continent}/{slug}"
    else:
        url = f"https://www.wowhead.com/forever/quests/{continent}/{slug}"
    html = http_cache.get(url, refresh=refresh)
    rows, truncated = _list_rows(html)
    name = None
    match = re.search(r"in <b>([^<]+)</b>", html)
    if match:
        name = match.group(1)
    return rows, truncated, name


def _object_after(html, marker):
    index = html.find(marker)
    if index < 0:
        return None
    start = html.find("{", index)
    if start < 0:
        return None
    return _json_at(html, start)


def quest_page(quest_id, refresh=False, locale="en"):
    if locale == "pt":
        url = f"https://www.wowhead.com/forever/pt/quest={quest_id}"
    else:
        url = f"https://www.wowhead.com/forever/quest={quest_id}"
    html = http_cache.get(url, refresh=refresh)
    gathered = _object_after(html, "WH.Gatherer.addData(5, 16,") or {}
    record = gathered.get(str(quest_id)) or {}
    details = _object_after(html, f"$.extend(g_quests[{int(quest_id)}],") or {}
    if not record and not details:
        raise RuntimeError(f"Página da missão {quest_id} sem dados da missão solicitada.")
    return {
        "name": unescape(details.get("name") or record.get("name_ptbr" if locale == "pt" else "name_enus") or ""),
        "category": details.get("category"),
        "level": details.get("level"),
        "required_level": details.get("reqlevel"),
        "reqclass": details.get("reqclass", record.get("reqclass")) or 0,
        "reqrace": details.get("reqrace", record.get("reqrace")) or 0,
        "side": details.get("side", record.get("_side", record.get("side"))),
        "series": _series(html, quest_id),
        "starts": _starts(html),
    }


def zone_title(area_id, locale="pt", refresh=False):
    prefix = "pt/" if locale == "pt" else ""
    url = f"https://www.wowhead.com/forever/{prefix}zone={int(area_id)}"
    html = http_cache.get(url, refresh=refresh)
    match = re.search(r"<h1[^>]*>([^<]+)</h1>", html)
    if not match:
        return None
    title = unescape(match.group(1)).strip()
    if title.startswith("[") and title.endswith("]"):
        return None
    return title


def _series(html, quest_id):
    match = re.search(r'<table class="series">(.*?)</table>', html, re.S)
    if not match:
        return [quest_id]
    ordered = []
    for row in re.findall(r"<tr>(.*?)</tr>", match.group(1), re.S):
        link = re.search(r"quest=(\d+)", row)
        if link:
            ordered.append(int(link.group(1)))
        elif "<b>" in row:
            ordered.append(int(quest_id))
    return ordered or [quest_id]


def _starts(html):
    mapped = _object_after(html, "new Mapper(")
    if not mapped:
        return []
    starts = []
    for area_key, zone in (mapped.get("objectives") or {}).items():
        try:
            area_id = int(area_key)
        except (TypeError, ValueError):
            area_id = None
        for level in zone.get("levels") or []:
            for point in level:
                if point.get("point") == "start" and point.get("id"):
                    item = dict(point)
                    item["area_id"] = area_id
                    starts.append(item)
    return starts
