"""rhythm-reaper - the studio.

Turns a lane + a concept into a complete, production-ready Suno deliverable, and
validates any draft against the platform's real limits.

What this module deliberately does NOT do: write your bars. Template-generated
lyrics are slop. The studio produces the full PRODUCTION FRAME - the style field
written out, the exclude list, the section plan with bar targets and metatags, the
hook placement, the respelled pronunciation lexicon, and the generation notes - so
the writer fills a frame that is already correct instead of guessing at one.

Limits enforced in code (not eyeballed):
  Style field  <= 1000 chars
  Lyrics field <= 3000 chars
"""

from __future__ import annotations

import re

STYLE_LIMIT = 1000
LYRICS_LIMIT = 3000

# Structural metatags Suno understands. Every section header must carry one.
STRUCTURAL_TAGS = {
    "intro", "verse", "pre-chorus", "chorus", "post-chorus", "hook", "bridge",
    "interlude", "instrumental", "guitar solo", "solo", "breakdown", "build-up",
    "build up", "drop", "outro", "end", "silence", "refrain", "ad-lib", "skit",
}

# Dynamic tags that contradict each other inside ONE section.
DYNAMIC_OPPOSITIONS = [
    ("high energy", "low energy"),
    ("explosive", "quiet arrangement"),
    ("aggressive", "intimate"),
    ("building energy", "falling tension"),
    ("dark atmosphere", "euphoric"),
    ("belted", "whispered"),
    ("slow down", "high energy"),
]

# Phonetic respellings: AI vocalists pronounce, they do not read. Left side is what
# appears in text, right side is what forces the sound. Curated from real slur
# reports on rendered takes - extend it when a new proper noun slurs.
RESPELL_TABLE = {
    "nous": "Noose",
    "sibyl": "Sih-bull",
    "helixa": "Heh-lick-suh",
    "bankr": "Bank-er",
    "mcintosh": "M C I N T O S H",
    "x402": "ex four oh two",
    "p2p": "P two P",
    "jpeg": "J-peg",
    "distro": "Dis-tro",
    "atropos": "At-roh-pos",
    "psyche": "Sy-kee",
    "teknium": "Tek-nee-um",
    "d0xeddev": "Doxed Dev",
    "d0xed": "Doxed",
    "devio": "Dev-ee-oh",
    "base'd": "Based",
    "zk": "Z K",
    "api": "A P I",
    "nft": "N F T",
    "ai": "A I",
    "gpu": "G P U",
    "usdc": "U S D C",
    "eth": "E T H",
}

_WORDISH = re.compile(r"[A-Za-z][A-Za-z0-9'\-]*")


def _digits_to_words(text: str) -> str:
    """Spell every digit run as words - Suno mispronounces bare numerals."""
    words = {"0": "oh", "1": "one", "2": "two", "3": "three", "4": "four",
             "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine"}

    def repl(match: "re.Match[str]") -> str:
        spelled = " ".join(words[d] for d in match.group(0))
        # "40B" must not become the single nonsense token "ohB".
        nxt = text[match.end():match.end() + 1]
        return spelled + (" " if nxt and nxt.isalpha() else "")

    return re.sub(r"\d+", repl, text)


def proper_noun_candidates(text: str) -> list[str]:
    """Tokens that are likely to slur: acronyms, digit-bearing, camel-case brands."""
    found: list[str] = []
    for token in _WORDISH.findall(text or ""):
        if token.lower() in RESPELL_TABLE:
            found.append(token)
            continue
        if re.search(r"\d", token):
            found.append(token)
            continue
        if len(token) >= 2 and token.isupper():
            found.append(token)
            continue
        # internal capital after the first letter: DisTrO, MCINTOSH, x402-style
        if re.search(r"[A-Z]", token[1:]):
            found.append(token)
    seen: set[str] = set()
    out = []
    for token in found:
        low = token.lower()
        if low not in seen:
            seen.add(low)
            out.append(token)
    return out


