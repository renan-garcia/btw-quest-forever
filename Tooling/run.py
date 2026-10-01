"""Atualiza os dados do BtWQuests Forever.

Exemplos, na pasta Tooling:

  python run.py status
  python run.py list
  python run.py list pendente
  python run.py zones
  python run.py scan
  python run.py fetch eastern-kingdoms/westfall
  python run.py build eastern-kingdoms/westfall
  python run.py update eastern-kingdoms/westfall
  python run.py update eastern-kingdoms/westfall --dry-run
  python run.py seed eastern-kingdoms/westfall
  python run.py seed classes/paladin --delay=15
  python run.py seed eastern-kingdoms/westfall --refresh
  python run.py reset

O cache fica em AddOns/Tooling/cache. --refresh ignora o cache e baixa de novo,
antes ou depois do comando. O addon lido e gravado é AddOns/BtWQuestsForever.
"""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import foreverdb, http_cache, warcraftdb, wowhead
from lib.chains import allocate_ids, group_chains
from lib.class_place import place_class_quests, rehome_foreign
from lib.leveling import is_leveling_zone, retire_off_grid
from lib.lua_emit import emit
from lib.scan_addon import scan
from lib.state_store import load, quest_gaps, refresh_summary, restrictions_for, save
from lib.uimap import UI_MAP_BY_AREA
from lib.series import missing_members, series_groups


def _add_delay(parser):
    parser.add_argument("--delay", type=float, default=0, help="Segundos entre downloads novos do Wowhead. 0 não espera.")


def _add_refresh(parser):
    parser.add_argument("--refresh", action="store_true", dest="refresh_after", help="Ignora o cache e baixa de novo.")


def _refresh_requested(args):
    return bool(args.refresh or getattr(args, "refresh_after", False))


def main(argv):
    parser = argparse.ArgumentParser(description="Ferramentas de dados do BtWQuests Forever.")
    parser.add_argument("--refresh", action="store_true", help="Ignora o cache e baixa de novo.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Mostra o que já entrou e o que falta.")
    listed = sub.add_parser("list", help="Lista as zonas e o slug para o update.")
    listed.add_argument("status", nargs="?", choices=["pending", "partial", "done", "pendente", "parcial", "pronta"])
    zones = sub.add_parser("zones", help="Atualiza a lista de zonas.")
    _add_delay(zones)
    _add_refresh(zones)
    sub.add_parser("scan", help="Relê o addon e atualiza o estado.")

    fetch = sub.add_parser("fetch", help="Baixa uma zona para o estado, sem gravar o Lua.")
    fetch.add_argument("zone")
    fetch.add_argument("--limit", type=int, default=0, help="Limita quantas páginas de missão baixar.")
    _add_delay(fetch)
    _add_refresh(fetch)

    build = sub.add_parser("build", help="Grava o Lua a partir do estado.")
    build.add_argument("zone", nargs="?")

    update = sub.add_parser("update", help="Baixa uma zona e grava o Lua.")
    update.add_argument("zone")
    update.add_argument("--limit", type=int, default=0)
    update.add_argument("--dry-run", action="store_true")
    _add_delay(update)
    _add_refresh(update)

    seed = sub.add_parser("seed", help="Faz fetch, update e build de uma zona.")
    seed.add_argument("zone")
    seed.add_argument("--limit", type=int, default=0, help="Limita quantas páginas de missão baixar.")
    _add_delay(seed)
    _add_refresh(seed)

    sub.add_parser("reset", help="Apaga as zonas geradas e zera o progresso do addon.")

    args = parser.parse_args(argv)
    delay = getattr(args, "delay", 0) or 0
    if delay < 0:
        raise SystemExit("--delay precisa ser zero ou mais.")
    if delay:
        print(f"Wowhead: {delay:g}s entre downloads novos.")
    http_cache.set_delay(delay)
    refresh = _refresh_requested(args)
    if args.command == "status":
        command_status()
    elif args.command == "list":
        command_list(args.status)
    elif args.command == "zones":
        command_zones(refresh)
    elif args.command == "scan":
        command_scan()
    elif args.command == "fetch":
        command_fetch(args.zone, refresh, args.limit, write=False)
    elif args.command == "build":
        command_build(args.zone)
    elif args.command == "update":
        command_fetch(args.zone, refresh, args.limit, write=not args.dry_run)
    elif args.command == "seed":
        command_seed(args.zone, refresh, args.limit)
    elif args.command == "reset":
        command_reset()
    return 0


