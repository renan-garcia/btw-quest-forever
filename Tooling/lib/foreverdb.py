import re
from urllib.parse import unquote

from lib import http_cache


def zone_guide(slug, refresh=False):
    html = http_cache.get(f"https://foreverdb.net/quests/{slug}", refresh=refresh)
    quests = {}
    for href, quest_id in re.findall(r'href="(/quest/(\d+)[^"]*)"', html):
        quests[int(quest_id)] = "https://foreverdb.net" + href
    classic_note = "CMaNGOS" in html or "Classic data" in html
    return {"quests": quests, "classic_note": classic_note}


def quest_pin(url, refresh=False):
    html = http_cache.get(url, refresh=refresh)
    pins = []
    for map_id, x, y, name in re.findall(r"/maps/(\d+)\?pin=([\d.]+),([\d.]+),([^\"&]+)", html):
        pins.append({
            "map": int(map_id),
            "x": round(float(x) / 100, 4),
            "y": round(float(y) / 100, 4),
            "name": unquote(name),
        })
    pickup = None
    text = re.sub(r"<[^>]+>", " ", html)
    match = re.search(r"Pick up:\s*([^.<\n]+)", text)
    if match:
        pickup = match.group(1).strip()
    return {"pins": pins, "pickup": pickup}
