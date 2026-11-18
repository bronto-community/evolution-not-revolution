# Evolution, not revolution: the lab

The live demo for the OSMC 2026 talk. The same incident in two labs side by side, same apps, same traffic,
same UI (one OpenSearch + OpenSearch Dashboards). The only difference is the data:

- **classic**: what teams have today. The apps write their log line; Fluent Bit ships it to OpenSearch
  (`classic-logs-*`) and splits it into fields. No traces, no trace id, no OpenTelemetry.
- **enriched**: the same apps, same image, same start command, plus context: the **OpenTelemetry Injector**
  (`/etc/ld.so.preload`, zero code) with the Python agent, **`trace_id`/`span_id` appended to the same log line**, and
  an **OpenTelemetry Collector** that reads the same log files, receives the traces, gives everything the same names
  (OpenTelemetry semantic conventions) and writes logs and spans to OpenSearch (`enriched-logs-*`, `enriched-spans-*`)
  and the traces to **Jaeger** (waterfall).

## The incident

We are the platform team of a city transit operator. **departures-api** (ours) serves live departures for a stop;
its most important clients are the departure boards in the stations. **stops-api** is the network data team's
shared master-data service (also used by the website and the ticket machines).

- Every `/departures` request makes one quick call to stops-api (`/stops/<id>/platforms`, ~6 ms), through a
  shared urllib3 connection pool (`app/departures_api.py`: `PoolManager(maxsize=POOL_SIZE, block=True)`,
  `POOL_SIZE` 5, "plenty" since 2019). A board shows the printed timetable when live data takes longer than
  500 ms: `WARNING event=served_from_timetable ... reason=live_data_late stops_api_ms=...`.
- A third-party journey planner app polls our public API. **JourneyApp 4.0** polls `/departures?stop=X` like a
  board. **JourneyApp 5.0**, rolling out through the app stores, adds `&include=route`: departures-api then also
  looks up the next 5 stops of each of the 5 departures, **25 calls to stops-api** (`/stops/<id>`, ~45 ms),
  in parallel through a `ThreadPoolExecutor` "to be fast". Same endpoint, same polling rate, status 200.
- The 5.0 requests take the pool's connections; board requests **wait inside departures-api** for a connection
  (~1 s), miss their live-data budget, get the timetable. That is the alert. stops-api stays fast (p95 ~53 ms),
  its traffic rises less than 2x. Nothing was deployed by us, no errors, all 200.
- **classic**: departures-api says `stops_api_ms=1200`, stops-api says `duration_ms=6`. The access log has the
  path, not the query string or the user agent: 4.0 and 5.0 look the same. The two teams' logs contradict each other.
- **enriched**: the trace of a slow board request shows departures-api's client span ~1 s, and inside it
  stops-api's server span ~10 ms: the time is lost before the call leaves us. The slowest requests are
  `user_agent.original = JourneyApp/5.0.0 ...`, `url.query = stop=...&include=route`, each with 25 calls to stops-api.
  These attributes come from the zero-code instrumentation, not from app code.
- **Mitigation**: `make fix` raises the pool to 50 (`STOPS_API_POOL_SIZE`, restart departures-api in both labs).

**Why the pool has 5 connections.** A full pool of N connections moves about N / 50 ms of stops-api calls per
second. With 10 connections that is ~200 calls/s per lab, and to keep 5.0 at ~15 % of the phones the base
traffic has to be ~2.5x what it is now; measured, that put the lab at 4-6 CPU cores and starved it into false
timetable fallbacks before the rollout. With 5 connections the whole lab runs at **~1.3 cores normal, ~1.8-2.2 cores
during the incident** (see Verified runs). The story is the same.

## What runs where

All ports on 127.0.0.1.

| | URL | |
|---|---|---|
| OpenSearch Dashboards | http://localhost:5601 | Discover, Alerting. Light theme, times Europe/Berlin |
| OpenSearch | http://localhost:9200 | `classic-logs-*`, `enriched-logs-*`, `enriched-spans-*` (daily, kept 2 days) |
| Jaeger UI | http://localhost:16686 | enriched traces, last 40000 traces in memory (~15 min of traffic) |
| classic departures-api / stops-api | http://localhost:8000 / http://localhost:8001 | e.g. `/departures?stop=plaerrer` |
| enriched departures-api / stops-api | http://localhost:8100 / http://localhost:8101 | |
| log files | `logs/classic/<host>/*.log`, `logs/enriched/<host>/*.log` | the "central log bucket" |

