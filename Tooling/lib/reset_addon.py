import re

from lib.paths import ADDON
from lib.state_store import load, save

TOC_FILES = ("BtWQuestsForever.toc", "BtWQuestsForever_Camelot.toc")
KEEP_ZONE = ("continent", "slug", "area_id", "name_en", "name_pt")


def reset_addon():
    removed_files = _delete_zone_files()
    _reset_defines()
    _reset_general()
    _reset_databases()
    _reset_locales()
    _reset_tocs()
    quests, npcs, zones = _reset_state()
    return {
        "zone_files": removed_files,
        "quests": quests,
        "npcs": npcs,
        "zones": zones,
    }


def _delete_zone_files():
    removed = 0
    elwynn = ADDON / "ElwynnForest.lua"
    if elwynn.exists():
        elwynn.unlink()
        removed += 1
    zones = ADDON / "Zones"
    if zones.exists():
        for path in zones.glob("*.lua"):
            path.unlink()
            removed += 1
    return removed


def _reset_defines():
    path = ADDON / "Defines.lua"
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r"BtWQuests\.Constant\.Category\.Forever = \{.*?\n\}",
        "BtWQuests.Constant.Category.Forever = {\n}",
        text,
        count=1,
        flags=re.S,
    )
    text = re.sub(
        r"BtWQuests\.Constant\.Chain\.Forever = \{.*?\n\}",
        "BtWQuests.Constant.Chain.Forever = {\n}",
        text,
        count=1,
        flags=re.S,
    )
    path.write_text(text, encoding="utf-8", newline="\n")


def _reset_general():
    text = "\n".join([
        "local Database = BtWQuests.Database",
        "local EXPANSION_ID = BtWQuests.Constant.Expansions.Forever",
        "",
        "Database:AddExpansionItems(EXPANSION_ID, {",
        "})",
        "",
    ])
    (ADDON / "General.lua").write_text(text, encoding="utf-8", newline="\n")


def _reset_databases():
    (ADDON / "Database" / "Quests.lua").write_text(
        "BtWQuestsDatabase:AddQuestsTable({\n})\n",
        encoding="utf-8",
        newline="\n",
    )
    (ADDON / "Database" / "Quests.ptBR.lua").write_text(
        "if GetLocale() ~= \"ptBR\" then\n    return\nend\n\nBtWQuestsDatabase:UpdateQuestsTable({\n})\n",
        encoding="utf-8",
        newline="\n",
    )
    (ADDON / "Database" / "NPCs.lua").write_text(
        "BtWQuestsDatabase:AddNPCsTable({\n})\n",
        encoding="utf-8",
        newline="\n",
    )
    (ADDON / "Database" / "NPCs.ptBR.lua").write_text(
        "if GetLocale() ~= \"ptBR\" then\n    return\nend\n\nBtWQuestsDatabase:UpdateNPCsTable({\n})\n",
        encoding="utf-8",
        newline="\n",
    )
    (ADDON / "Database" / "Index.enUS.lua").write_text(
        "if GetLocale() ~= \"enUS\" then\n    return\nend\n\nBtWQuestsDatabase:AddSearchBuckets({})\n",
        encoding="utf-8",
        newline="\n",
    )
    (ADDON / "Database" / "Index.ptBR.lua").write_text(
        "if GetLocale() ~= \"ptBR\" then\n    return\nend\n\nBtWQuestsDatabase:AddSearchBuckets({})\n",
        encoding="utf-8",
        newline="\n",
    )


def _reset_locales():
    (ADDON / "Localization.lua").write_text(
        "local L = BtWQuests.L\n\nL[\"FOREVER\"] = \"Forever\"\n",
        encoding="utf-8",
        newline="\n",
    )
    (ADDON / "Localization.ptBR.lua").write_text(
        "local L = BtWQuests.L\n\nL[\"FOREVER\"] = \"Forever\"\n",
        encoding="utf-8",
        newline="\n",
    )


def _reset_tocs():
    for name in TOC_FILES:
        path = ADDON / name
        lines = path.read_text(encoding="utf-8").splitlines()
        body = [
            line for line in lines
            if line != "ElwynnForest.lua" and not (line.startswith("Zones/") and line.endswith(".lua"))
        ]
        path.write_text("\n".join(body) + "\n", encoding="utf-8", newline="\n")


def _reset_state():
    state = load()
    quests = len(state.get("quests") or {})
    npcs = len(state.get("npcs") or {})
    kept = {}
    for key, zone in (state.get("zones") or {}).items():
        fresh = {"status": "pending"}
        for field in KEEP_ZONE:
            if zone.get(field) is not None:
                fresh[field] = zone[field]
        kept[key] = fresh
    state["zones"] = kept
    state["quests"] = {}
    state["npcs"] = {}
    save(state)
    return quests, npcs, len(kept)
