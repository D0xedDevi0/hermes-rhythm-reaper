# Screenshots

Stills pulled from `docs/demo.mp4` with `ffmpeg -ss <t> -frames:v 1`, so each one shows
what the demo shows at that second - real captured tool output, not a mock-up.

| file | at | what it is |
| --- | --- | --- |
| `lane-spec.png` | 22s | `reaper_lane uk-drill` - tempo, key, drums, low end, the ARC, and the section plan with bar counts and an energy map |
| `deliverable.png` | 36s | `reaper_block ghetto-blues` - the pasteable deliverable in Suno's field order, with the fitted character counts |
| `lane-sweep-41of41.png` | 72s | the sweep: all 41 lanes built and validated in one pass |

Rebuild: `python3 scripts/demo_build.py render`, then re-extract with the timestamps above.
