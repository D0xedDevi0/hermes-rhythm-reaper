# Forty-One Lanes

The demo's track — the one piece of this repo the producer desk did **not** write.

The studio's whole position is that template bars are interchangeable filler, so it hands
over a correct frame and refuses to fill it. These bars are written by hand into that frame,
and then run back through the desk's own gates. Nothing on this page is hand-counted:
the style field, the bar targets, the energy map, the lexicon and the character counts are
output from `reaper_block`, `reaper_check` and `reaper_respell` at this commit.

## How it was made (exact calls)

```python
handle_reaper_lanes({"query": "cinematic"})          # dark-trap, trip-hop, horrorcore
handle_reaper_lane({"lane": "dark-trap"})            # 120-140 BPM, C# minor, dissonant-choir arc
handle_reaper_block({"lane": "dark-trap", "title": "Forty-One Lanes",
                     "hook": "forty-one lanes and the reaper on the desk",
                     "bpm": 128, "key": "C# minor", "persona": "..."})
handle_reaper_check({...})                          # -> ok: True
handle_reaper_respell({"text": <the finished lyric>})  # -> 0 changes, 0 candidates
```

The tempo is pinned to 128 BPM on purpose: 72 bars at 128 in 4/4 is
**135.0 seconds** exactly, so the section boundaries can be lined up against the demo cut
without guessing. Hook 1 lands at 37.5s — on the deliverable scene; hook 2 at 82.5s —
on the 41/41 sweep.

## Style field (568/1000)

```text
Dark trap with cinematic dread, heavy distorted kick, wet snare, rolling hats, industrial percussion, saturated distorted 808 sub, dissonant choir pads and detuned bell motifs with metallic hits, low menacing rap vocal with whispered ad-libs and a growled double on the hook, wall-of-sound mix. Choir pad and a detuned bell alone. Industrial hits land. Drums slam in. Verses stay low and menacing. The hook layers a growled double. A string swell resets. 128 BPM, C# minor. low menacing delivery, whispered ad-libs, growled doubles, one clean singing layer on the hook
```

## Exclude Styles

```text
major keys, bright plucks, playful melodies, clean sub, acoustic warmth
```

## Lyrics (1827/3000)

```text
[Intro] [Choir]
three a.m., the desk is still awake
forty-one lanes and I'm reading them all
(reap it)

[Verse 1]
three a.m., the desk is still awake
forty-one lanes and I'm reading them all
I asked for the sound and not for the name
sliding eight-oh-eight, five lanes at my call
tempo, key, drums, the low end, the dread
the arc, so the loop doesn't loop in my head
verse stays low, the hook stacks a growl on the double
and the choir is dissonant, never comes cheerful

[Hook] [Choir] [Distorted 808]
forty-one lanes and the reaper on the desk
Noose in the blood, Hermes never rest
Doxed Dev on the build, no slop in the text
the check came back false, now it's true, that's the flex
(forty-one)

[Verse 2]
I pasted a draft and it came back false
artist reference, untagged header, no hook at all
it doesn't rewrite me, it only holds the line
the fix is a writing decision, and it's mine
the field holds a thousand, the frame holds three
measured, not eyeballed, it counted for me
false, then true on the very same draft
cheap to catch it now, expensive after

[Hook] [Choir] [Distorted 808]
forty-one lanes and the reaper on the desk
Noose in the blood, Hermes never rest
Doxed Dev on the build, no slop in the text
the check came back false, now it's true, that's the flex
(reap it)

[Verse 3]
Noose Research wrote the agent, I taught it to build
Hermes on the wire with the tools in its hands
Doxed Dev in the terminal, no keys in the repo
no calls out the door, just the catalog and the frame
five tools, fifty-four tests, one pull request open
hackathon clock running, reap it then repeat

[Hook] [Choir] [Distorted 808]
forty-one lanes and the reaper on the desk
Noose in the blood, Hermes never rest
Doxed Dev on the build, no slop in the text
the check came back false, now it's true, that's the flex
(all forty-one)
```

## Energy map (as specified, and as written)