def command_reset():
    from lib.reset_addon import reset_addon

    summary = reset_addon()
    print(f"Arquivos de zona apagados: {summary['zone_files']}")
    print(f"Missões removidas do estado: {summary['quests']}")
    print(f"NPCs removidos do estado: {summary['npcs']}")
    print(f"Zonas no catálogo, todas pendentes: {summary['zones']}")
    print("O cache de download foi mantido. Use /reload no jogo.")


def command_status():
    state = load()
    summary = refresh_summary(state)
    print(f"Zonas: {summary['zones_done']} prontas, {summary['zones_partial']} parciais, {summary['zones_pending']} pendentes, {summary['zones_total']} no total")
    print(f"Missões no estado: {summary['quests']}")
    print(f"Sem origem: {len(summary['quests_missing_source'])} {summary['quests_missing_source']}")
    print(f"Sem nome ptBR: {len(summary['quests_missing_pt'])} {summary['quests_missing_pt']}")
    print(f"Sem série conhecida: {len(summary['quests_missing_series'])}")
    print(f"NPCs: {summary['npcs']}, com lacuna: {len(summary['npcs_with_gaps'])}")
    partial = [key for key, zone in sorted(state["zones"].items()) if zone.get("status") == "partial"]
    if partial:
        print("Parciais: " + ", ".join(partial))


def command_list(status_filter):
    labels = {"pending": "pendente", "partial": "parcial", "done": "pronta"}
    aliases = {"pendente": "pending", "parcial": "partial", "pronta": "done"}
    wanted = aliases.get(status_filter, status_filter)
    state = load()
    refresh_summary(state)
    zones = sorted(
        state["zones"].items(),
        key=lambda item: (item[1].get("continent") or "", item[1].get("name_en") or item[0]),
    )
    continent = None
    shown = 0
    for key, zone in zones:
        status = zone.get("status") or "pending"
        if wanted and status != wanted:
            continue
        if zone.get("continent") != continent:
            continent = zone.get("continent")
            print()
            print(continent or "outros")
        name = zone.get("name_en") or zone.get("slug") or key
        print(f"  {labels.get(status, status):<8} {key}  {name}")
        shown += 1
    print()
    print(f"{shown} zonas. Rode .\\atualizar.ps1 seed <slug>")


def command_scan():
    state = scan(load())
    save(state)
    command_status()


def command_zones(refresh):
    state = scan(load())
    _add_zones(state, refresh)
    save(state)
    print(f"Zonas no estado: {len(state['zones'])}")


def _add_zones(state, refresh):
    names = {}
    try:
        names = warcraftdb.zone_names(refresh=refresh)
    except Exception as error:
        print(f"WarcraftDB não respondeu os nomes ({error}). Sigo com o Wowhead.")
    for leaf in wowhead.zone_tree(refresh=refresh):
        zone = state["zones"].get(leaf["key"], {})
        zone.setdefault("continent", leaf["continent"])
        zone.setdefault("slug", leaf["slug"])
        zone["area_id"] = leaf["area_id"]
        zone.setdefault("name_en", names.get(leaf["area_id"]) or leaf["slug"])
        zone.setdefault("status", "pending")
        state["zones"][leaf["key"]] = zone


