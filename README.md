# The Rhythm Reaper

**A hip-hop producer desk for Hermes Agent.** 41 lanes across seven families, and for any
one of them a complete production frame you can paste straight into Suno — style field,
exclude line, tagged lyric frame with bar targets, energy map, pronunciation lexicon.

It knows the difference between the drum programme of boom bap and the sliding 808 of
drill, and it enforces the platform's real limits in code instead of eyeballing them.

**It does not write your bars.** Template lyrics are slop and you can hear it in the first
four. The desk owns the production decisions and hands you the structure already solved.

## Watch it

A 94-second walkthrough — animated, rendered offline from real captured tool output —
[`docs/demo.mp4`](docs/demo.mp4) ([source ledger](docs/evidence/demo_capture.txt) ·
[proof](docs/evidence/demo_proof.json)):

Every frame is drawn on a canvas by [`docs/render/demo.html`](docs/render/demo.html),
where the whole picture is a pure function of `t`: nothing is timed, nothing is randomised
per run, so any frame can be re-rendered identically at any time.
[`scripts/demo_render.py`](scripts/demo_render.py) drives that page through the local
Chrome (CDP), writes the PNG sequence, and encodes it with ffmpeg. The strings it draws
come from the ledger, which `scripts/demo_build.py capture` produced.

1. searching the catalog by *sound* (`sliding 808`) rather than by name;
2. one lane read out in full — tempo, key, drum programme, low end, the dynamic ARC, and a
   section plan with bar counts and an energy map;
3. `reaper_block` returning a pasteable deliverable inside the 1000/3000-char limits;
4. the validator rejecting a real bad draft and passing a real finished one;
5. the pronunciation sweep on a hazard line;
6. the sweep that matters: **41/41 lanes build a deliverable that passes its own gates.**

Nothing in it is a screen recording — the frames are generated from captured handler
output, and every line traces back to the ledger. `scripts/demo_build.py capture` re-runs
the real calls; `render` rebuilds the cut.

## Install

```bash
hermes plugins install D0xedDevi0/hermes-rhythm-reaper --enable
```

Or, if it is already in your catalog:

```bash
hermes plugins enable rhythm-reaper
```

No credentials. No network. No subprocesses. Pure local computation — the 41-lane catalog
is a Python module in this repo.

## Quick start

```
/reaper lanes sliding 808
/reaper spec uk-drill
/reaper block ghetto-blues | Hood Up | I put my head down and I built it from the ground
```

Or from an agent session, with the tools:

```python
reaper_lanes(query="gospel half-time")          # find a lane by production vocabulary
reaper_lane(lane="ghetto-blues")                # the full spec + section plan + energy map
reaper_block(lane="ghetto-blues", title="Hood Up",
             hook="I put my head down and I built it from the ground",
             concept="the climb, staying solid when nobody was watching")
reaper_check(style=..., lyrics=<finished lyric>, hook=...)   # validate before pasting
reaper_respell(text=<finished lyric>)           # sweep pronunciation hazards
```

## The lanes

🟦 **foundational** (10) — boom bap, jazz rap, G-Funk, old-school electro, Miami bass, New Orleans bounce, hyphy, crunk, snap, chopped and screwed
🟦 **trap** (8) — trap, southern/Memphis trap, dark trap, plugg/pluggnb, rage, hyperpop rap, afro-trap, Latin trap
🟦 **drill** (4) — UK drill, New York drill, sample drill, Detroit/Flint
🟦 **melodic** (4) — ghetto blues (soul-trap / pain music), trap soul, emo rap, cloud rap
🟦 **alt** (6) — lo-fi hip hop, beat tape / instrumental, trip hop, abstract / alternative, nerdcore, country rap
🟦 **hard** (7) — horrorcore, Memphis horrorcore, trap metal / scream rap, phonk, drift phonk, grime, chopper / speed rap
🟦 **conscious** (2) — conscious / political, boom bap revival

Every lane carries tempo family, key centres, drum programme, low end, harmony and sample
source, vocal delivery, **the dynamic ARC**, metatag vocabulary, what to exclude, and
generation notes.

## What one lane returns

`reaper_lane("uk-drill")` — real output, shortened:

