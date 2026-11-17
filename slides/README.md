# Evolution, not revolution: the deck

[Slidev](https://sli.dev) deck for the talk at OSMC 2026, Nuremberg. The published version is linked from the
[repo README](../README.md).

```bash
npm install
npm run dev      # deck on http://localhost:3030, presenter view with speaker notes at /presenter
npm run build    # static build into dist/
```

The speaker notes carry rough timings (`[mm:ss]`) and say what to say on each click.

## The demo slides

The lab demo is replayed from stills of the real lab (`public/walk/*.png`). Each click adds a spotlight or a
zoom. `components/WalkShot.vue` draws them from the boxes in `components/walk.json`. To capture new stills, run
`make walk` in [`../lab`](../lab) while the incident is on.

The two agent videos (`public/video/`) are recorded with [`../agent-demo`](../agent-demo).

## Components

| component | used for |
|---|---|
| `PhoneAlert` | cold open: the departure board, then the critical check |
| `ClassicTools` | the check, the graph, the logs (two rounds) |
| `IncidentChat` | the on-call chat (three rounds) |
| `Bikeshed` | the detour |
| `EvolutionChart` | systems vs. the way we catch and fix problems |
| `Villages` | the motif: villages, roads, a railway |
| `LabMap` | what we have, what we add, what's next |
| `WalkShot` | one step of the demo, from a still |
| `SectionCard`, `ThanksBronto`, `QrCode` | section cards, the last slide |

`global-top.vue` gives keyboard focus back after clicks, so the arrow keys keep working.