Compose projects (`scripts/lab.sh classic|enriched|shared <compose args>`):

| project | files | containers |
|---|---|---|
| transit-classic | `compose.yaml` + `compose.classic.yaml` | departures-api, stops-api, fluent-bit |
| transit-enriched | `compose.yaml` + `compose.enriched.yaml` | departures-api, stops-api (+ injector mounts), otel-collector |
| transit-shared | `compose.shared.yaml` | opensearch, dashboards, jaeger, loadgen |

`compose.enriched.yaml` is everything that is added for the enriched lab. The app image (`app/Dockerfile`,
`python:3.11.18-slim`, Flask, urllib3) has no OpenTelemetry in it.

Files: `app/` (departures_api.py, stops_api.py, common.py = access log, network.py = U-Bahn network + timetable,
loadgen.py), `injector/` (install.sh, ld.so.preload, etc/injector.conf, etc/default_env.conf),
`collector/config.yaml`, `fluent-bit/`, `jaeger/` (config, UI link back to Discover), `dashboards/`,
`scripts/` (setup.py, status.py, schedule.py, cycle.sh, verify.py, cpu.sh, ui/), `state/` (schedule, pool size,
loadgen.json), `runs/`, `screens/`, `recordings/`.

## Requirements

- Docker Desktop (the Makefile uses its `desktop-linux` buildx builder). Tested on Apple Silicon with 10 CPUs for
  the VM; the lab itself needs about 2 cores during the incident. The injector checksums are pinned for arm64;
  on amd64 `injector/install.sh` downloads the amd64 builds and skips the check.
- Python 3 on the host for `scripts/*.py`.
- Node.js and `npm install` in `lab/`, only for `make walk`, `make screens` and `make record` (headless Chromium).

## Make targets

| | |
|---|---|
| `make up` | start everything, wait until healthy, set up OpenSearch (templates, pipeline, retention, the two monitors) and Dashboards (index patterns, settings). First time ~3-5 min (Dashboards is slow to start), then ~1 min |
| `make down` | stop everything, keep the data |
| `make status` | the schedule, 5.0 share, per lab: boards served from timetable and their latency (what the boards saw, last 60 s), stops-api req/s and handling time (from its own logs), alert state; clock drift warning |
| `make schedule` | show the rollout plan. `ROLLOUT_AT=14:25` or `ROLLOUT_IN=10m`, `RAMP=5m` (default), `SHARE=15` (default, % of the phones on 5.0 at the end of the ramp), `OFF=1` |
| `make fix` | the mitigation: pool 5 -> 50, departures-api restarted in both labs |
| `make reset` | back to normal for the next run: rollout off, pool 5, departures-api restarted. `WIPE=1`: also delete all data and start fresh |
| `make screens` | screenshots of both click paths into `screens/` (needs the incident on) |
| `make walk` | stills of both click paths for the deck: `../slides/public/walk/` and `../slides/components/walk.json` (needs the incident on) |
| `make record` | videos of both click paths into `recordings/` (needs the incident on) |

## Schedule (the rollout)

The loadgen (one container, both labs) is the scheduler: the rollout is a change in the traffic, not a deploy.
`make schedule ...` writes `state/schedule.env`; the loadgen re-reads it every 2 s. It uses the **host's clock**
(mtime of `state/.clock`, written through the bind mount), because the Docker VM clock has drifted before;
`make status` warns when the VM clock is more than 5 s off.

Traffic per lab: 30 departure boards (poll every 3 s), 180 JourneyApp phones (poll every 3-7 s), the website +
ticket machines at 60 req/s straight to stops-api. The 5.0 share ramps linearly from 0 at `ROLLOUT_AT` to
`SHARE` % of the phones over `RAMP`, and stays there until `make reset` (or `make schedule OFF=1`).

For the talk: `make up` at least 20 minutes before (so there is normal history), then e.g.
`make schedule ROLLOUT_AT=14:20` about 10 minutes before you show the labs. Measured: boards start falling back
~1.5 min after the rollout start (5.0 at ~5 %), the alert fires in both labs after ~2-3 min, the incident is
fully developed at the end of the ramp.