def command_fetch(zone_key, refresh, limit, write):
    state = scan(load())
    if zone_key not in state["zones"]:
        _add_zones(state, refresh)
    if zone_key not in state["zones"]:
        raise SystemExit(f"Zona desconhecida: {zone_key}. Rode zones e use continente/slug.")
    _fetch_zone(state, zone_key, refresh, limit)
    save(state)
    if write:
        placed = list(state["zones"][zone_key].get("affected_zones") or state["zones"][zone_key].get("placed_into") or [])
        if zone_key not in placed:
            placed.insert(0, zone_key)
        emit(state, placed)
        save(state)
        print(f"Lua gravado para {zone_key}")
    command_status()


def command_seed(zone_key, refresh, limit):
    print(f"== fetch {zone_key}")
    command_fetch(zone_key, refresh, limit, write=False)
    print(f"== update {zone_key}")
    command_fetch(zone_key, False, limit, write=True)
    print(f"== build {zone_key}")
    command_build(zone_key)


def command_build(zone_key):
    state = load()
    if zone_key and zone_key not in state["zones"]:
        raise SystemExit(f"Zona desconhecida: {zone_key}")
    retire_off_grid(state)
    save(state)
    placed = state["zones"][zone_key].get("affected_zones") if zone_key else None
    emit(state, list(dict.fromkeys([zone_key] + placed)) if placed else zone_key)
    save(state)
    print("Lua gravado.")


def _translated(name):
    if not name:
        return None
    text = name.strip()
    if text.startswith("[") and text.endswith("]"):
        return None
    return text


def _fetch_zone(state, zone_key, refresh, limit):
    zone = state["zones"][zone_key]
    if not zone.get("ui_map_id"):
        zone["ui_map_id"] = UI_MAP_BY_AREA.get(zone.get("area_id"))
    continent, slug = zone_key.split("/", 1)
    rows, truncated, name_en = wowhead.zone_quest_rows(continent, slug, "en", refresh=refresh)
    pt_names = {}
    name_pt = None
    try:
        pt_rows, _, name_pt = wowhead.zone_quest_rows(continent, slug, "pt", refresh=refresh)
        pt_names = {int(row["id"]): row.get("name") for row in pt_rows}
    except Exception as error:
        print(f"Lista ptBR falhou ({error}).")
    if name_en:
        zone["name_en"] = name_en
    if name_pt:
        zone["name_pt"] = name_pt
    zone["list_truncated"] = truncated
    if truncated:
        print(f"A lista de {zone_key} veio cortada em 1000. Nada dessa zona foi fechado.")
        return

    quest_ids = []
    for row in rows:
        quest_id = int(row["id"])
        quest_ids.append(quest_id)
        quest = state["quests"].setdefault(str(quest_id), {})
        quest.update({
            "zone": zone_key,
            "name_en": row.get("name") or quest.get("name_en"),
            "name_pt": _translated(pt_names.get(quest_id)) or _translated(quest.get("name_pt")),
            "level": row.get("level"),
            "required_level": row.get("reqlevel"),
            "side": row.get("side"),
            "in_addon": quest.get("in_addon", False),
        })
        category = row.get("category")
        if category:
            quest["quest_zone_id"] = int(category)
    zone["quest_ids"] = quest_ids
    if is_leveling_zone(zone):
        zone.setdefault("constant", _constant_name(slug))
        zone.setdefault("locale_key", _locale_key(zone["constant"]))
        zone.setdefault("lua_file", f"Zones/{zone['constant']}.lua")

    had_map = zone.get("ui_map_id")
    targets = quest_ids if not limit else quest_ids[:limit]
    _fetch_pages(state, zone, targets, refresh)
    _expand_series(state, zone, targets, refresh, limit=limit)
    _support(state, zone, refresh)
    if zone.get("ui_map_id") and not had_map:
        _fetch_pages(state, zone, targets, refresh)
    _fill_pt_npcs(state, zone.get("quest_ids") or [], refresh)
    _refresh_chain_names(zone, state["quests"])
    if is_leveling_zone(zone) and not zone.get("chains_locked"):
        rehome_foreign(state, zone)
    if not is_leveling_zone(zone):
        place_class_quests(state, zone)
        return
    if not zone.get("chains_locked"):
        zone["chains"] = group_chains(zone, state["quests"])
        allocate_ids(state, zone)


