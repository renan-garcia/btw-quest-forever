import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import run
from lib import wowhead
from lib import lua_emit
from lib.chains import group_chains
from lib.class_place import _home, place_class_quests, rehome_foreign
from lib.series import series_groups
from lib.state_store import empty


SERIES = [93835, 94369, 93089, 94946, 94947, 93963]


def fixture():
    state = empty()
    state["zones"] = {
        "eastern-kingdoms/stormwind-city": {"continent": "eastern-kingdoms", "slug": "stormwind-city", "area_id": 1519},
        "eastern-kingdoms/alterac-mountains": {"continent": "eastern-kingdoms", "slug": "alterac-mountains", "area_id": 36},
        "eastern-kingdoms/redridge-mountains": {"continent": "eastern-kingdoms", "slug": "redridge-mountains", "area_id": 44},
        "eastern-kingdoms/elwynn-forest": {"continent": "eastern-kingdoms", "slug": "elwynn-forest", "area_id": 12},
    }
    for index, quest_id in enumerate(SERIES):
        state["quests"][str(quest_id)] = {
            "name_en": str(quest_id), "quest_zone_id": 16593 if index < 4 else 1519,
            "level": 12, "required_level": 7, "series_known": True,
            "series": SERIES, "side": 1, "start_areas": [36] if index == 4 else [1519],
        }
    return state


