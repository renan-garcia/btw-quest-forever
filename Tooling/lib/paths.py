from pathlib import Path

TOOLING = Path(__file__).resolve().parents[1]
ADDONS = TOOLING.parent
ADDON = ADDONS / "BtWQuestsForever"
CACHE = TOOLING / "cache"
STATE_FILE = TOOLING / "state" / "progress.json"