```
bpm   138-145          key   F minor
drums sparse punchy kick, sharp snare on the 2 and 4, rolling hats
low   signature sliding 808 sub, aggressive glide between notes
ARC   A single dark piano note holds alone. The sliding 808 and drill drums land.
      Verses are cold and clipped. The hook repeats a deadpan threat.
      A silent pocket drops before the final verse.

section plan:
  Intro      4 bars  energy 4/10      Verse 2   16 bars  energy 7/10
  Verse 1   16 bars  energy 7/10      Hook       8 bars  energy 8/10
  Hook       8 bars  energy 8/10      Verse 3   12 bars  energy 8/10
```

## Why the ARC is the point

The ARC is the one line that stops every render being a flat two-minute loop: what opens
bare, when the drums land, where the hook opens up, what strips back before the end.

It is also the field that never gets trimmed. `reaper_block` fits the style field by
dropping **whole clauses** in a deliberate priority order — descriptor → ARC → BPM/key →
persona — so a long lane loses the tail, never the dynamics.

Real fitted result for `ghetto-blues` / *Hood Up*: **638 / 1000 characters**, ARC intact,
lyric frame **448 / 3000**.

## The validator

`reaper_check` measures the finished draft, not the frame:

🟦 style field ≤ **1000 characters**, lyrics ≤ **3000 characters**
🟦 no artist references (`sounds like`, `in the style of`, `feat`) — describe the sound
🟦 every section header carries a recognised structural tag
🟦 no contradictory dynamic tags sharing one section (`[High Energy] [Low Energy]`)
🟦 the song actually has a chorus or hook
🟦 known-to-slur proper nouns left un-respelled in the finished lyric

A real bad draft, caught:

```
ok=FALSE
  ! references another artist's style - describe the SOUND instead
  ! 2 section header(s) carry no recognised structural tag
  ! no chorus/hook section - the song has no payoff
```

It reports; it does not silently rewrite. The fix is a writing decision, and the desk does
not make those for you.

## Pronunciation

Pronunciation is baked in at generation — there is no post-render fix short of
re-recording. So sweep the **finished lyric**, not just the title:

```
$ reaper_respell("I got the JPEG scan of the 40B and a DisTrO run on Nous with x402 receipts")
  nous    -> Noose
  x402    -> ex four oh two
  jpeg    -> J-peg
  distro  -> Dis-tro
  40      -> four oh
```

Caps and hyphens fix most slurs. When a caps fix fails on a word the rhyme depends on, stop
respelling and rewrite the bar.

## Tests

```bash
python -m unittest discover -s tests -v     # 54 offline tests, stdlib only
```

The suite includes the sweep the demo shows: **every one of the 41 lanes** is built through
`reaper_block` and asserted to pass its own validation gates, so a lane that stops building
fails CI rather than failing a user. CI also proves the plugin imports with `python3 -S`
(standard library only) and that every tool declared in the manifest is actually registered.

## Trust and disclosure

- **Egress:** none. No network call of any kind, at install time or at runtime.
- **Credentials:** none read, none needed. No tool is gated, because no tool can be broken
  by a missing secret. The plugin never touches `os.environ`, `.env`, `auth.json`, or any
  other credential store.
- **Files written outside the plugin:** none. The plugin is pure computation over the
  catalog in this repo; there is no data directory, cache, or log file.
- **Shell / background behaviour:** none in the plugin. No `subprocess`, no threads, no
  timers, nothing spawned. Two developer tools outside the plugin's import graph do spawn
  processes: `scripts/demo_build.py` calls `ffmpeg` to encode the demo, and
  `scripts/demo_render.py` drives the local Chrome over CDP and then calls `ffmpeg`.
  Neither script is imported by the plugin.
- **Committed binaries:** none. `docs/demo.mp4` is a rendered demo artifact; there is no
  compiled code, no `.so`, no bytecode.

## Layout

```
plugin.yaml                 manifest (5 tools, 0 hooks, no deps, no env)
__init__.py                 register() - 5 tools, /reaper command, bundled skill
genres.py                   the 41-lane catalog
studio.py                   builder, validator, respell engine
tools.py                    tool schemas + handlers
skills/rhythm-reaper-operations/SKILL.md   operator's manual (loaded with the plugin)
scripts/demo_build.py       capture the real handler output, and render the static cut
scripts/demo_render.py      render the animated cut through Chrome + ffmpeg
docs/render/demo.html       the animated demo itself (canvas, deterministic from t)
tests/                      54 offline tests
docs/                       the demo cut and its source ledger
```

## License

MIT — see [LICENSE](LICENSE).