class SeriesPlacementTests(unittest.TestCase):
    def test_parser_reads_requested_quest_and_category(self):
        html = ('WH.Gatherer.addData(5, 16, {"1":{"_side":2},"93835":{"_side":1}});'
                '$.extend(g_quests[93835], {"name":"Confront Lorthuna","category":16593,"level":12,"reqlevel":7});')
        with patch.object(wowhead.http_cache, "get", return_value=html):
            page = wowhead.quest_page(93835)
        self.assertEqual((page["side"], page["category"], page["level"]), (1, 16593, 12))

    def test_unrelated_or_error_page_is_rejected(self):
        with patch.object(wowhead.http_cache, "get", return_value='WH.Gatherer.addData(5, 16, {"1":{}});'):
            with self.assertRaises(RuntimeError):
                wowhead.quest_page(93835)

    def test_series_keeps_members_outside_initial_list(self):
        groups, loose = series_groups(SERIES[-2:], fixture()["quests"])
        self.assertEqual(groups, [SERIES])
        self.assertEqual(loose, [])

    def test_shorter_version_is_not_a_second_chain(self):
        state = fixture()
        state["quests"]["94947"]["series"] = SERIES[:-1]
        self.assertEqual(series_groups(SERIES[-2:], state["quests"])[0], [SERIES])

    def test_faction_branches_remain_separate(self):
        quests = {"1": {"series": [1, 2, 3]}, "4": {"series": [1, 2, 4]}}
        self.assertEqual(series_groups([1, 4], quests)[0], [[1, 2, 3], [1, 2, 4]])

    def test_origin_category_precedes_later_npc_location(self):
        state = fixture()
        with patch("lib.class_place._zone_title", return_value="Ilha de Zefras"):
            self.assertEqual(_home(SERIES, state["quests"], state), "new/16593")
        self.assertNotIn("ui_map_id", state["zones"]["new/16593"])

    def test_missing_first_chapter_does_not_fall_back_to_alterac(self):
        state = fixture()
        del state["quests"]["93835"]
        self.assertIsNone(_home(SERIES, state["quests"], state))

    def test_multiple_start_areas_do_not_depend_on_npc_order(self):
        state = fixture()
        quest = {"name_en": "Elmore", "quest_zone_id": 1519, "series_known": True, "start_areas": [44, 12]}
        state["quests"]["1097"] = quest
        self.assertIsNone(_home([1097], state["quests"], state))
        quest["start_areas"].reverse()
        self.assertIsNone(_home([1097], state["quests"], state))

    def test_unique_start_area_can_place_a_capital_quest(self):
        state = fixture()
        state["quests"]["1"] = {"name_en": "Q", "quest_zone_id": 1519, "series_known": True, "start_areas": [12]}
        self.assertEqual(_home([1], state["quests"], state), "eastern-kingdoms/elwynn-forest")

    def test_full_chain_migration_removes_old_category_and_is_idempotent(self):
        state = fixture()
        old = state["zones"]["eastern-kingdoms/alterac-mountains"]
        old.update(category_id=16002, lua_file="Zones/AlteracMountains.lua", chains=[{
            "constant": "Old", "id": 160301, "quests": SERIES[-2:],
            "faction": "Alliance", "class_id": None, "complete_all": False,
            "from_class": "eastern-kingdoms/stormwind-city",
        }])
        source = dict(state["zones"]["eastern-kingdoms/stormwind-city"], quest_ids=SERIES[-2:])
        with patch("lib.class_place._zone_title", return_value="Ilha de Zefras"):
            place_class_quests(state, source)
        destination = state["zones"]["new/16593"]
        self.assertEqual(destination["chains"][0]["quests"], SERIES)
        self.assertEqual(destination["chains"][0]["id"], 160301)
        self.assertNotIn("category_id", old)
        self.assertIn("eastern-kingdoms/alterac-mountains", source["affected_zones"])
        saved_id = destination["chains"][0]["id"]
        source["quest_ids"] = SERIES[-2:]
        place_class_quests(state, source)
        self.assertEqual(len(destination["chains"]), 1)
        self.assertEqual(destination["chains"][0]["id"], saved_id)

    def test_native_zone_keeps_the_tail_in_the_same_chain(self):
        state = fixture()
        zone = {"continent": "new", "slug": "16593", "area_id": 16593,
                "new_region": True, "constant": "Zone16593", "quest_ids": SERIES}
        for quest in state["quests"].values():
            quest["chain_zone"] = "new/16593"
        self.assertEqual(group_chains(zone, state["quests"])[0]["quests"], SERIES)

    def test_second_source_does_not_duplicate_an_existing_series(self):
        state = fixture()
        source = dict(state["zones"]["eastern-kingdoms/stormwind-city"], quest_ids=SERIES[-2:])
        with patch("lib.class_place._zone_title", return_value="Ilha de Zefras"):
            place_class_quests(state, source)
        other = {"continent": "classes", "slug": "unknown", "quest_ids": SERIES}
        place_class_quests(state, other)
        self.assertEqual(len(state["zones"]["new/16593"]["chains"]), 1)
        self.assertTrue(all(state["quests"][str(item)]["zone"] == "new/16593" for item in SERIES))

    def test_incomplete_series_is_not_emitted_as_other_quests(self):
        state = fixture()
        del state["quests"]["93835"]
        zone = {"continent": "eastern-kingdoms", "slug": "alterac-mountains",
                "area_id": 36, "constant": "AlteracMountains", "quest_ids": SERIES[-2:]}
        self.assertEqual(group_chains(zone, state["quests"]), [])

    def test_expansion_fetches_missing_members_and_respects_limit(self):
        state = fixture()
        for quest_id in SERIES[:-2]:
            del state["quests"][str(quest_id)]
        zone = {"quest_ids": SERIES[-2:]}
        original = fixture()["quests"]

        def fetch(current, _zone, ids, _refresh):
            for quest_id in ids:
                current["quests"][str(quest_id)] = copy.deepcopy(original[str(quest_id)])

        with patch.object(run, "_fetch_pages", side_effect=fetch) as mocked:
            run._expand_series(state, zone, SERIES[-2:], limit=2)
            mocked.assert_not_called()
            run._expand_series(state, zone, SERIES[-2:])
            self.assertEqual(mocked.call_args.args[2], SERIES[:-2])
        self.assertTrue(all(str(item) in state["quests"] for item in SERIES))

    def test_refresh_also_updates_existing_chapters(self):
        state = fixture()
        with patch.object(run, "_fetch_pages") as mocked:
            run._expand_series(state, {"quest_ids": SERIES[-2:]}, SERIES[-2:], refresh=True)
        self.assertEqual(mocked.call_args.args[2], SERIES[:-2])
        self.assertTrue(mocked.call_args.args[3])

    def test_unknown_map_does_not_use_the_fetching_zone_map(self):
        state = fixture()
        page = {"reqclass": 0, "reqrace": 0, "side": 1, "series": SERIES,
                "starts": [{"area_id": 16593, "id": 55, "name": "NPC", "coord": [50, 50]}]}
        run._apply_page(state, {"ui_map_id": 1429}, 93835, page)
        self.assertFalse(state["npcs"]["55"].get("locations"))
        self.assertEqual(state["quests"]["93835"]["start_areas"], [16593])

    def test_multiple_starts_clear_the_previous_single_origin(self):
        state = fixture()
        state["quests"]["93835"]["start_area"] = 44
        page = {"reqclass": 0, "reqrace": 0, "side": 1, "series": SERIES,
                "starts": [{"area_id": area, "id": area, "name": "NPC", "coord": [50, 50]} for area in (44, 12)]}
        run._apply_page(state, {}, 93835, page)
        self.assertIsNone(state["quests"]["93835"]["start_area"])
        self.assertEqual(state["quests"]["93835"]["start_areas"], [12, 44])

    def test_returning_a_series_to_its_origin_removes_the_old_copy(self):
        state = fixture()
        source = state["zones"]["eastern-kingdoms/elwynn-forest"]
        source.update(quest_ids=SERIES, constant="ElwynnForest")
        destination = state["zones"]["eastern-kingdoms/alterac-mountains"]
        destination.update(category_id=16002, lua_file="Zones/AlteracMountains.lua", chains=[{
            "constant": "Old", "id": 160301, "quests": SERIES,
            "from_class": "eastern-kingdoms/elwynn-forest",
        }])
        for quest in state["quests"].values():
            quest["quest_zone_id"] = 12
        rehome_foreign(state, source)
        self.assertEqual(destination["chains"], [])
        self.assertEqual(source["quest_ids"], SERIES)
        self.assertIn("eastern-kingdoms/alterac-mountains", source["affected_zones"])

    def test_locked_zone_removes_blocks_of_moved_chains(self):
        text = ('-- class chains: classes/mage\nOLD_CALL\n-- end class chains: classes/mage\n'
                'Database:AddCategory(CATEGORY_ID, {\n    items = {\n'
                '        -- class item: classes/mage\nOLD_ITEM\n        -- end class item: classes/mage\n'
                '    },\n})\n')
        with patch.object(Path, "exists", return_value=True), patch.object(Path, "read_text", return_value=text), \
                patch.object(Path, "write_text") as written:
            lua_emit._write_one({"chains_locked": True, "lua_file": "Locked.lua", "chains": []})
            result = written.call_args.args[0]
        self.assertNotIn("OLD_CALL", result)
        self.assertNotIn("OLD_ITEM", result)
        self.assertIn("Database:AddCategory", result)

    def test_npc_without_known_map_is_still_registered(self):
        state = empty()
        state["npcs"]["55"] = {"name_en": "NPC"}
        with patch.object(lua_emit, "_write") as written:
            lua_emit.write_npcs(state)
            result = "\n".join(written.call_args_list[0].args[1])
        self.assertIn("[55]", result)
        self.assertTrue(state["npcs"]["55"]["in_addon"])


if __name__ == "__main__":
    unittest.main()
