---
name: rhythm-reaper-operations
description: Use when producing a hip-hop track — pick a lane, build a production-ready Suno deliverable, validate it, then fill the bars.
---

# The Rhythm Reaper — operator's manual

A hip-hop producer desk. 41 lanes across seven families. It hands you the
production frame; **you write the bars**. That division is deliberate — this desk
does not emit template lyrics, because generated bars are slop and you can hear it
in the first four.

## When to use this

- The user wants a hip-hop track, beat concept, or Suno prompt in any subgenre.
- The user has a draft and wants it validated before rendering.
- The user has a proper noun that keeps getting slurred in a render.

## The five-step loop

1. **Pick the lane.** `reaper_lanes` with a query or family. If the user gave a
   vague brief ("something dark and slow"), search the production vocabulary —
   "sliding 808", "half-time", "cowbell", "gospel" — not just names.
2. **Read the spec.** `reaper_lane` gives tempo, keys, drums, low end, harmony and
   sample source, vocal delivery, the ARC, metatags, what to exclude, and the
   section plan with bar targets and an energy map. Read the ARC out loud to
   yourself before you write a single line.
3. **Build the deliverable.** `reaper_block` with the lane, a title (usually the
   hook), the hook line, and a one-line concept. Out comes the style field written
   out, the Exclude Styles line, a tagged lyric frame with bar slots and the hook
   placed, a pronunciation lexicon, and generation notes.
4. **Write into the frame.** Real bars, real imagery, specific to the user's story.
   The frame gives you bar counts and where the energy rises — use them.
5. **Validate before pasting.** `reaper_check` on the FINISHED lyric. Then paste
   into Suno: Title / Style / Exclude / Lyrics.

## The hard limits — enforced in code, not eyeballed

- **Style field ≤ 1000 characters.** Measured by `reaper_check`.
- **Lyrics field ≤ 3000 characters.** Measured by `reaper_check`.

`reaper_block` already fits the style field: the descriptor and the ARC are the
priority, and the tail (BPM, key, persona) is what gives way if a lane runs long.
Do not re-add text after `fit` has trimmed it without re-checking.

## Style field anatomy

Order matters, because trimming eats from the end:

1. **Descriptor** — the sound itself: drums, low end, harmony, vocal. No artist names.
2. **The ARC** — the single highest-leverage line in the whole field. It is the
   dynamic journey: what opens bare, when drums land, where the hook opens up, what
   strips back before the end. Without an ARC every render is a flat 2-minute loop.
3. **BPM and key.**
4. **Persona** — optional vocal character sentence.

Never write "sounds like <artist>" or "in the style of <artist>" — Suno ignores or
misreads it, and it adds nothing a production description cannot carry. Describe
the sound.

## The Exclude Styles field is not optional

Each lane carries an `exclude` list. Drop the lane's exclude line in verbatim. Most
"the genre came out wrong" complaints are a missing exclude: trap hats appearing in
a boom-bap beat, autotune in a conscious track, clean sub in phonk.

## Pronunciation — fix it in the LYRICS, before the render

Pronunciation is baked in at generation. There is no post-render fix short of
re-recording. So:

- **Sweep the FINISHED lyric**, not just the title. `reaper_respell`.
- Proper nouns, acronyms, digit-bearing tokens and camel-case brand names are the
  hazards: they are read, not performed.
- Caps and hyphens fix most slurs. `DisTrO` → `Dis-tro`; `x402` → `ex four oh two`.
- **Test unusual ones in a 30-second clip first.** A full render is an expensive way
  to find out that a word still slurs.
- **If a caps fix fails on a word the rhyme depends on, stop respelling and rewrite
  the bar.** Fighting the pronunciation costs more than changing the line.

## Bar-level craft that the frame cannot do for you

- **One image per bar, and make it concrete.** "Down bad in December with the heat
  off" beats "going through hard times" every single time.
- **The hook must be sayable after one listen.** If you cannot repeat it back, it is
  a verse line, not a hook.
- **Do not rhyme the same vowel sound four bars running** unless the monotony IS the
  effect (it is in chopper-style runs and chanted hooks — nowhere else).
- **Respect the energy map.** Section energies are in the plan; a bar that reads
  intimate does not belong in the breakdown.

## Genre traps worth knowing

- **Trap** is a *drum programme*, not a tempo. Reroll any drop that comes back tame —
  the failure mode is a polite beat with the right BPM.
- **Drill** lives and dies on the sliding 808 and the sparse arrangement. Static sub
  or a busy beat means reroll.
- **Ghetto blues and pain music** tolerate BPM drift *down* and a minor-key drift:
  those are features, not defects. Do not chase the spec to the decimal, and keep the
  guitar or keys break.
- **Boom bap** that lands straight has failed; the swing is the genre. Keep the
  crackle.
- **Phonk and drift phonk** want saturation and grit. A clean mix ruins them.
- **Lo-fi and cloud rap** depend on reverb and noise floor. Cleaning them up destroys
  the lane.

## Reproduction checklist

- [ ] Lane chosen and its ARC read before writing
- [ ] Style field ≤ 1000 chars, no artist references
- [ ] Exclude line taken from the lane verbatim
- [ ] Every section header carries a structural tag ([Verse 1], [Chorus], …)
- [ ] Hook present and sayable
- [ ] Proper nouns respelled in the finished lyric
- [ ] `reaper_check` reports `ok: true`
- [ ] Unusual pronunciations tested in a 30s clip