## The live demo

In the talk the demo is replayed from stills (slides 22-25 and 30-36): `make walk` captures them while the incident
is on (about 5 minutes after the rollout starts); the deck outlines and zooms each step. The steps below are the same
click paths, for doing it live (Q&A, workshops).

Open beforehand: Dashboards (http://localhost:5601), Jaeger (http://localhost:16686). Time picker: Last 15 minutes.

### Before (classic): from the alert, following the data

1. **Alerting** (menu: OpenSearch Plugins > Alerting) > **Monitors** > `classic: departures served from timetable`.
   The monitor's own page: its trigger (more than 5 % from timetable), the History bar turning red, the active alert on top.
   (Not the Alerting overview: it lists every alert of both labs, all past runs included.)
   The alert counts `event=served_from_timetable` lines against `/departures` requests in the last minute (> 5 %).
2. **Discover**, index pattern `classic-logs-*`, query `event:served_from_timetable`. Add columns `stop`,
   `stops_api_ms` (click the field, "add"). All stops, all hosts; `stops_api_ms` ~600-2000: "stops-api is slow".
3. Same Discover, query `app:stops-api`. Add `path`, `duration_ms`. stops-api answers `/stops/<id>/platforms`
   in a few ms: "not us". Their p95 is ~50 ms.
4. What else is in the line? Field list: `method`, `path`, `status`, `duration_ms`, `host`. Query
   `app:departures-api and path:"/departures"`: all 200, no errors, same path for everything. No way to tell
   requests apart, no way to connect a departures-api line to the stops-api line it caused. Dead end.

### After (enriched): the same moment, the same moves, with context

1. **Alerting** > **Monitors** > `enriched: departures served from timetable`: the same monitor, on `enriched-logs-*`, Active.
2. **Discover**, index pattern `enriched-*` (logs and spans together), query
   `attributes.event.name:served_from_timetable`. The same lines, now with `traceId` (a link).
3. Click a `traceId` value: Jaeger opens the trace. `departures-api GET /departures` ~1.2 s, its client span
   `GET` (to stops-api) ~1.2 s, and inside it `stops-api GET /stops/<stop_id>/platforms` ~10 ms, at the very end.
   **The time is lost before the call leaves departures-api**: waiting for a connection.
4. Who has the connections? In Jaeger, **Search**: Service `departures-api`, Span Name `GET /departures`,
   Lookback `Last 5 minutes`, Limit `500`, Find Traces. In the scatter plot, dot size = number of spans: most dots
   are tiny (3 spans), a few are big. **Click a big dot**: a trace with ~53 spans opens, 26 parallel calls to stops-api.
   Click the root span: `user_agent.original = JourneyApp/5.0.0 (...)`, `url.query = stop=...&include=route`.
   (Alternative: Table view, click the Spans header twice for most first.)
   (Checked during an incident: of 200 recent traces, every one with more than 5 spans was JourneyApp/5.0.0.)
   Don't use the Discover field list for this step: the full user agent includes the device, so JourneyApp/4.0.7
   splits into several values and 5.0 doesn't stand out.
5. In that trace: one 5.0 request with **26 parallel calls to stops-api**,
   each waiting for one of the 5 connections. Root cause: the 5.0 rollout (`include=route`) exhausts
   departures-api's connection pool to stops-api; the boards queue behind it.
6. Optional: in Jaeger, the ↗ icon left of the trace title opens "Logs and spans of this trace in Discover", or in Discover query
   `traceId:<id>` on `enriched-*`: the request's spans and its log lines (both services) in one list.
7. `make fix` (pool 50). `make status`: boards back to ~0 % within ~1-2 min.

Where the attributes come from: `user_agent.original`, `url.query`, `http.route`, `url.full` are set by the
Python agent's Flask and urllib3 instrumentations (semantic conventions, `OTEL_SEMCONV_STABILITY_OPT_IN=http`);
the `ThreadPoolExecutor` children are connected to the request by the agent's threading instrumentation. No app code.

## The Collector config that gives everything the same names (slide)

From `collector/config.yaml`:

```yaml
receivers:
  file_log:
    include: [/var/log/transit/*/*.log]
    storage: file_storage
    operators:   # <time> <host> <app>[<version>]: <LEVEL> key=value ... trace_id=... span_id=...
      - type: regex_parser
        regex: '^(?P<time>\S+) (?P<host>\S+) (?P<app>[\w-]+)\[(?P<version>[^\]]+)\]: (?P<level>\w+) (?P<kv>.*)$'
        timestamp: { parse_from: attributes.time, layout_type: gotime, layout: '2006-01-02T15:04:05.000Z' }
        severity: { parse_from: attributes.level }
      - type: key_value_parser
        parse_from: attributes.kv
      # who wrote the line: the same resource attributes the apps put on their spans
      - { type: move, from: attributes.host,    to: 'resource["host.name"]' }
      - { type: move, from: attributes.app,     to: 'resource["service.name"]' }
      - { type: move, from: attributes.version, to: 'resource["service.version"]' }


processors:
  transform/logs:
    log_statements:
      - context: resource
        statements:
          - set(attributes["deployment.environment.name"], "production")
      - context: log
        statements:
          # the line's fields under their semantic-convention names
          - set(attributes["http.request.method"], attributes["method"]) where attributes["method"] != nil
          - set(attributes["url.path"], attributes["path"]) where attributes["path"] != nil
          - set(attributes["http.response.status_code"], Int(attributes["status"])) where attributes["status"] != nil
          - set(attributes["event.name"], attributes["event"]) where attributes["event"] != nil
          - set(attributes["duration_ms"], Int(attributes["duration_ms"])) where attributes["duration_ms"] != nil
          - set(attributes["stops_api_ms"], Int(attributes["stops_api_ms"])) where attributes["stops_api_ms"] != nil
          # trace_id/span_id at the end of the line: the log record's trace context
          - set(trace_id.string, attributes["trace_id"]) where attributes["trace_id"] != nil and attributes["trace_id"] != "0"
          - set(span_id.string, attributes["span_id"]) where attributes["span_id"] != nil and attributes["span_id"] != "0"
          - delete_matching_keys(attributes, "^(time|level|kv|method|path|status|event|trace_id|span_id)$")
  transform/spans:
    trace_statements:
      - context: span
        statements:
          - set(attributes["duration_ms"], (end_time_unix_nano - start_time_unix_nano) / 1000000)
```

The result in OpenSearch (collector-contrib `opensearch` exporter, default `ss4o` mapping):

| | logs (`enriched-logs-*`) | spans (`enriched-spans-*`) |
|---|---|---|
| service, version | `resource.service.name`, `resource.service.version` | the same |
| host, environment | `resource.host.name`, `resource.deployment.environment.name` | the same |
| request | `attributes.http.request.method`, `attributes.url.path`, `attributes.http.response.status_code` | the same + `attributes.url.query`, `attributes.user_agent.original`, `attributes.http.route` |
| trace | `traceId`, `spanId` | `traceId`, `spanId`, `parentSpanId` |
| time | `@timestamp` | `@timestamp` (= `startTime`, set by the ingest pipeline `enriched`), `attributes.duration_ms` (Collector) |

Classic (`classic-logs-*`, Fluent Bit): `host`, `app`, `version`, `level`, `method`, `path`, `status`,
`duration_ms`, `event`, `stop`, `reason`, `stops_api_ms`, `message`.

## The injector

`injector/install.sh` (run by `make build`, needs network once) downloads `libotelinject.so`
v0.12.0 (opentelemetry-injector) and the `opentelemetry-python-autoinstrumentation` 0.0.3 `.deb`
(opentelemetry-packaging), checksums pinned for arm64, and unpacks them into `injector/root`. `compose.enriched.yaml`
mounts that, `injector/ld.so.preload` as `/etc/ld.so.preload` and `injector/etc` as `/etc/opentelemetry/injector`.
`default_env.conf`: OTLP to the Collector, traces only (`OTEL_METRICS_EXPORTER=none`, `OTEL_LOGS_EXPORTER=none`:
logs stay in the files), `OTEL_PYTHON_LOG_CORRELATION=true` (`%(otelTraceID)s` in the log format),
`OTEL_SEMCONV_STABILITY_OPT_IN=http`, `OTEL_PYTHON_EXCLUDED_URLS=health`. Per service in compose:
the standard `OTEL_SERVICE_NAME` and `OTEL_RESOURCE_ATTRIBUTES` (service.version, deployment.environment.name); the SDK
reads them directly. (The injector also has `OTEL_INJECTOR_SERVICE_NAME` etc. for setting them from the outside.) Constraints of
the agent bundle: CPython 3.11 only, no OpenTelemetry package in the image, `urllib3==2.7.0` and `packaging==26.2`
pinned to the bundle's versions.

## Known quirks

- **CPU contention makes the incident worse.** The fallback share depends on CPU: during `make screens` it went
  from ~35 % to ~70 %, and back within ~2 min. Other containers on the same Docker VM (local Kubernetes
  clusters, other demos) make false alarms more likely: stop them before you demo. `scripts/cpu.sh` shows CPU per container.
- **Restarting the loadgen** (e.g. `make up` after `make down`) makes all phones start at once: ~1 min of
  timetable fallbacks without any 5.0 traffic. Start the lab well before the talk.
- **`make fix`**: ~30-60 s of worse numbers right after the restart (clients reconnect), then ~0 % within ~1-2 min.
- **Changing `collector/config.yaml` or `fluent-bit/*`**: compose does not notice; `scripts/lab.sh enriched restart otel-collector`.
- Jaeger keeps only the last 40000 traces (~15 min). A trace id link from older log lines finds nothing in Jaeger;
  the spans are still in OpenSearch (`traceId:<id>` on `enriched-*`).
- Dashboards takes 3-5 min to start the first time.

## Verified runs (17 Nov 2026, Docker 29.9, Apple Silicon, 10 CPUs for the VM)

`scripts/cycle.sh` runs reset -> 4 min normal -> rollout (3 min ramp) -> 7 min incident -> `make fix` -> `make reset`,
with assertions (`scripts/verify.py` checks the data itself). Logs in `runs/`.

| | cycle 1 | cycle 2 |
|---|---|---|
| before rollout: boards from timetable / board p95 | 0 % / 18-65 ms | 0 % / < 150 ms |
| alert fired after rollout start | 213 s (both labs) | 213 s (both labs) |
| incident: boards from timetable | 30-39 % | > 10 % (30-50 % typical) |
| stops-api handling p95 / rate vs baseline | 53 ms / 1.9x (until the collapse, below) | 53 ms / 1.78x classic, 1.70x enriched |
| `make fix` -> boards < 2 % (60 s window) | not reached (see below) | 62 s classic, 93 s enriched |
| failures | 4: a retry-storm collapse at 11:12 (loadgen timeout was 15 s); fixed: client timeout 60 s | 1: one 5.0 trace had 17 calls (stop near the end of the line, shorter routes; 20-26 is typical) |

Measured in cycle 2: a slow board trace `7fe81963c7f9dd25986a438950b3dfe0`: departures-api client span 1231 ms,
stops-api server span 7 ms. A 5.0 trace `dd206c0f598aa575fa20bb1f89f6f3e4` (`stop=roethenbach&include=route`):
26 client spans 41-588 ms, stops-api server spans 8-57 ms. Classic during the incident: timetable lines
`stops_api_ms` p50 701 / p95 1667, stops-api platform lookups `duration_ms` p50 6 / p95 9. No `trace_id` in
the classic files or index. CPU: the whole lab 1.1-1.3 cores normal, 1.8-2.5 cores during the incident.

`make screens` (screens/1-8): alert list; classic timetable lines; classic stops-api lines; enriched lines
with traceId; Jaeger board trace (gap); slowest requests with user_agent.original top 5 (66 % JourneyApp/5.0.0);
Jaeger 5.0 trace with its attributes; one trace id in Discover (3 log lines + 3 spans). `make walk` captures the
stills the deck uses, `make record` the same click paths as videos.

## Images

`opensearchproject/opensearch:3.9.0`, `opensearchproject/opensearch-dashboards:3.9.0`,
`otel/opentelemetry-collector-contrib:0.165.0`, `jaegertracing/jaeger:2.22.0`, `fluent/fluent-bit:5.1.5`,
`python:3.11.18-slim` (apps, loadgen). App: Flask 3.1.3, urllib3 2.7.0. Agent (bundle): opentelemetry-sdk 1.43.0,
instrumentation 0.64b0.
