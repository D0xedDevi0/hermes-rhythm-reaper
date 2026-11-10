"""rhythm-reaper - tool handlers and schemas.

Every handler returns a JSON string (the host serialises it into the tool result).
Nothing here needs a credential, so no tool is gated.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent


def _load(name: str):
    """Load a sibling by path. Cached under a namespaced key so __init__ and this
    module share one instance (the dashed plugin dir is not importable)."""
    key = f"rhythm_reaper_{name}"
    cached = sys.modules.get(key)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(key, _HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


genres = _load("genres")
studio = _load("studio")


def _dumps(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


# ------------------------------------------------------------------ schemas

REAPER_LANES_SCHEMA = {
    "name": "reaper_lanes",
    "description": ("List or search the hip-hop production lanes this producer desk knows - tempo family, "
                    "key centres and the vibe of each. Filters: family (foundational, trap, drill, melodic, "
                    "alt, hard, conscious) and a free-text query over names and production vocabulary."),
    "parameters": {"type": "object", "properties": {
        "query": {"type": "string", "description": "Free text: 'sliding 808', 'gospel', 'cowbell', 'uptempo'."},
        "family": {"type": "string", "description": "One of: foundational, trap, drill, melodic, alt, hard, conscious."},
        "limit": {"type": "integer", "description": "Max lanes to return (default 20)."},
    }},
}

REAPER_LANE_SCHEMA = {
    "name": "reaper_lane",
    "description": ("The full production spec for ONE lane: tempo family, key centres, drum programme, low end, "
                    "harmony and sample source, vocal delivery, the dynamic ARC, metatag vocabulary, what to "
                    "exclude, generation notes, and the section plan with bar targets and an energy map. "
                    "Read-only."),
    "parameters": {"type": "object", "properties": {
        "lane": {"type": "string", "description": "Lane id or name, e.g. 'ghetto-blues', 'uk-drill', 'boom bap'."},
    }, "required": ["lane"]},
}

REAPER_BLOCK_SCHEMA = {
    "name": "reaper_block",
    "description": ("Build a complete, production-ready Suno deliverable for a lane: the Style field written out "
                    "(with the dynamic ARC), the Exclude Styles line, a tagged lyric frame with bar targets and the "
                    "hook placed, a phonetic pronunciation lexicon for every proper noun, generation notes, and an "
                    "energy map. The studio writes the FRAME, not your bars - it never generates template lyrics. "
                    "Validated against the real 1000/3000-char platform limits."),
    "parameters": {"type": "object", "properties": {
        "lane": {"type": "string", "description": "Lane id or name (see reaper_lanes)."},
        "title": {"type": "string", "description": "Track title - usually the hook phrase."},
        "hook": {"type": "string", "description": "The chorus line people will remember."},
        "concept": {"type": "string", "description": "One line of subject/theme for the writer."},
        "bpm": {"type": "integer", "description": "Override the lane's default tempo."},
        "key": {"type": "string", "description": "Override the lane's default key, e.g. 'F minor'."},
        "persona": {"type": "string", "description": "Vocal persona sentence to append to the style field."},
    }, "required": ["lane", "title"]},
}

REAPER_CHECK_SCHEMA = {
    "name": "reaper_check",
    "description": ("Validate a draft before it goes into Suno: measures the Style field against the 1000-char limit "
                    "and the lyrics against 3000, confirms every section header carries a recognized structural tag, "
                    "catches contradictory dynamic tags sharing one section, confirms a chorus/hook exists, and flags "
                    "known-to-slur proper nouns left un-respelled. Pass the finished lyric, not the frame."),
    "parameters": {"type": "object", "properties": {
        "style": {"type": "string", "description": "The Style field body to measure."},
        "lyrics": {"type": "string", "description": "The full lyrics text including [metatags]."},
        "title": {"type": "string", "description": "Track title."},
        "hook": {"type": "string", "description": "The hook line, if it should be checked for respelling."},
    }, "required": ["lyrics"]},
}

REAPER_RESPELL_SCHEMA = {
    "name": "reaper_respell",
    "description": ("Sweep text for pronunciation hazards before it is baked into a render. Returns every candidate "
                    "proper noun (acronyms, digit-bearing tokens, camel-case brand names, known crypto names) with a "
                    "phonetic respelling. Pronunciation is fixed in the LYRICS - once generated it cannot be changed, "
                    "so sweep the finished lyric, not just the title word."),
    "parameters": {"type": "object", "properties": {
        "text": {"type": "string", "description": "The text to sweep (a lyric, a title, a concept line)."},
    }, "required": ["text"]},
}


# ----------------------------------------------------------------- handlers

def _lane_or_error(lane_id: str) -> tuple[dict | None, str]:
    lane = genres.by_id(lane_id)
    if lane:
        return lane, ""
    near = genres.search(lane_id or "", limit=5)
    names = ", ".join(f"{l['id']} ({l['name']})" for l in near) or "none"
    return None, f"unknown lane '{lane_id}'. Closest: {names}"


def handle_reaper_lanes(args: dict | None = None, **kwargs) -> str:
    args = args or {}
    family = (args.get("family") or "").strip().lower()
    query = (args.get("query") or "").strip()
    try:
        limit = int(args.get("limit") or 20)
    except (TypeError, ValueError):
        limit = 20
    limit = max(1, min(limit, 40))

    if family and family not in genres.FAMILIES:
        return _dumps({"error": f"unknown family '{family}'",
                       "families": genres.FAMILIES})
    pool = [l for l in genres.LANES if not family or l["family"] == family]
    if query:
        hits = {l["id"] for l in genres.search(query, limit=40)}
        pool = [l for l in pool if l["id"] in hits]
    return _dumps({
        "count": len(pool),
        "total_lanes": len(genres.LANES),
        "families": genres.families(),
        "lanes": [{"id": l["id"], "name": l["name"], "family": l["family"],
                   "bpm": l["bpm"], "keys": l["keys"], "vibe": l["vibe"]}
                  for l in pool[:limit]],
    })


def handle_reaper_lane(args: dict | None = None, **kwargs) -> str:
    args = args or {}
    lane, error = _lane_or_error(args.get("lane") or "")
    if not lane:
        return _dumps({"error": error})
    plan = studio.plan_sections(lane)
    return _dumps({
        "id": lane["id"], "name": lane["name"], "family": lane["family"],
        "bpm": lane["bpm"], "keys": lane["keys"], "vibe": lane["vibe"],
        "drums": lane["drums"], "low_end": lane["low"], "harmony": lane["harmony"],
        "sample_source": lane["sample"], "vocal": lane["vocal"],
        "arc": lane["arc"], "metatags": lane["tags"],
        "exclude_styles": lane["exclude"], "style_field": lane["style"],
        "gen_notes": lane["notes"],
        "section_plan": [{"section": s["section"], "bars": s["bars"],
                          "energy": s["energy"], "metatags": s["metatags"]} for s in plan],
    })


def render_pasteable(block: dict) -> str:
    """The deliverable in the order it gets pasted into Suno."""
    lines = [
        f"TITLE: {block['title']}",
        "",
        "STYLE:",
        block["style"]["text"],
        "",
        f"EXCLUDE: {block['exclude']}",
        "",
        "LYRICS:",
        block["lyrics_frame"]["text"],
        "",
        "GEN NOTES:",
    ]
    lines += [f"  - {note}" for note in block["gen_notes"]]
    if block["lexicon"]:
        lines += ["", "PRONUNCIATION SWEEP:"]
        lines += [f"  - {item['word']} -> {item['say']}" for item in block["lexicon"]]
    return "\n".join(lines)


def handle_reaper_block(args: dict | None = None, **kwargs) -> str:
    args = args or {}
    lane, error = _lane_or_error(args.get("lane") or "")
    if not lane:
        return _dumps({"error": error})
    title = (args.get("title") or "").strip()
    if not title:
        return _dumps({"error": "title is required - usually the hook phrase"})

    block = studio.build_block(
        lane, title,
        hook=args.get("hook"), concept=args.get("concept"),
        bpm=args.get("bpm"), key=args.get("key"), persona=args.get("persona"),
    )
    validation = studio.check_block(block["title"], block["style"]["text"],
                                   block["lyrics_frame"]["text"], block["hook"])
    return _dumps({
        "lane": block["lane"],
        "title": block["title"],
        "style": block["style"],
        "exclude": block["exclude"],
        "lyrics_frame": block["lyrics_frame"],
        "energy_map": block["energy_map"],
        "lexicon": block["lexicon"],
        "gen_notes": block["gen_notes"],
        "validation": validation,
        "pasteable": render_pasteable(block),
        "reminder": ("The frame is ready; the bars are yours. Write into the bar slots, "
                     "then run reaper_check on the finished lyric before pasting."),
    })


def handle_reaper_check(args: dict | None = None, **kwargs) -> str:
    args = args or {}
    result = studio.check_block(
        args.get("title") or "",
        args.get("style") or "",
        args.get("lyrics") or "",
        args.get("hook"),
    )
    result["reminder"] = ("Pronunciation is baked in at generation - sweep proper nouns BEFORE the render, "
                          "and test unusual ones in a 30s clip first.")
    return _dumps(result)


def handle_reaper_respell(args: dict | None = None, **kwargs) -> str:
    args = args or {}
    text = args.get("text") or ""
    if not text.strip():
        return _dumps({"error": "nothing to sweep"})
    candidates = studio.proper_noun_candidates(text)
    rewritten, applied = studio.respell(text)
    table = []
    for token in candidates:
        low = token.lower()
        if low in studio.RESPELL_TABLE:
            say = studio.RESPELL_TABLE[low]
        elif any(ch.isdigit() for ch in token):
            say = studio._digits_to_words(token)
        elif token.isupper() and len(token) >= 2:
            say = " ".join(token)
        else:
            say = "respell to the SOUND, then test in a 30s clip"
        table.append({"word": token, "say": say})
    return _dumps({
        "candidates": table,
        "count": len(table),
        "rewritten": rewritten,
        "changes": [{"from": b, "to": a} for b, a in applied],
        "note": ("Caps and hyphens fix most slurs. When a caps fix fails on a word the rhyme depends on, "
                 "stop respelling and rewrite the bar."),
    })


__all__ = [
    "REAPER_LANES_SCHEMA", "REAPER_LANE_SCHEMA", "REAPER_BLOCK_SCHEMA",
    "REAPER_CHECK_SCHEMA", "REAPER_RESPELL_SCHEMA",
    "handle_reaper_lanes", "handle_reaper_lane", "handle_reaper_block",
    "handle_reaper_check", "handle_reaper_respell", "render_pasteable",
]
