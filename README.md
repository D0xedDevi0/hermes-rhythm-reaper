# The Rhythm Reaper

A hip-hop producer desk inside Hermes. **41 lanes across seven families**, and for
any of them a complete production frame you can paste straight into Suno.

It knows the difference between the drum programme of boom bap and the sliding 808
of drill. It writes the style field, the exclude line, the section plan with bar
targets, the energy map and the pronunciation lexicon. **It does not write your
bars** — template lyrics are slop and you can hear it in the first four. It hands
you a frame that is already correct.

## Install

```bash
hermes plugins enable rhythm-reaper
```

No credentials, no network, no subprocesses. Pure local computation.

## The lanes

🟦 **foundational** (10) — boom bap, jazz rap, G-funk, old-school electro, Miami bass, New Orleans bounce, hyphy, crunk, snap, chopped and screwed
🟦 **trap** (8) — trap, southern/Memphis trap, dark trap, plugg/pluggnb, rage, hyperpop rap, afro-trap, Latin trap
🟦 **drill** (4) — UK drill, New York drill, sample drill, Detroit/Flint
🟦 **melodic** (4) — ghetto blues (soul-trap/pain music), trap soul, emo rap, cloud rap
🟦 **alt** (6) — lo-fi hip hop, beat tape/instrumental, trip hop, abstract/alternative, nerdcore, country rap
🟦 **hard** (7) — horrorcore, Memphis horrorcore, trap metal/scream rap, phonk, drift phonk, grime, chopper/speed rap
🟦 **conscious** (2) — conscious/political, boom bap revival

Every lane carries: tempo family, key centres, drum programme, low end, harmony and
sample source, vocal delivery, **the dynamic ARC**, metatag vocabulary, what to
exclude, and generation notes.

## Tools

🟦 `reaper_lanes` — list or search the lanes by family or production vocabulary
🟦 `reaper_lane` — the full production spec plus the section plan and energy map
🟦 `reaper_block` — build a complete, validated, pasteable deliverable
🟦 `reaper_check` — validate a finished draft before it goes into Suno
🟦 `reaper_respell` — sweep text for pronunciation hazards

## Command

```
/reaper lanes [query]
/reaper spec <lane>
/reaper block <lane> | <title> | <hook>
```

## The hard limits

Enforced in code, not eyeballed:

🟦 Style field ≤ **1000 characters**
🟦 Lyrics field ≤ **3000 characters**

`reaper_block` fits the style field for you. Priority order is descriptor → ARC →
BPM/key → persona, so when a lane runs long it is the tail that gives way, never the
ARC.

## What gets validated

`reaper_check` reports pass/fail on:

🟦 style length and artist references (`sounds like`, `in the style of`, `feat`)
🟦 lyric length
🟦 every section header carrying a recognised structural tag
🟦 contradictory dynamic tags sharing one section (`[High Energy] [Low Energy]`)
🟦 the song actually having a chorus or hook
🟦 known-to-slur proper nouns left un-respelled in the finished lyric

## Worked example

```python
reaper_block(lane="ghetto-blues", title="Hood Up",
             hook="i put my head down and i built it from the ground",
             concept="the climb, staying solid")
```

Returns a pasteable deliverable containing:

- a style field with the ghetto-blues ARC (lone piano and guitar → soft trap knock →
  half-sung confessions → autotuned melodic cry → guitar break → biggest hook last)
- the exclude line (`aggressive shouting, EDM drops, harsh distortion, ...`)
- a tagged lyric frame with bar targets and the hook placed in every chorus
- a pronunciation lexicon for every proper noun in the title, hook and concept
- generation notes (`BPM drift DOWN and a minor-key drift are FEATURES here`)

## Why the studio does not write lyrics

Anything that assembles bars from templates produces interchangeable filler — the
kind of thing that reads as competent and means nothing. The valuable, non-generic
parts of a hip-hop track are the production decisions and the writer's specifics.
So the desk owns the first and hands the second to you with the structure already
solved. The frame is the craft; the bars are the art.

## Tests

```bash
python -m unittest discover -s tests
```

54 offline tests. Includes a full sweep asserting that **all 41 lanes** build a
deliverable that passes its own validation gates.

## Layout

```
plugin.yaml                 manifest
__init__.py                 register() — 5 tools, /reaper, bundled skill
genres.py                   the 41-lane catalog
studio.py                   builder, validator, respell engine
tools.py                    tool schemas + handlers
skills/rhythm-reaper-operations/SKILL.md   operator's manual
tests/                      54 offline tests
```