def respell(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Apply the respell table plus the digit rule.

    Returns ``(new_text, [(before, after), ...])`` so the caller can show exactly
    what changed rather than silently rewriting the writer's words.
    """
    applied: list[tuple[str, str]] = []
    out = text or ""
    for before, after in RESPELL_TABLE.items():
        pattern = re.compile(rf"\b{re.escape(before)}\b", re.IGNORECASE)
        if pattern.search(out):
            out = pattern.sub(after, out)
            applied.append((before, after))
    rewritten = _digits_to_words(out)
    if rewritten != out:
        for m in re.finditer(r"\d+", out):
            applied.append((m.group(0), _digits_to_words(m.group(0))))
        out = rewritten
    return out, applied


def fit(text: str, limit: int) -> tuple[str, bool]:
    """Clamp to *limit* by dropping whole trailing clauses, never mid-word."""
    text = (text or "").strip()
    if len(text) <= limit:
        return text, False
    parts = [p.strip() for p in text.split(",")]
    while parts and len(", ".join(parts)) > limit:
        parts.pop()
    trimmed = ", ".join(parts).rstrip(", ")
    if not trimmed:
        trimmed = text[:limit].rsplit(" ", 1)[0]
    return trimmed, True


def build_style(lane: dict, bpm=None, key: str | None = None,
                persona: str | None = None, extra: str | None = None) -> dict:
    """Assemble the Style field. The ARC is preserved; the tail gives way first."""
    core = lane["style"].rstrip(". ")
    arc = lane["arc"].rstrip(". ")
    head = f"{core}. {arc}."
    tail_bits = []
    if bpm:
        tail_bits.append(f"{bpm} BPM")
    if key:
        tail_bits.append(key)
    tail = ", ".join(tail_bits)
    if persona:
        tail = f"{tail}. {persona.strip().rstrip('.')}" if tail else persona.strip()
    if extra:
        tail = f"{tail}. {extra.strip().rstrip('.')}" if tail else extra.strip()

    full = f"{head} {tail}".strip()
    fitted, trimmed = fit(full, STYLE_LIMIT)
    if trimmed:
        # The tail is the first casualty - keep descriptor + arc intact.
        fitted, _ = fit(head, STYLE_LIMIT)
    return {
        "text": fitted,
        "chars": len(fitted),
        "limit": STYLE_LIMIT,
        "trimmed": trimmed,
        "ok": len(fitted) <= STYLE_LIMIT,
    }


# Per-family section plan: (section name, bars, energy out of 10)
STRUCTURES = {
    "foundational": [("Intro", 4, 3), ("Verse 1", 16, 6), ("Chorus", 8, 8),
                     ("Verse 2", 16, 6), ("Chorus", 8, 8), ("Bridge", 8, 6),
                     ("Chorus", 8, 9)],
    "trap": [("Intro", 4, 3), ("Verse 1", 16, 6), ("Hook", 8, 8),
             ("Verse 2", 16, 6), ("Hook", 8, 8), ("Verse 3", 12, 7),
             ("Hook", 8, 9)],
    "drill": [("Intro", 4, 4), ("Verse 1", 16, 7), ("Hook", 8, 8),
              ("Verse 2", 16, 7), ("Hook", 8, 8), ("Verse 3", 12, 8)],
    "melodic": [("Intro", 4, 3), ("Verse 1", 16, 5), ("Chorus", 8, 8),
                ("Verse 2", 16, 6), ("Chorus", 8, 8), ("Bridge", 8, 6),
                ("Chorus", 8, 10), ("Outro", 8, 3)],
    "alt": [("Intro", 8, 3), ("Verse 1", 16, 6), ("Chorus", 8, 7),
            ("Verse 2", 16, 6), ("Instrumental Break", 8, 5),
            ("Chorus", 8, 8), ("Outro", 8, 2)],
    "hard": [("Intro", 4, 5), ("Verse 1", 16, 8), ("Chorus", 8, 9),
             ("Verse 2", 16, 8), ("Chorus", 8, 9), ("Breakdown", 8, 10),
             ("Chorus", 8, 10)],
    "conscious": [("Intro", 4, 3), ("Verse 1", 16, 6), ("Hook", 8, 7),
                  ("Verse 2", 16, 6), ("Hook", 8, 7), ("Bridge", 8, 5),
                  ("Verse 3", 16, 7), ("Hook", 8, 9)],
}


def plan_sections(lane: dict) -> list[dict]:
    """The section plan for a lane, with tags, bar targets and energy."""
    plan = STRUCTURES.get(lane["family"], STRUCTURES["trap"])
    lane_tags = lane.get("tags") or []
    out = []
    for index, (name, bars, energy) in enumerate(plan):
        tag = f"[{name}]"
        extra = []
        if name.lower().startswith(("chorus", "hook")) and lane_tags:
            extra = lane_tags[:2]
        elif name.lower() == "breakdown" and lane_tags:
            extra = lane_tags[2:3]
        out.append({
            "section": name,
            "tag": tag,
            "bars": bars,
            "energy": energy,
            "metatags": [tag] + extra,
            "index": index,
        })
    return out


def build_lyrics_frame(lane: dict, hook: str | None = None,
                       concept: str | None = None) -> dict:
    """A tagged skeleton: section headers, metatags, bar slots and hook placement.

    Bar slots are ``____`` on purpose - a bracket annotation would be
    indistinguishable from a metatag.
    """
    plan = plan_sections(lane)
    hook_line = (hook or "____").strip()
    lines: list[str] = []
    for section in plan:
        lines.append(" ".join(section["metatags"]))
        if section["index"] == 0 and concept:
            # Inside the section body, never above the first tag - a bare line
            # before [Intro] would read as an untagged section to the validator.
            lines.append(f"({concept.strip()})")
        if section["section"].lower().startswith(("chorus", "hook")):
            lines.append(hook_line)
            lines.append("____")
        else:
            for _ in range(0, section["bars"], 4):
                lines.append("____")
        lines.append("")
    text = "\n".join(lines).strip()
    return {
        "text": text,
        "chars": len(text),
        "limit": LYRICS_LIMIT,
        "ok": len(text) <= LYRICS_LIMIT,
        "plan": plan,
    }


def build_block(lane: dict, title: str, hook: str | None = None,
                concept: str | None = None, bpm=None, key: str | None = None,
                persona: str | None = None) -> dict:
    """A complete, production-ready deliverable for one lane."""
    style = build_style(lane, bpm=bpm or lane["bpm"], key=key or lane["keys"][0],
                        persona=persona)
    frame = build_lyrics_frame(lane, hook=hook, concept=concept)
    lexicon = proper_noun_candidates(" ".join(x for x in (title, hook, concept) if x))
    respelled = []
    for token in lexicon:
        low = token.lower()
        if low in RESPELL_TABLE:
            respelled.append({"word": token, "say": RESPELL_TABLE[low]})
        elif re.search(r"\d", token):
            respelled.append({"word": token, "say": _digits_to_words(token)})
        elif token.isupper() and len(token) >= 2:
            respelled.append({"word": token, "say": " ".join(token)})
        else:
            respelled.append({"word": token, "say": f"respell to the SOUND (test in a 30s clip)"})
    return {
        "lane": {"id": lane["id"], "name": lane["name"], "family": lane["family"],
                 "bpm": lane["bpm"], "keys": lane["keys"], "vibe": lane["vibe"]},
        "title": title.strip(),
        "style": style,
        "exclude": lane["exclude"],
        "lyrics_frame": frame,
        "hook": (hook or "").strip(),
        "lexicon": respelled,
        "gen_notes": list(lane.get("notes") or []),
        "energy_map": [{"section": s["section"], "bars": s["bars"], "energy": s["energy"]}
                       for s in frame["plan"]],
    }


def check_style(text: str) -> dict:
    """Validate a Style field body."""
    text = (text or "").strip()
    issues = []
    if not text:
        issues.append("empty style field")
    if len(text) > STYLE_LIMIT:
        issues.append(f"style is {len(text)} chars, over the {STYLE_LIMIT} limit")
    if re.search(r"\b(style of|sounds like|in the style of)\b", text, re.I):
        issues.append("references another artist's style - describe the SOUND instead")
    if "feat" in text.lower():
        issues.append("contains 'feat' - remove artist references")
    return {"check": "style", "chars": len(text), "limit": STYLE_LIMIT,
            "ok": not issues, "issues": issues}


def check_lyrics(text: str) -> dict:
    """Validate a Lyrics field: limits, structural tags, contradictory dynamics."""
    text = text or ""
    issues = []
    if len(text) > LYRICS_LIMIT:
        issues.append(f"lyrics are {len(text)} chars, over the {LYRICS_LIMIT} limit")

    sections = [s for s in re.split(r"\n(?=\s*\[)", text.strip()) if s.strip()] if text.strip() else []
    if not sections:
        issues.append("no sections found - add structural tags like [Verse 1] [Chorus]")

    untagged = 0
    contradictions = []
    for section in sections:
        # Strip first: the split leaves the newline that preceded the tag, so a
        # raw split("\n")[0] would hand back an empty header and never match.
        header = section.strip().split("\n", 1)[0]
        tags = [t.strip().lower() for t in re.findall(r"\[([^\]]+)\]", header)]
        if not any(any(struct in tag for struct in STRUCTURAL_TAGS) for tag in tags):
            untagged += 1
        low = header.lower()
        for left, right in DYNAMIC_OPPOSITIONS:
            if left in low and right in low:
                contradictions.append(f"{left} + {right} in '{header.strip()}'")
    if untagged:
        issues.append(f"{untagged} section header(s) carry no recognised structural tag")

    counts: dict[str, int] = {}
    for name in re.findall(r"\[([^\]]+)\]", text):
        key = name.strip().lower()
        if any(struct in key for struct in ("verse", "chorus", "hook")):
            counts[key] = counts.get(key, 0) + 1
    if not any("chorus" in k or "hook" in k for k in counts):
        issues.append("no chorus/hook section - the song has no payoff")

    return {"check": "lyrics", "chars": len(text), "limit": LYRICS_LIMIT,
            "sections": len(sections), "untagged": untagged,
            "contradictions": contradictions,
            "ok": not issues, "issues": issues}


def check_block(title: str, style: str, lyrics: str, hook: str | None = None) -> dict:
    """Full deliverable validation. Returns overall ok + every sub-check."""
    style_result = check_style(style)
    lyrics_result = check_lyrics(lyrics)
    extra = []
    if not (title or "").strip():
        extra.append("no title")
    names = proper_noun_candidates(" ".join(x for x in (title, hook) if x))
    unswept = []
    for name in names:
        target = RESPELL_TABLE.get(name.lower())
        # Flag a known-to-slur noun that is still sitting un-respelled in the lyric.
        if target and re.search(rf"\b{re.escape(name)}\b", lyrics or ""):
            unswept.append(f"{name} -> {target}")
    if unswept:
        extra.append("known-to-slur proper nouns not respelled in the lyric: "
                     + ", ".join(sorted(set(unswept))))
    checks = [style_result, lyrics_result]
    ok = all(c["ok"] for c in checks) and not extra
    return {
        "ok": ok,
        "checks": checks,
        "issues": extra + [i for c in checks for i in c["issues"]],
        "style_chars": style_result["chars"],
        "lyrics_chars": lyrics_result["chars"],
    }
