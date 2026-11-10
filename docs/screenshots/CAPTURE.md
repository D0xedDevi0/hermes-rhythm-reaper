# Screenshots

Stills pulled from the encoded cut with
`ffmpeg -ss <t> -i docs/demo.mp4 -frames:v 1 <name>.png`, so each one shows exactly what
the video shows at that second - drawn from the captured handler ledger, not mocked up.

| file | at | what it is |
| --- | --- | --- |
| `lane-spec.png` | 30s | `reaper_lane uk-drill` - tempo, key, drums, low end, harmony, vocal, the ARC, and the section plan with bar counts and an energy map |
| `deliverable.png` | 50s | `reaper_block ghetto-blues` - the pasteable deliverable in Suno's field order, with the fitted character counts |
| `validator-verdict.png` | 66s | `reaper_check` on a real finished draft - both limits measured, 0 issues |
| `lane-sweep-41of41.png` | 88s | the sweep: all 41 lanes built and gated in one pass |

Rebuild the whole cut:

```bash
python3 scripts/demo_render.py html
python3 scripts/demo_render.py capture --start 0 --end 2835   # 94.5s of timeline at 30fps
python3 scripts/demo_render.py encode
```

Then re-extract the stills with the timestamps above. The renderer refuses to run without
`docs/evidence/demo_scenes.json`, so a still can never drift from the ledger it came from.
