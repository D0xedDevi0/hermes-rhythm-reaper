"""Offline tests for rhythm-reaper. No network, no credentials, no subprocesses."""

import importlib.util
import json
import pathlib
import sys
import unittest

_PLUGIN = pathlib.Path(__file__).resolve().parent.parent


def _load(name):
    key = f"rhythm_reaper_{name}"
    if key in sys.modules:
        return sys.modules[key]
    spec = importlib.util.spec_from_file_location(key, _PLUGIN / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


genres = _load("genres")
studio = _load("studio")
tools = _load("tools")

REQUIRED_LANE_KEYS = {
    "id", "name", "family", "bpm", "bpm_mid", "keys", "vibe", "drums", "low",
    "harmony", "sample", "vocal", "arc", "tags", "exclude", "style", "notes",
}


class TestCatalog(unittest.TestCase):
    def test_catalog_is_populated(self):
        self.assertGreaterEqual(len(genres.LANES), 40)

    def test_every_lane_has_every_key(self):
        for lane in genres.LANES:
            self.assertEqual(REQUIRED_LANE_KEYS - set(lane), set(),
                             f"{lane.get('id')} missing keys")

    def test_lane_ids_unique(self):
        ids = genres.ids()
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_family_has_lanes(self):
        counts = genres.families()
        for family in genres.FAMILIES:
            self.assertGreater(counts.get(family, 0), 0, f"{family} has no lanes")

    def test_style_and_arc_are_substantial(self):
        for lane in genres.LANES:
            self.assertGreater(len(lane["style"]), 150, lane["id"])
            self.assertGreater(len(lane["arc"]), 100, lane["id"])
            self.assertLessEqual(len(lane["style"]), studio.STYLE_LIMIT, lane["id"])

    def test_no_artist_references_in_style_fields(self):
        for lane in genres.LANES:
            low = lane["style"].lower()
            for bad in ("sounds like", "in the style of", " feat ", "ft."):
                self.assertNotIn(bad, low, f"{lane['id']} references an artist")

    def test_every_lane_has_exclude_and_tags(self):
        for lane in genres.LANES:
            self.assertTrue(lane["exclude"].strip(), lane["id"])
            self.assertGreaterEqual(len(lane["tags"]), 3, lane["id"])


class TestLookup(unittest.TestCase):
    def test_by_id_exact(self):
        self.assertEqual(genres.by_id("ghetto-blues")["family"], "melodic")

    def test_by_id_tolerates_case_and_spacing(self):
        for probe in ("BOOM BAP", "boom_bap", " boom-bap ", "Boom-Bap"):
            self.assertIsNotNone(genres.by_id(probe), probe)

    def test_by_id_unknown(self):
        self.assertIsNone(genres.by_id("polka-drill"))
        self.assertIsNone(genres.by_id(""))

    def test_search_by_production_vocabulary(self):
        hits = genres.search("sliding 808")
        self.assertTrue(hits)
        self.assertIn("uk-drill", [h["id"] for h in hits])

    def test_search_respects_limit(self):
        self.assertLessEqual(len(genres.search("", limit=3)), 3)


class TestRespell(unittest.TestCase):
    def test_table_hit(self):
        out, applied = studio.respell("DisTrO on Base")
        self.assertIn("Dis-tro", out)
        self.assertTrue(applied)

    def test_digits_are_spelled(self):
        out, _ = studio.respell("move 402 units")
        self.assertIn("four oh two", out)

    def test_digits_do_not_glue_to_letters(self):
        out, _ = studio.respell("40B params")
        self.assertIn("four oh B", out)
        self.assertNotIn("ohB", out)

    def test_acronym_candidate_detected(self):
        self.assertIn("JPEG", studio.proper_noun_candidates("the JPEG proof"))

    def test_camel_case_detected(self):
        self.assertIn("DisTrO", studio.proper_noun_candidates("a DisTrO run"))

    def test_plain_words_are_not_candidates(self):
        self.assertEqual(studio.proper_noun_candidates("i built it from the ground"), [])


class TestFit(unittest.TestCase):
    def test_under_limit_untouched(self):
        text, trimmed = studio.fit("short, sweet", 100)
        self.assertEqual(text, "short, sweet")
        self.assertFalse(trimmed)

    def test_over_limit_drops_whole_clauses(self):
        text = ", ".join(f"clause {i}" for i in range(200))
        out, trimmed = studio.fit(text, 100)
        self.assertTrue(trimmed)
        self.assertLessEqual(len(out), 100)
        self.assertFalse(out.endswith(","))

    def test_never_cuts_mid_word(self):
        out, _ = studio.fit("a" * 50 + ", " + "b" * 50, 60)
        self.assertTrue(out == "a" * 50 or set(out) == {"a", " ", ","})


class TestChecks(unittest.TestCase):
    def test_style_ok(self):
        self.assertTrue(studio.check_style("dusty boom bap drums")["ok"])

    def test_style_over_limit_fails(self):
        self.assertFalse(studio.check_style("x" * (studio.STYLE_LIMIT + 1))["ok"])

    def test_style_artist_reference_fails(self):
        result = studio.check_style("in the style of someone famous")
        self.assertFalse(result["ok"])

    def test_lyrics_missing_tags_fails(self):
        result = studio.check_lyrics("just some words with no tags at all")
        self.assertFalse(result["ok"])

    def test_lyrics_good_draft_passes(self):
        draft = ("[Intro]\n____\n\n[Verse 1]\n____\n\n[Chorus]\nhook line here\n\n"
                 "[Verse 2]\n____\n\n[Chorus]\nhook line here")
        self.assertTrue(studio.check_lyrics(draft)["ok"])

    def test_lyrics_untagged_section_detected(self):
        draft = "[Intro]\n____\n\n[Part A]\n____\n\n[Chorus]\nhook"
        result = studio.check_lyrics(draft)
        self.assertFalse(result["ok"])
        self.assertEqual(result["untagged"], 1)

    def test_contradictory_dynamics_detected(self):
        draft = "[Chorus] [High Energy] [Low Energy]\nhook"
        result = studio.check_lyrics(draft)
        self.assertTrue(result["contradictions"])

    def test_no_payoff_detected(self):
        draft = "[Intro]\n____\n\n[Verse 1]\n____"
        self.assertFalse(studio.check_lyrics(draft)["ok"])

    def test_lyrics_over_limit_fails(self):
        draft = "[Chorus]\n" + ("word " * 700)
        self.assertFalse(studio.check_lyrics(draft)["ok"])

    def test_block_flags_unrespelled_known_noun(self):
        result = studio.check_block("t", "ok style",
                                    "[Chorus]\nNous is here", hook="Nous is here")
        self.assertFalse(result["ok"])
        self.assertTrue(any("Nous" in i for i in result["issues"]))


class TestBlocks(unittest.TestCase):
    def test_every_lane_builds_a_valid_deliverable(self):
        for lane in genres.LANES:
            block = studio.build_block(lane, f"{lane['name']} Test",
                                       hook="put my head down and i built it",
                                       concept="coming up from nothing")
            self.assertLessEqual(block["style"]["chars"], studio.STYLE_LIMIT, lane["id"])
            self.assertLessEqual(block["lyrics_frame"]["chars"],
                                 studio.LYRICS_LIMIT, lane["id"])
            verdict = studio.check_block(block["title"], block["style"]["text"],
                                         block["lyrics_frame"]["text"], block["hook"])
            self.assertTrue(verdict["ok"], f"{lane['id']}: {verdict['issues']}")

    def test_frame_has_tagged_sections_and_hook(self):
        lane = genres.by_id("trap")
        block = studio.build_block(lane, "Test", hook="the hook line")
        text = block["lyrics_frame"]["text"]
        self.assertIn("[Verse 1]", text)
        self.assertIn("the hook line", text)

    def test_energy_map_covers_plan(self):
        lane = genres.by_id("trap-soul")
        block = studio.build_block(lane, "Test")
        self.assertEqual(len(block["energy_map"]),
                         len(studio.plan_sections(lane)))

    def test_family_name_as_lane_lists_that_family(self):
        raw = tools.handle_reaper_lane({"lane": "melodic"})
        data = json.loads(raw)
        self.assertIn("error", data)
        self.assertIn("trap-soul", data["error"])

    def test_pasteable_contains_all_four_suno_fields(self):
        lane = genres.by_id("ghetto-blues")
        out = tools.render_pasteable(studio.build_block(lane, "Hood Up",
                                                       hook="i built it"))
        for field in ("TITLE:", "STYLE:", "EXCLUDE:", "LYRICS:"):
            self.assertIn(field, out)


class TestHandlers(unittest.TestCase):
    def _call(self, handler, payload):
        raw = handler(payload)
        self.assertIsInstance(raw, str)
        return json.loads(raw)

    def test_lanes(self):
        data = self._call(tools.handle_reaper_lanes, {"limit": 5})
        self.assertEqual(len(data["lanes"]), 5)
        self.assertEqual(data["total_lanes"], len(genres.LANES))

    def test_lanes_bad_family(self):
        data = self._call(tools.handle_reaper_lanes, {"family": "polka"})
        self.assertIn("error", data)

    def test_lane(self):
        data = self._call(tools.handle_reaper_lane, {"lane": "uk-drill"})
        self.assertEqual(data["id"], "uk-drill")
        self.assertTrue(data["section_plan"])

    def test_lane_unknown_suggests(self):
        data = self._call(tools.handle_reaper_lane, {"lane": "drill"})
        self.assertIn("error", data)
        self.assertIn("uk-drill", data["error"])

    def test_lane_unknown_error(self):
        data = self._call(tools.handle_reaper_lane, {"lane": "zzz"})
        self.assertIn("error", data)

    def test_block_requires_title(self):
        data = self._call(tools.handle_reaper_block, {"lane": "trap"})
        self.assertIn("error", data)

    def test_block_end_to_end(self):
        data = self._call(tools.handle_reaper_block,
                          {"lane": "ghetto-blues", "title": "Hood Up",
                           "hook": "i put my head down and i built", "concept": "the climb"})
        self.assertTrue(data["validation"]["ok"])
        self.assertIn("STYLE:", data["pasteable"])

    def test_check_reports_ok(self):
        data = self._call(tools.handle_reaper_check,
                          {"title": "t", "style": "dark trap",
                           "lyrics": "[Chorus]\nhook line"})
        self.assertTrue(data["ok"])

    def test_respell_empty(self):
        self.assertIn("error", self._call(tools.handle_reaper_respell, {"text": "  "}))

    def test_respell_reports_changes(self):
        data = self._call(tools.handle_reaper_respell, {"text": "DisTrO and x402"})
        self.assertGreaterEqual(data["count"], 2)
        self.assertTrue(data["changes"])


class TestRegistration(unittest.TestCase):
    def test_register_wires_five_tools_command_and_skill(self):
        recorded = {"tools": [], "commands": [], "skills": []}

        class Ctx:
            def register_tool(self, **kw):
                recorded["tools"].append(kw["name"])

            def register_command(self, name, handler, **kw):
                recorded["commands"].append(name)

            def register_skill(self, name, path, **kw):
                recorded["skills"].append(name)

        init = _load("__init__")
        init.register(Ctx())
        self.assertEqual(sorted(recorded["tools"]),
                         sorted(["reaper_lanes", "reaper_lane", "reaper_block",
                                 "reaper_check", "reaper_respell"]))
        self.assertEqual(recorded["commands"], ["reaper"])
        self.assertEqual(recorded["skills"], ["rhythm-reaper-operations"])

    def test_declared_tools_match_manifest(self):
        manifest = (_PLUGIN / "plugin.yaml").read_text()
        for tool in ("reaper_lanes", "reaper_lane", "reaper_block",
                     "reaper_check", "reaper_respell"):
            self.assertIn(tool, manifest)

    def test_no_gated_tools(self):
        init = _load("__init__")
        for name, schema, handler, emoji in init._TOOLS:
            self.assertTrue(callable(handler), name)

    def test_command_help(self):
        init = _load("__init__")
        self.assertIn("/reaper lanes", init._reaper_command(""))

    def test_command_lanes(self):
        init = _load("__init__")
        self.assertIn("lanes", init._reaper_command("lanes"))

    def test_command_spec(self):
        init = _load("__init__")
        self.assertIn("sliding", init._reaper_command("spec uk-drill").lower())

    def test_command_block(self):
        init = _load("__init__")
        out = init._reaper_command("block trap | Test Title | the hook")
        self.assertIn("TITLE: Test Title", out)

    def test_command_usage_errors(self):
        init = _load("__init__")
        self.assertIn("usage", init._reaper_command("block trap"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