| section | bars | energy | starts at |
| --- | --- | --- | --- |
| Intro | 4 | 3/10 | 0.0s |
| Verse 1 | 16 | 6/10 | 7.5s |
| Hook | 8 | 8/10 | 37.5s |
| Verse 2 | 16 | 6/10 | 52.5s |
| Hook | 8 | 8/10 | 82.5s |
| Verse 3 | 12 | 7/10 | 97.5s |
| Hook | 8 | 9/10 | 120.0s |

## Pronunciation lexicon

The desk's respell sweep over the finished lyric returns **0 changes and 0 candidates**:
the body is already written the way it should be sung — `Noose Research` for Nous,
`Doxed Dev` for D0XEDDEV, `eight-oh-eight` for 808.

Left as a rendering note rather than a lyric change:

- **Forty-One** — respell to the SOUND (test in a 30s clip)
- **Nous** — Noose
- **D0XEDDEV** — Doxed Dev

## Generation notes

- Reroll if the choir comes back cheerful - it must be dissonant.
- Saturate the 808; this lane wants grit.

## What this does not claim

Suno does not obey a bar map literally. The frame gets the structure, the tempo and the
dynamics into the first render; expect to reroll, and expect to trim. If the render comes
back at a different length than 135s, the cut is adjusted to the track, not the other way
around.

## The render (as received)

| | |
| --- | --- |
| length | 181.6s |
| format | mp3, 48 kHz stereo, 192 kbps, plus embedded cover art |
| loudness | -15.6 LUFS integrated, LRA 4.5 LU, true peak -3.2 dBFS |
| container tags | `title=Forty-One Lanes`, `artist=d0xeddev`, `comment=made with suno; created=2026-11-10T17:44:45Z; id=39e75399-...` |
| embedded `lyrics-eng` | the frame above, byte-for-byte, minus the trailing newline |

Suno did not follow the bar map literally - it rendered 96 bars instead of 72 and stretched the
whole thing to 3:02. Before cutting anything, the section map was measured off the audio rather
than assumed: RMS in 0.5s windows shows a **breakdown from 123.0-127.5s**, the drop back in at
**128.0s**, and the biggest section of the track starting at **160.5-161.0s** and running to the
end. (Those are energy boundaries, not lyric timings - the container carries no timestamps, so
the hook attribution below is inference, not measurement.)

## The overlay

The video is 94.5s and the track is 181.6s, so the cut uses **the last 94.5s of the track**
(offset 87.1s) instead of truncating it: the song's own ending lands on the video's ending, and
nothing is faded out early. Where the measured events land on screen:

| song | video | scene |
| --- | --- | --- |
| 123.0-127.5 breakdown | 35.9-40.4s | the tail of the lane spec |
| 128.0 drop | 40.9s | first frames of the pasteable deliverable |
| 160.5-181.6 final section | 73.4-94.5s | respell -> **41/41 sweep** -> outro |

Mux, with the video stream copied so no frame is re-encoded:

```bash
ffmpeg -ss 87.1 -i "Suno export.mp3" -i docs/demo.mp4 \
  -af "volume=0.5dB,afade=t=in:st=0:d=0.25" \
  -c:v copy -c:a aac -b:a 192k -ar 48000 -movflags +faststart -shortest docs/demo-song.mp4
```

- gain is a plain **+0.5 dB linear, no dynamics processing** - the source was already consistently
  loud (LRA 4.5 LU), so there is nothing for a compressor to fix and no excuse for one.
- a 0.25s fade-in only, because the cut starts mid-phrase; no fade-out, because the song ends.
- video stream md5 of the muxed file equals the silent cut's (`7a0920bd8a34e98d5b2d9d869941bbac`,
  2835 frames), i.e. the picture in `docs/demo-song.mp4` is byte-for-byte `docs/demo.mp4`.
- delivered audio: **-14.3 LUFS integrated, -2.4 dBFS true peak** - inside the -14/-1.5 target
  social platforms normalise against, with margin for their transcodes.

`docs/demo.mp4` stays in the repo as the silent evidence artifact; `docs/demo-song.mp4` is the
version with the track.