def _fetch_pages(state, zone, quest_ids, refresh):
    for quest_id in quest_ids:
        state["quests"].setdefault(str(quest_id), {"in_addon": False})
    def load(quest_id):
        try:
            return quest_id, wowhead.quest_page(quest_id, refresh=refresh), None
        except Exception as error:
            return quest_id, None, error

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(load, quest_id) for quest_id in quest_ids]
        for future in as_completed(futures):
            quest_id, page, error = future.result()
            if error is not None:
                state["quests"][str(quest_id)]["fetch_error"] = str(error)
                print(f"Missão {quest_id} falhou ({error}).")
                continue
            _apply_page(state, zone, quest_id, page)


def _expand_series(state, zone, seed_ids, refresh=False, limit=0):
    """Baixa os capítulos referenciados, inclusive os que estão em outras zonas."""
    known = list(dict.fromkeys(seed_ids))
    attempted = set(seed_ids)
    downloaded = len(seed_ids)
    while True:
        grouped, _ = series_groups(known, state["quests"])
        members = list(dict.fromkeys(known + [item for series in grouped for item in series]))
        if len(members) > 1000:
            raise RuntimeError("Expansão de séries excedeu 1000 missões; confira os dados antes de gravar.")
        for quest_id in members:
            state["quests"].setdefault(str(quest_id), {"in_addon": False})
        needed = members if refresh else missing_members(members, state["quests"])
        pending = [item for item in needed if item not in attempted]
        if limit:
            pending = pending[:max(0, limit - downloaded)]
        known = members
        if not pending:
            break
        attempted.update(pending)
        downloaded += len(pending)
        print(f"Séries: buscando {len(pending)} capítulos fora da lista inicial.")
        _fetch_pages(state, zone, pending, refresh)
    zone["quest_ids"] = list(dict.fromkeys((zone.get("quest_ids") or []) + known))
    missing = missing_members(known, state["quests"])
    if missing:
        print(f"Séries incompletas, classificação pendente: {missing}")
    return known


def _apply_page(state, zone, quest_id, page):
    quest = state["quests"][str(quest_id)]
    quest.pop("fetch_error", None)
    name = _translated(page.get("name"))
    if name:
        quest["name_en"] = name
    for field, source in (("quest_zone_id", "category"), ("level", "level"), ("required_level", "required_level")):
        if page.get(source) is not None:
            quest[field] = page[source]
    quest["reqclass"] = page["reqclass"]
    quest["reqrace"] = page["reqrace"]
    if page["side"] is not None:
        quest["side"] = page["side"]
    quest["series"] = page["series"]
    quest["series_known"] = True
    quest["restrictions"] = restrictions_for(quest.get("side"), quest.get("reqclass") or 0, quest.get("reqrace") or 0)
    starts = page["starts"]
    quest["start_areas"] = sorted({item["area_id"] for item in starts if item.get("area_id")})
    quest["start_area"] = quest["start_areas"][0] if len(quest["start_areas"]) == 1 else None
    if not starts:
        return
    start = next((item for item in starts if item.get("area_id") == quest.get("quest_zone_id") and _coord_pair(item.get("coord"))),
                 next((item for item in starts if _coord_pair(item.get("coord"))), starts[0]))
    npc_id = int(start["id"])
    quest["source"] = {"type": "npc", "id": npc_id}
    npc = state["npcs"].setdefault(str(npc_id), {})
    npc["name_en"] = start.get("name") or npc.get("name_en")
    npc.setdefault("in_addon", False)
    pair = _coord_pair(start.get("coord"))
    map_id = UI_MAP_BY_AREA.get(start.get("area_id"))
    if pair and map_id:
        x, y = pair
        npc.setdefault("locations", {}).setdefault(str(map_id), [{"x": round(x / 100, 4), "y": round(y / 100, 4)}])


