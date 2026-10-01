import hashlib
import threading
import time
import urllib.request
from pathlib import Path

from lib.paths import CACHE

_LOCK = threading.Lock()
_PACE = threading.Lock()
_DELAY = 0.0
_NEXT = 0.0
HEADERS = {"User-Agent": "Mozilla/5.0 (BtWQuestsForever tooling)"}


def set_delay(seconds):
    global _DELAY
    _DELAY = max(0.0, float(seconds or 0))


def _wait_turn(url):
    global _NEXT
    if not _DELAY or "wowhead.com" not in url:
        return
    with _PACE:
        wait = _NEXT - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _NEXT = time.monotonic() + _DELAY


def _path_for(url):
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
    return CACHE / digest[:2] / digest


def get(url, refresh=False, timeout=40):
    path = _path_for(url)
    if path.exists() and not refresh:
        return path.read_text(encoding="utf-8")

    _wait_turn(url)
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        text = response.read().decode("utf-8", "replace")

    with _LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    return text


def get_json(url, refresh=False, timeout=40):
    import json

    return json.loads(get(url, refresh=refresh, timeout=timeout))
