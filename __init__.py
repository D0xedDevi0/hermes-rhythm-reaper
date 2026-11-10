"""rhythm-reaper - the hip-hop producer desk.

Registers five tools, the ``/reaper`` command and the bundled operations skill.

The desk knows 41 hip-hop lanes. For any of them it will hand back the full
production spec, build a complete pasteable Suno deliverable (style field, exclude
list, tagged lyric frame with bar targets, pronunciation lexicon, generation
notes), validate a draft against the real platform limits, and sweep text for
pronunciation hazards.

It does not write your bars on purpose - template lyrics are slop. It hands you a
frame that is already correct.
"""

from __future__ import annotations

import importlib.util
import json
import logging
import pathlib
import sys

logger = logging.getLogger(__name__)

_HERE = pathlib.Path(__file__).resolve().parent


def _load(name: str):
    """Load a sibling module by path (the dashed plugin dir is not importable)."""
    key = f"rhythm_reaper_{name}"
    cached = sys.modules.get(key)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(key, _HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


tools = _load("tools")
genres = _load("genres")

# No credential is involved anywhere in this plugin, so NO tool is gated and no
# handler can be hidden by a missing secret.
_TOOLS = (
    ("reaper_lanes", tools.REAPER_LANES_SCHEMA, tools.handle_reaper_lanes, "🎛️"),
    ("reaper_lane", tools.REAPER_LANE_SCHEMA, tools.handle_reaper_lane, "📋"),
    ("reaper_block", tools.REAPER_BLOCK_SCHEMA, tools.handle_reaper_block, "🎚️"),
    ("reaper_check", tools.REAPER_CHECK_SCHEMA, tools.handle_reaper_check, "🧪"),
    ("reaper_respell", tools.REAPER_RESPELL_SCHEMA, tools.handle_reaper_respell, "🗣️"),
)

_HELP = f"""🟦 /reaper lanes [query] — the {len(genres.LANES)} lanes, with tempo and vibe
🟦 /reaper spec <lane> — full production spec + section plan for one lane
🟦 /reaper block <lane> | <title> | <hook> — a complete pasteable deliverable
🟦 /reaper check — validate a draft against the 1000/3000-char limits

Families: {", ".join(genres.FAMILIES)}
Example: /reaper block ghetto-blues | Hood Up | I put my head down and I built"""


def _args(raw: str) -> list[str]:
    return [p.strip() for p in (raw or "").split("|")]


def _reaper_command(raw_args: str) -> str:
    """``/reaper <action> ...`` - the same operations as the tools, from chat."""
    parts = (raw_args or "").strip().split(None, 1)
    action = (parts[0] if parts else "help").lower()
    rest = parts[1].strip() if len(parts) > 1 else ""

    if action in ("lanes", "list", "styles"):
        data = json.loads(tools.handle_reaper_lanes({"query": rest, "limit": 30}))
        lines = [f"🟦 {data['count']} lanes (of {data['total_lanes']})"]
        for lane in data["lanes"]:
            lines.append(f"🟦 {lane['id']} — {lane['bpm']} BPM — {lane['vibe']}")
        return "\n".join(lines)

    if action in ("spec", "lane", "info"):
        if not rest:
            return "usage: /reaper spec <lane>"
        data = json.loads(tools.handle_reaper_lane({"lane": rest}))
        if data.get("error"):
            return f"failed — {data['error']}"
        plan = "\n".join(f"🟦 {s['section']} ({s['bars']} bars, energy {s['energy']}/10)"
                         for s in data["section_plan"])
        return "\n".join([
            f"{data['name']} — {data['bpm']} BPM — {data['keys'][0]}",
            f"🟦 drums: {data['drums']}",
            f"🟦 low end: {data['low_end']}",
            f"🟦 vocal: {data['vocal']}",
            f"🟦 exclude: {data['exclude_styles']}",
            "section plan:", plan,
        ])

    if action in ("block", "build"):
        args = _args(rest)
        if len(args) < 2:
            return "usage: /reaper block <lane> | <title> | <hook>"
        payload = {"lane": args[0], "title": args[1]}
        if len(args) > 2 and args[2]:
            payload["hook"] = args[2]
        data = json.loads(tools.handle_reaper_block(payload))
        if data.get("error"):
            return f"failed — {data['error']}"
        return data["pasteable"]

    if action == "check":
        return ("reaper_check needs multi-line input — call the tool with style + lyrics "
                "instead of using the command.")

    return _HELP


def register(ctx) -> None:
    """Register the producer tools, the /reaper command and the bundled skill."""
    for name, schema, handler, emoji in _TOOLS:
        ctx.register_tool(name=name, toolset="rhythm_reaper", schema=schema, handler=handler,
                          description=schema["description"], emoji=emoji)

    ctx.register_command("reaper", _reaper_command,
                         description="Hip-hop producer desk: lanes, specs, deliverables, validation",
                         args_hint="lanes [query]|spec <lane>|block <lane> | <title> | <hook>")

    # A plugin's skills/ dir is NOT auto-discovered - the host only learns about a
    # bundled skill through this call.
    skill = _HERE / "skills" / "rhythm-reaper-operations" / "SKILL.md"
    if skill.is_file():
        ctx.register_skill("rhythm-reaper-operations", skill,
                           description="Use when producing a hip-hop track: pick a lane, build a "
                                       "production-ready Suno deliverable, validate it before pasting.")
    else:
        logger.warning("rhythm-reaper bundled skill missing at %s", skill)

    logger.debug("rhythm-reaper registered %d tools + /reaper + skill (%d lanes)",
                 len(_TOOLS), len(genres.LANES))