def _coord_pair(coord):
    if not isinstance(coord, (list, tuple)) or len(coord) < 2:
        return None
    try:
        return float(coord[0]), float(coord[1])
    except (TypeError, ValueError):
        return None


def _support(state, zone, refresh):
    area_id = zone.get("area_id")
    if area_id:
        try:
            rows, _ = warcraftdb.quests_for_area(area_id, refresh=refresh)
            known = {int(row["record_id"]) for row in rows}
            zone["warcraftdb_ids"] = sorted(known)
        except Exception as error:
            print(f"WarcraftDB falhou ({error}).")
    try:
        guide = foreverdb.zone_guide(zone["slug"], refresh=refresh)
    except Exception as error:
        print(f"ForeverDB falhou ({error}).")
        return
    zone["foreverdb_classic_note"] = guide["classic_note"]
    for quest_id in zone.get("quest_ids") or []:
        quest = state["quests"][str(quest_id)]
        if "origem" not in quest_gaps(quest):
            continue
        url = guide["quests"].get(quest_id)
        if not url:
            continue
        try:
            pin = foreverdb.quest_pin(url, refresh=refresh)
        except Exception:
            continue
        quest.setdefault("support", {})["foreverdb"] = pin
        if zone.get("ui_map_id") is None and pin["pins"]:
            zone["ui_map_id"] = pin["pins"][0]["map"]
        if pin["pins"] and not quest.get("source"):
            first = pin["pins"][0]
            quest["source"] = {
                "type": "coords",
                "mapID": first["map"],
                "x": first["x"],
                "y": first["y"],
                "name": first["name"],
            }


def _fill_pt_npcs(state, quest_ids, refresh):
    pending = []
    for quest_id in quest_ids:
        quest = state["quests"].get(str(quest_id)) or {}
        source = quest.get("source") or {}
        npc_id = source.get("id")
        npc = state["npcs"].get(str(npc_id))
        if _translated(quest.get("name_pt")) and (not npc_id or (npc and _translated(npc.get("name_pt")))):
            continue
        pending.append((quest_id, npc_id))

    def load(item):
        quest_id, npc_id = item
        try:
            return quest_id, npc_id, wowhead.quest_page(quest_id, refresh=refresh, locale="pt"), None
        except Exception as error:
            return quest_id, npc_id, None, error

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(load, item) for item in pending]
        for future in as_completed(futures):
            quest_id, npc_id, page, error = future.result()
            if error is not None:
                print(f"Nome ptBR do NPC da missão {quest_id} falhou ({error}).")
                continue
            name_pt = _translated(page.get("name"))
            if name_pt:
                state["quests"][str(quest_id)]["name_pt"] = name_pt
            starts = page["starts"]
            matching = next((item for item in starts if int(item.get("id") or 0) == npc_id), None)
            if not matching:
                continue
            name = _translated(matching.get("name"))
            if not name:
                continue
            npc = state["npcs"].setdefault(str(npc_id), {})
            npc["name_pt"] = name


def _refresh_chain_names(zone, quests):
    for chain in zone.get("chains") or []:
        if not chain.get("quests"):
            continue
        first = quests.get(str(chain["quests"][0])) or {}
        if not _translated(chain.get("name_pt")):
            chain["name_pt"] = _translated(first.get("name_pt")) or first.get("name_en") or chain.get("name_pt")
        if not chain.get("name_en"):
            chain["name_en"] = first.get("name_en")


def _constant_name(slug):
    parts = [part for part in slug.replace("-", " ").split() if part]
    return "".join(part[:1].upper() + part[1:] for part in parts)


def _locale_key(constant):
    import re
    return re.sub(r"(?<!^)([A-Z])", r"_\1", constant).upper()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
