# Agent finale: same alert, same agent, two labs

Real Claude Code (pinned to 2.1.312 in `cc/`) runs in a browser terminal ([ttyd](https://github.com/tsl0922/ttyd)) against a
scripted model (`mock_model.py`). The two videos at the end of the talk are recorded from it. It asks the same question twice:

> The departure boards alert fired: boards falling back to the timetable since 18:16. Find out why.

- **classic**: an `opensearch` MCP server with `search_logs` / `field_stats` on `classic-logs` (log lines only).
  The agent finds the fallback lines (`stops_api_ms` ~700), /departures p50 up from ~10 ms to ~500 ms, stops-api fast
  by its own logs (p95 ~53 ms, traffic up less than 2x), no errors and no deploy, and stops with an honest
  "I can't tell from this data", listing what it would need.
- **enriched**: the same MCP server name plus `search_traces` / `get_trace`. The agent opens the trace of a
  slow board request (client span ~1 s vs stops-api server span a few ms: waiting for one of the 5 pool
  connections), asks who holds the connections the way a human would in Jaeger (departures-api traces of the
  last 2 minutes, most spans first: all JourneyApp/5.0.0 with `include=route` and 53 spans, boards and 4.0.7
  have 3), opens one (26 parallel stops-api calls), and ends with root cause, evidence (trace ids) and mitigation.

Nothing calls the real Anthropic API: `ANTHROPIC_BASE_URL` points at `127.0.0.1:8787`, the key is a dummy.

## Files

| file | what |
|---|---|
| `story.py` | the two scenes, written as code. **Edit wording here**, then `python3 story.py` writes `scenes.json` |
| `scenes.json` | generated: `{classic, enriched}` → `{label, prompt, turns:[[{text}, {tool, input, result}]]}` with `{{placeholders}}` |
| `values.json` | every number, id and timestamp the scenes show, referenced as `{{key}}` (see below) |
| `mock_model.py` | scripted Messages API on :8787; path `/classic` or `/enriched` picks the scene; GET `/next` = clicker |
| `fake_mcp.py` | stdio MCP server `opensearch` (`fake_mcp.py classic` or `enriched`), answers from scenes.json |
| `claude_live.sh` | starts Claude Code for one lab, fresh config dir each start (`cc/home-<lab>`, from `cc/claude.seed.json` and `cc/mcp.<lab>.json`), light theme, `--verbose` so tool results are shown |
| `live.sh` | both terminals for live use: classic on localhost:7681, enriched on :7682, plus the mock |
| `recording/record.mjs` | records one run to `recordings/agent-<lab>.mp4` (1920x1080, h264) |
| `transit-platform/` | the agent's working directory (only `.claude/settings.json`: allows `mcp__opensearch`) |

## Record

Needs Node.js, Python 3, `ttyd` and `ffmpeg` (`brew install ttyd ffmpeg`).

```bash
cd agent-demo
(cd cc && npm ci)              # only if cc/node_modules is missing
(cd recording && npm ci)       # only if recording/node_modules is missing (playwright-chromium)
node recording/record.mjs classic  --pace 7 --tail 20
node recording/record.mjs enriched --pace 7 --tail 20
```

Claude Code prints the wall clock at the end ("done 12:13"). The recordings use `TZ=Etc/GMT-7` (UTC+7) and were
started at 12:23 local, so it reads "done 18:24"/"18:26", matching the story clock. Re-recording at another time:
pick an `Etc/GMT-N` zone that maps the current time to ~18:24-18:30 (Node ignores minute offsets like `XST-7:08`).

Each run takes about 70 s plus encoding, starts its own mock model (:8787) and ttyd (:7689) and stops them at
the end, so don't run it while `live.sh` is up. Options: `--pace` seconds per agent turn, `--tail` seconds the
final answer stays on screen, `--font` terminal font size in px (default 24), `--keep-frames` keeps the PNGs
in `recordings/frames-<lab>/`. Output: `recordings/agent-classic.mp4` (~66 s), `recordings/agent-enriched.mp4` (~74 s).

Check a recording:

```bash
ffmpeg -ss 40 -i recordings/agent-enriched.mp4 -frames:v 1 check.png && open check.png
```

## Run live (or rehearse)

```bash
bash live.sh              # 5 s per turn on its own, GET http://127.0.0.1:8787/next skips ahead
bash live.sh --manual     # only /next advances (clicker / slide)
bash live.sh --pace 3
```

Open http://localhost:7681 (classic) and http://localhost:7682 (enriched), type the prompt above (any prompt
containing alert/board/timetable/why/departure starts the scene). Ctrl-C stops everything.
`curl -s 127.0.0.1:8787/next` advances one step; `curl -s 127.0.0.1:8787/state` shows where it is.
To show the tool calls folded ("Called opensearch") instead of with their results, start with
`DEMO_CLAUDE_FLAGS= bash live.sh`.

## Update the values (from the real lab)

All concrete values in the scenes are placeholders filled from **`values.json`**:
`{"key": {"value": "...", "about": "what it is"}}`. The scenes only contain `{{key}}`. To use the lab's numbers:

1. Edit the `value` fields in `values.json` (keep them strings; write numbers as you want them shown in
   prose, e.g. `"1,018"`: tables and key=value lines strip the thousands separator where needed).
   The main ones: `trace_board` (slow board request trace id), `trace_journey` (JourneyApp/5.0 trace id),
   `board_client_ms` / `board_server_ms` / `board_wait_ms`, `journey_calls`, the `win_*` counts for the
   two-second window, `journey5_first_seen`, the `board_*` / `stops_*` percentiles and counts,
   `first_fallback`, `fallback_count_1h`, `version`, sample stops and timestamps.
2. No regeneration needed: `mock_model.py` and `fake_mcp.py` fill the placeholders each time they read the
   scenes. Re-record both videos.
3. If a fact changes the story (not just a number), edit the text in `story.py`, run `python3 story.py`, re-record.

The values in `values.json` are real: taken read-only from the lab incident of 17 Nov 2026 (rollout 11:59:15,
alert 12:03:06), mapped onto the story clock as real + 6h13m (alert 18:16, the agent runs at ~18:24; tables use
3-minute buckets of the last 15 minutes). The pool size (5) and the 500 ms live-data budget are written into
prose in `story.py`.

## Notes

- Claude Code pretty-prints JSON tool results over many lines, which scrolls the story off screen, so the
  fake tools answer with short text: log hits as key=value lines, stats as small tables, traces as a span tree.
- `cc/claude.seed.json` is the Claude Code config each start begins with (onboarding done, dummy key approved,
  theme light). `@DEMO_DIR@` in it and in `cc/mcp.<lab>.json` is replaced with this directory at start.
  `cc/requests.log` logs every request Claude Code sent to the mock.
- `cc/ttyd-index.html` is ttyd's own page, served with `--index`.
