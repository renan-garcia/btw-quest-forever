from lib import http_cache

META_URL = "https://forever.warcraftdb.com/api/data/list/quests/meta"
LIST_URL = "https://forever.warcraftdb.com/api/data/list/quests"
NODE_URL = "https://forever.warcraftdb.com/api/data/node/quest/{}"


def _zone_labels(nodes, found):
    for node in nodes or []:
        if "value" in node and "label" in node:
            found[int(node["value"])] = node["label"]
        _zone_labels(node.get("children"), found)
    return found


def zone_names(refresh=False):
    meta = http_cache.get_json(META_URL, refresh=refresh)
    found = {}
    for item in meta.get("list_filters") or []:
        if item.get("key") == "zone":
            _zone_labels(item.get("options"), found)
    return found


def quests_for_area(area_id, refresh=False):
    page = 1
    rows = []
    total = None
    while True:
        url = f"{LIST_URL}?page={page}&per_page=100&filter_zone={area_id}"
        payload = http_cache.get_json(url, refresh=refresh)
        rows.extend(payload.get("rows") or [])
        total = payload.get("total") or 0
        pages = payload.get("pages") or 1
        if page >= pages:
            break
        page += 1
    return rows, total


def quest_node(quest_id, refresh=False):
    payload = http_cache.get_json(NODE_URL.format(quest_id), refresh=refresh)
    return payload.get("data") or {}
