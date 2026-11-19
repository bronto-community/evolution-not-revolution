---
theme: default
title: Evolution, Not Revolution
info: |
  ## Evolution, Not Revolution
  Growing observability on top of the monitoring you already have. OSMC 2026, Nuremberg.
colorSchema: light
transition: slide-left
mdc: true
class: text-left
favicon: /img/bronto-dino.png
fonts:
  sans: Radio Canada Big
  serif: Source Serif 4
  mono: Geist Mono
layout: full
---

<img src="/img/osmc-title.png" class="osmc-title" alt="Severin Neumann, Bronto. Evolution, not revolution: growing observability on top of the monitoring you already have. OSMC, Nuremberg, Nov 17-19 2026" />

<style>
.slidev-layout.full { padding: 0; }
.osmc-title { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; background: #000; }
</style>

<!--
The OSMC title card. On screen while people gather. Start at 11:15 sharp.
-->

---
layout: cover
class: text-left
---

<h1 class="title-hero"><span class="pop"><img src="/img/confetti-left.png" class="confetti c-left" />Evolution,<img src="/img/confetti-right.png" class="confetti c-right" /></span><br>not revolution</h1>

<div class="subtitle">Growing observability on top of the monitoring you already have</div>

<div class="byline">Severin Neumann · OSMC 2026 · Nuremberg</div>

<a href="https://bronto.io" target="_blank" rel="noopener" class="abs-bl m-10 brand-logo-link">
  <img src="/img/bronto-logo.webp" class="brand-logo" />
</a>

<style>
.title-hero { font-size: 4.6rem; line-height: 1.02; }
.title-hero .pop { position: relative; display: inline-block; }
.subtitle { margin-top: 1.6rem; font-size: 1.3rem; color: var(--ink-dim); }
.byline { margin-top: 0.6rem; font-family: 'Geist Mono', monospace; font-size: 0.9rem; color: var(--ink-dim); }
.confetti { position: absolute; width: 96px; height: auto; pointer-events: none; }
.c-left { top: -58px; left: -46px; }
.c-right { top: -22px; right: -92px; }
.brand-logo-link { display: inline-block; line-height: 0; transition: opacity 0.15s ease; }
.brand-logo-link:hover { opacity: 0.7; }
.brand-logo { width: 150px; height: auto; }
</style>

<!--
Title on screen. Next: who is talking.
-->

---
layout: center
---

<div class="intro">
<div class="intro-me">
<img src="/img/severin.png" class="me-photo" />
<div class="eyebrow">Who is talking</div>
<h1 class="me-name">Severin&nbsp;Neumann</h1>
<div class="me-role">Head of Community at Bronto</div>
<div class="sc-list me-list">
<span><b>OpenTelemetry</b> maintainer and member of the <b>Governance Committee</b></span>
<span><b>CNCF Ambassador</b></span>
</div>
<div class="me-handles">
<a href="https://svrnm.com" target="_blank" rel="noopener">svrnm.com</a>
<span class="dot">·</span> GitHub &amp; BlueSky <b>@svrnm</b>
<span class="dot">·</span> CNCF Slack <b>@Severin</b>
</div>
</div>
<div class="intro-co card">
<img src="/img/bronto-logo.webp" class="co-logo" />
<div class="co-claim">We build an OpenTelemetry-native backend for logs, metrics and traces.</div>
<div class="co-foot">
<a class="co-url" href="https://bronto.io" target="_blank" rel="noopener">bronto.io</a>
</div>
</div>
</div>

<style>
.intro {
  display: grid; grid-template-columns: 1.05fr 1fr; gap: 3rem;
  align-items: center; width: 100%; max-width: 54rem; margin: 0 auto;
  text-align: left;
}

/* speaker */
.eyebrow { font-family: 'Geist Mono', monospace; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.16em; color: var(--sapphire); margin-bottom: 0.7rem; }
.me-photo {
  width: 132px; height: 132px; border-radius: 50%; object-fit: cover;
  object-position: 52% 18%; margin-bottom: 1.1rem;
  box-shadow: 0 0 0 3px var(--mint), 0 0 0 6px var(--bg);
}
.me-name { font-size: 2.3rem; margin: 0; }
.me-role {
  margin-top: 0.45rem; font-family: 'Kalam', cursive;
  font-size: 1.1rem; color: var(--sapphire);
}
.me-list { margin-top: 1.3rem; }
.me-list span { font-size: 0.98rem; line-height: 1.4; }
.me-handles {
  margin-top: 1.3rem; font-family: 'Geist Mono', monospace;
  font-size: 0.72rem; color: var(--ink-dim); line-height: 1.7;
}
.me-handles b { color: var(--ink); font-weight: 600; }
.me-handles .dot { margin: 0 0.45rem; color: var(--border); }

/* company */
.intro-co { padding: 1.3rem 1.4rem 1.2rem; }
.co-logo { width: 128px; height: auto; }
.co-claim {
  margin-top: 0.9rem; font-family: 'Source Serif 4', Georgia, serif;
  font-size: 1.3rem; line-height: 1.2; max-width: 24ch;
}
.co-foot {
  display: flex; align-items: center; justify-content: space-between;
  gap: 1rem; margin-top: 1.3rem;
}
.co-url { font-family: 'Geist Mono', monospace; font-size: 0.95rem; }
</style>

<!--
Thirty seconds, no more. The OpenTelemetry hat is why I care about this topic, the Bronto hat is why I get to spend work time on it. Then straight into the cold open. No pitch: OSMC talks are educational, promotional content is not allowed.
-->

---
clicks: 2
---

<PhoneAlert :stage="$clicks" />

<!--
[0:00] You're on the platform at Plärrer. The app says your U1 to Fürth comes in two minutes.
[click] It left four minutes ago.
(Nuremberg crowd: let the laugh happen.)
[click] Somewhere, right now, at 11:16, a check goes critical: 38% of departures come from the timetable instead of live data.
You're on call. Let's see what you have.
-->

---
layout: center
---

<SectionCard kicker="Act one" title="Monitoring works" art="/img/dino-blocks.png" />

<!--
[0:40] Short. This is their world, and we show it working.
-->

---
clicks: 2
---

# The check, the graph, the logs

<ClassicTools :stage="$clicks" />

<!--
[1:00] Slide only, the lab comes later.
The check: stale-departures is critical. Everything else is green: the feed is fresh, the box is fine, the APIs answer. That already rules a lot out.
[click] The graph: only U1 climbs. U2 and U3 are flat. It started around 11:05.
[click] The logs: tail and grep. Timeouts, on U1.
Every one of these was built by someone who learned something in an earlier incident. That's good work.
-->

---
clicks: 3
---

# Found it

<IncidentChat :stage="$clicks" />

<!--
[3:00] The logs point at stops-api, and someone on the team has seen this before.
[click] Sam: stops-api gets slow when it's busy, give it more replicas.
[click] Alex scales it from 2 to 4.
[click] Nine minutes later the check is green again. Incident closed, postmortem written: "stops-api under-provisioned".
Experience plus the tools we have, and it took 15 minutes. That's a good result.
-->

---
layout: center
class: text-center
---

<div class="statement-big">This works.<br><em>There's nothing wrong with it.</em></div>

<!--
[4:30] Say it and mean it. Most people here run setups that have worked for ten or twenty years.
If your checks and graphs answer the questions you get asked, you're fine.
-->

---
layout: center
class: text-center
---

<div class="fake-end">
  <h1>Thank you!</h1>
  <div class="dim mt-4 text-xl">End of talk. Questions?</div>
  <div v-click class="or-does-it">…or does it?</div>
</div>

<style>
.fake-end h1 { font-size: 4.4rem; }
.or-does-it { margin-top: 3rem; font-family: 'Kalam', cursive; font-size: 2.6rem; color: var(--claim); transform: rotate(-3deg); }
</style>

<!--
[5:00] Pause, long enough that a few people reach for their bags.
[click] …or does it?
-->

---
layout: center
---

<SectionCard kicker="Act two" title="…or does it?" art="/img/dino-scientist.png" />

---
clicks: 2
---

# Two weeks later, the same check

<ClassicTools :stage="$clicks" :round="2" />

<!--
[6:00] Two weeks later, evening rush, 18:16. The same check goes critical, this time at 14%.
Everything else is green.
[click] The graph: every line is a bit worse, and none of them stands out. It goes up, down, up again.
[click] The logs: 41,827 warnings across all services. Retries, a slow query, messages out of order. None of them points anywhere in particular.
Let the blinking cursor sit for a second.
-->

---
clicks: 2
---

# Same people, no idea

<div class="chat-row">
  <IncidentChat :round="2" :auto="1400" :run="$clicks >= 1" />
  <div class="uu" :class="{ on: $clicks >= 2 }">
    <span class="arrow">←</span>
    this is what people call<br>an <b>unknown unknown</b>
  </div>
</div>

<!--
[6:45] Same chat channel, same two people as last time.
[click] The messages come in on their own:
Alex: critical again, all lines this time. Sam: stops-api looks fine, it's not that. Alex: 41k warnings, where do I even start? Sam: no idea, restart departures-api and see?
Nobody has seen this one before. The tools tell us that something is wrong, but not where and not why.
[click] This is what people call an unknown unknown. And now I have to take a short detour.
-->

---
clicks: 2
---

# Detour: the bikeshed

<Bikeshed :stage="$clicks" />

<!--
[7:30] "Unknown unknowns" is one of those terms. Ask five people and you get five definitions.
Same with "what is observability", "where does it sit next to monitoring", "how many pillars". We could spend the whole 45 minutes in front of this shed. People do.
[click] There's a word for that. Parkinson, 1957: a committee approves a nuclear power plant in minutes and then argues for an hour about the bike shed, because everyone has an opinion on bike sheds.
[click] Not today. It doesn't help Alex and Sam.
-->

---
clicks: 3
---

# Hard problems keep getting harder

<EvolutionChart :stage="$clicks" />

<div class="evo-cap" :class="{ on: $clicks >= 3 }">So the way we catch and fix them has to keep <b>evolving</b>.</div>

<style>
.evo-cap { margin-top: 0.2rem; text-align: center; font-family: 'Source Serif 4', Georgia, serif; font-size: 1.6rem; opacity: 0; transition: opacity 0.4s ease; }
.evo-cap.on { opacity: 1; }
.evo-cap b { color: var(--sapphire); }
</style>

<!--
[8:15] What doesn't change: there were always hard problems.
[click] Our systems: one server, then VMs and the cloud, then containers and microservices. Now AI writes and ships a good part of the code, faster than any of us can review it. Every step makes the problems harder.
[click] And every time, the way we catch and fix problems moved too. Logs (syslog, early 80s), checks (SNMP, 1988), graphs (MRTG, 1995). Then traces (Dapper paper, 2010). OpenTelemetry in 2019, stable semantic conventions so the data means the same thing everywhere (HTTP, late 2023), and now AI helping with the investigation.
[click] Alex and Sam are here: logs, checks and graphs. Tools from the last century, and they worked for the systems of that time. The system kept growing, their practice didn't. That's the gap.
So the way we catch and fix problems has to keep evolving.
The years are rough anchors; the sources are in the comment at the top of components/EvolutionChart.vue.
-->

---
layout: center
class: text-center
---

<div class="statement-big">The usual pitch: a revolution.</div>
<div class="mt-4 text-xl dim">Rip out the old tools, buy the new thing, start over.</div>

<div v-click class="evo-no"><span class="pop"><img src="/img/confetti-left.png" class="confetti c-left" />Evolution,<img src="/img/confetti-right.png" class="confetti c-right" /></span><br>not revolution.</div>

<style>
.evo-no { margin-top: 3.6rem; font-family: 'Source Serif 4', Georgia, serif; font-size: 4rem; line-height: 1.05; color: var(--sapphire); }
.evo-no .pop { position: relative; display: inline-block; }
.evo-no .confetti { position: absolute; width: 84px; height: auto; pointer-events: none; }
.evo-no .c-left { top: -50px; left: -46px; }
.evo-no .c-right { top: -20px; right: -82px; }
</style>

<!--
[9:30] So the system outgrew the practice. The usual pitch at this point is a revolution: throw out Nagios and the log server, buy the new platform, start over.
[click] I'm arguing for the opposite. Evolution, not revolution. (The title, said out loud for the first time.)
-->

---
layout: center
class: text-center
---

<div class="statement-big dim" style="font-size: 1.8rem; max-width: none; margin-bottom: 2.4rem">Observability: <i>systematically</i> making your system<br>more observable <span class="sic">(sic)</span>.</div>

<style>
.sic { font-family: 'Kalam', cursive; font-size: 1.3rem; }
</style>

<div v-click class="formula small">
  <span class="f-mon">Monitoring</span>
  <span class="f-op">+</span>
  <span class="f-ctx">context enrichment</span>
  <span class="f-op">=</span>
  <span class="f-obs">observability</span>
</div>

<div v-click class="mt-10 text-xl dim">Keep what you have. Add the context that connects it.</div>

<!--
[10:00] Read the top line with a straight face. Yes, it's circular, on purpose. The word that matters is "systematically": a practice you repeat, not a product you buy.
[click] The formula is the method. [click] This is the "systematic" part, not a second definition. Keep the monitoring, add context. Let it sit for a moment.
-->

---
layout: center
---

<SectionCard kicker="Another image" title="Grow the villages together" art="/img/dino-space.png" />

---
clicks: 4
---

# Neighbouring villages

<Villages :stage="$clicks" />

<div class="vil-cap">
  <span v-if="$clicks === 0"><i class="chip">today</i>Some telemetry is already connected: within one host, one service, one tool.</span>
  <span v-else-if="$clicks === 1"><i class="chip">today</i>Across them, you match by hostname and timestamp. Slow, but it works.</span>
  <span v-else-if="$clicks === 2"><i class="chip add">+ shared attributes</i>Add what's missing, and name it the same everywhere.</span>
  <span v-else-if="$clicks === 3"><i class="chip add">+ traces &amp; correlation</i>Follow one request, and carry its context into every log line.</span>
  <span v-else><i class="chip eq">= observability</i>You kept every tool you had. Now they're connected.</span>
</div>


<!--
[15:00] The picture for the rest of the talk. Villages. Inside each one, everyone knows everyone: some checks, graphs and logs already fit together. Your villages look different from mine. Doesn't matter. Look at the roads.
[click] Between them: dirt tracks. Hostname, timestamp. You can walk over and answer some questions, slowly. That's where Alex and Sam are.
[click] Enrichment: the same street names everywhere. service.name means the same thing in every village, so the tracks become roads and every village is reachable.
[click] Then a train line. A trace follows one passenger, one request, through every village. The stations are the trace_id in your log lines.
Local hook: the first German railway ran from Nuremberg to Fürth in 1835. Today the U1 does.
[click] And over time the villages grow into one town. The old centres are still there. Nobody tore down Fürth. Evolution, not revolution.
-->

---
clicks: 1
---

# Building the roads and the railway

<div class="build">
  <div class="card ok">
    <div class="bchip add">+ shared attributes</div>
    <h4>Add what's missing</h4>
    <p>Which service, which version, which line? A lot of telemetry doesn't say. Add <code>service.name</code>, <code>service.version</code>, <code>transit.line</code>.</p>
    <h4>Follow a standard</h4>
    <div class="names">
      <div><code>host</code> <code>hostname</code></div><i>→</i><div><code>host.name</code></div>
      <div><code>svc</code> <code>app_name</code> <code>service</code></div><i>→</i><div><code>service.name</code></div>
    </div>
    <a class="tl-url" href="https://opentelemetry.io/docs/concepts/semantic-conventions/" target="_blank" rel="noopener">opentelemetry.io/docs/concepts/semantic-conventions</a>
  </div>
  <div v-click class="card new">
    <div class="bchip add">+ traces &amp; correlation</div>
    <h4>Add traces</h4>
    <p>A trace follows one request through every service it touches. Zero-code instrumentation adds it without changing the app.</p>
    <h4>Propagate the context</h4>
    <p>Every hop passes the trace context on, in the <code>traceparent</code> header. Put the <code>trace_id</code> into the log format you already use, and every log line belongs to a request.</p>
  </div>
</div>


<!--
[17:00] How do we build the roads and the railway?
Roads: shared attributes. Two parts. First, add what's missing: a lot of telemetry doesn't say which service, version or line it belongs to. Second, name it the same way everywhere. Your logs say host, your metrics say hostname. Don't invent your own names: OpenTelemetry's semantic conventions already define them. That alone lets one query reach logs, metrics and checks.
[click] Railway: traces and correlation. A trace follows one request through every service, and zero-code instrumentation adds it without app changes. But the trace is only half of it. The context has to travel: every hop passes it on in the traceparent header, and once the trace_id is in your log lines, every log line belongs to a request. That's context propagation, and it's useful beyond tracing.
Order matters: roads first, then the railway.
-->

---
clicks: 1
---

# What we build

<LabMap :stage="$clicks" brand />

<!--
[19:00] The lab, with the stack most of us have. The apps: departures-api calls stops-api. Icinga checks them and alerts. Prometheus scrapes them and draws the graphs. A log shipper puts the logs into central storage. All of that stays.
[click] What we add, in green. The checks and the graphs keep running, unchanged. A Collector reads the same log files the log shipper reads, and the apps get zero-code traces and a trace_id in the log format they already use. The Collector gives logs and traces the same names and sends them over OTLP to the backend. In the lab that's OpenSearch for search and Jaeger for the trace view, and today's log shipper (Fluent Bit) keeps feeding the classic index next to it. It can be any backend that speaks OTLP. (The lab leaves the checks and graphs out: the incident is found in logs and traces.)
Next: the "before".
-->

---
layout: center
class: text-center
---

<div class="live-cue">The lab · before</div>
<div class="statement-big">What we have</div>
<div class="mt-4 text-xl dim">The incident, in the tools we already run.</div>

<!--
[20:00] The lab from the repo, during the incident. Each click is one step I'd take. The screens are real stills from the lab (`make walk`, lab/scripts/ui/walk.js). If anyone wants to see it live, the lab runs on my laptop afterwards.
-->

---
layout: full
clicks: 1
---

<WalkShot step="b1-alert" :spot="($clicks >= 1 ? [{x:51,y:25,w:25,h:19},{x:51,y:47,w:37,h:8}] : [])" :zoom="null" at="tr" :width="46"
  caption="The alert: more than 5 % of the departure boards show the printed timetable." />

<!--
The alert, as OpenSearch shows it. [click] Trigger: more than 5 % of the boards from the timetable, since 16:43 in the lab, 18:16 in our story. The monitor reads classic-logs: our logs, as we have them today.
-->

---
layout: full
clicks: 2
---

<WalkShot step="b2-timetable" :spot="($clicks === 1 ? [{x:22,y:24,w:77,h:27}] : [])" :zoom="($clicks >= 2 ? {x:21,y:56,w:44,h:28} : null)" at="tr" :width="56"
  caption="departures-api: served from timetable, at every stop. Its call to stops-api took 600 to 1,200 ms." />

<!--
Discover, classic-logs-*, query event:served_from_timetable. [click] It started a few minutes ago, out of nowhere. [click] Every stop, every board. And the field says it: stops_api_ms, 600, 700, 1,100. 'stops-api is slow.'
-->

---
layout: full
clicks: 1
---

<WalkShot step="b3-stops-api" :spot="[]" :zoom="($clicks >= 1 ? {x:20,y:56,w:44,h:38} : null)" at="tr" :width="56"
  caption="stops-api, its own log: every call answered in under 50 ms." />

<!--
Same Discover, query app:stops-api. That's the other team's service. [click] Everything under 50 ms: the route lookups around 45, and /stops/<stop>/platforms, the call our boards make, 5 to 10 ms. 'Not us,' says the other team. And they're right, by their logs. Two teams' logs, contradicting each other.
-->

---
layout: full
clicks: 2
---

<WalkShot step="b4-dead-end" :spot="($clicks >= 2 ? [{x:0.5,y:29,w:19.5,h:60},{x:57.5,y:57,w:26,h:42}] : $clicks >= 1 ? [{x:0.5,y:29,w:19.5,h:60}] : [])" :zoom="null" at="tr" :width="46"
  caption="Every request: GET /departures 200. No client, no query string, nothing that connects the two lines." />

<!--
What else do we have? [click] The fields in the line: app, method, path, status, duration_ms, host, level, version. [click] All 200, all /departures, the same for everybody. No way to tell requests apart, no way to connect our line to the stops-api line it caused. Dead end. There's data everywhere. What's missing is the way from one piece to the next.
-->

---
clicks: 2
---

# Add attributes

<div class="cfg">
  <div class="cfg-h"><b>departures-api.log</b><span>unchanged</span></div>
  <div class="logmap" :class="{ on: $clicks >= 2 }">
    <span class="tk"><code>departures-01</code><em>host.name</em></span>
    <span class="tk"><code>departures-api</code><em>service.name</em></span><span class="tk"><code>[3.1.0]</code><em>service.version</em></span>
    <span class="tk plain"><code>: INFO</code><em>&nbsp;</em></span>
    <span class="tk"><code>method=GET</code><em>http.request.method</em></span>
    <span class="tk"><code>path=/departures</code><em>url.path</em></span>
    <span class="tk"><code>status=200</code><em>http.response.status_code</em></span>
  </div>
</div>

<div v-click="1" class="cfg mt-4">
  <div class="cfg-h"><b>collector/config.yaml</b><span>excerpt · the Collector reads the same log files</span></div>
<pre class="diff"><span class="ctx">file_log:</span><span class="ctx">  operators:</span><span class="add">    - { type: move, from: attributes.host,    to: '<b>resource["host.name"]</b>' }</span><span class="add">    - { type: move, from: attributes.app,     to: '<b>resource["service.name"]</b>' }</span><span class="add">    - { type: move, from: attributes.version, to: '<b>resource["service.version"]</b>' }</span><span class="ctx">transform/logs:</span><span class="add">    - set(attributes["<b>http.request.method</b>"], attributes["method"])</span><span class="add">    - set(attributes["<b>url.path</b>"], attributes["path"])</span><span class="add">    - set(attributes["<b>http.response.status_code</b>"], Int(attributes["status"]))</span></pre>
</div>

<div v-click="2" class="dz-note">The names come from the <a href="https://opentelemetry.io/docs/concepts/semantic-conventions/" target="_blank" rel="noopener">OpenTelemetry semantic conventions</a>, the same names the traces will use.</div>

<style>
.logmap em { visibility: hidden; }
.logmap.on em { visibility: visible; }
.logmap code { transition: background 0.3s; }
.slidev-layout .logmap code { font-size: 0.76rem; }
.logmap { gap: 0 0.2rem; }
.logmap:not(.on) .tk:not(.plain) code { background: transparent; color: var(--ink-dim); }
</style>

<!--
[21:00] Step one: attributes. And it's the Collector we promised on the last slide.
This is the log line departures-api writes today. We don't touch it.
[click] The Collector reads the same log files the log shipper reads. A few lines of config: who wrote the line (host, app, version) become resource attributes, and the fields in the line get their standard names.
[click] Now the line says host.name, service.name, service.version, http.request.method, url.path, http.response.status_code. Those names aren't ours, they're from the OpenTelemetry semantic conventions. The traces on the next slide use exactly the same names, and that's what lets one filter work on both.
-->

---
clicks: 2
---

# Add traces

<div class="dz two">
  <div class="cfg">
    <div class="cfg-h"><b>/etc/ld.so.preload</b><span>new file</span></div>
<pre class="diff"><span class="add"><b>/usr/lib/opentelemetry/injector/libotelinject.so</b></span></pre>
  </div>
  <div class="cfg-side">The OpenTelemetry Injector: zero-code instrumentation for every Java, Node.js, .NET and Python process on the box.</div>
</div>

<div v-click="1" class="cfg mt-4">
  <div class="cfg-h"><b>/etc/opentelemetry/injector/injector.conf</b><span>Python is opt-in</span></div>
<pre class="diff"><span class="add">python_auto_instrumentation_agent_path_prefix=<b>/usr/lib/opentelemetry/python</b></span></pre>
</div>

<div v-click="2" class="cfg mt-4">
  <div class="cfg-h"><b>departures-api</b><span>environment · same image, same start command</span></div>
<pre class="diff"><span class="ctx">command: python departures_api.py</span><span class="add">OTEL_SERVICE_NAME: <b>departures-api</b></span><span class="add">OTEL_RESOURCE_ATTRIBUTES: <b>service.version=3.1.0,deployment.environment.name=production</b></span></pre>
</div>

<!--
[23:00] Step two: traces. A trace follows one request through every service, and the context travels with it in the traceparent header, from departures-api to stops-api.
On a box you don't change the app, not even the start command. The OpenTelemetry Injector is one line in /etc/ld.so.preload, and it loads the zero-code instrumentation into every supported process.
[click] Python is opt-in: one more line in the injector's config. (In the lab: injector v0.12.0 with the Python agent package.)
[click] And the app gets the same names as its log lines: service name, version, environment. The standard OTel environment variables, the SDK reads them, with or without the injector. Same image, same start command as the classic lab. (The injector also has OTEL_INJECTOR_SERVICE_NAME and friends, for when someone sets them from the outside, e.g. per host.)
-->

---
clicks: 2
---

# Add the trace_id to the logs

<div class="cfg">
  <div class="cfg-h"><b>log format</b><span>the one the team already has</span></div>
<pre class="diff"><span class="ctx">%(asctime)s %(hostname)s %(app)s[%(version)s]: %(levelname)s %(message)s</span><span class="add">  <b>trace_id=%(otelTraceID)s span_id=%(otelSpanID)s</b></span></pre>
</div>

<div v-click="1" class="cfg mt-4">
  <div class="cfg-h"><b>default_env.conf</b><span>the injector's environment for every app</span></div>
<pre class="diff"><span class="add"><b>OTEL_PYTHON_LOG_CORRELATION=true</b></span></pre>
</div>

<div v-click="2" class="cfg mt-4">
  <div class="cfg-h"><b>departures-api.log</b><span>the result</span></div>
<pre class="diff"><span class="ctx">departures-01 departures-api[3.1.0]: INFO method=GET path=/departures status=200</span><span class="add">  <b>trace_id=ab31f8e4618884698987516b9709f7e8</b> span_id=4c4f0c3b05515ece</span></pre>
</div>

<div v-click="2" class="dz-note">Other languages: Java agent → MDC · Node.js → pino, winston · .NET → ILogger scopes</div>

<!--
[24:30] Step three: put the trace_id into the log format we already have. Two more fields at the end of the line.
[click] One environment variable turns on the logging instrumentation that fills them in.
[click] The same log line as before, now with the trace_id. Every log line belongs to a request, and the Collector turns it into the log record's trace id, the same field the spans have. Other languages do it differently: Java's agent puts it into the MDC, Node.js has instrumentations for pino and winston, .NET uses ILogger scopes.
-->

---
layout: center
class: text-center
---

<div class="live-cue">The lab · after</div>
<div class="statement-big">Same incident, with context</div>
<div class="mt-4 text-xl dim">From the alert to the root cause, one hop at a time.</div>

<!--
[26:00] Same moment, same incident, same moves. Nothing in the app changed, not even the start command.
-->

---
layout: full
clicks: 0
---

<WalkShot step="a1-alert" :spot="[]" :zoom="null" at="tr" :width="46"
  caption="Same moment, same alert. Now on the enriched data." />

<!--
The same alert, now on enriched-logs.
-->

---
layout: full
clicks: 2
---

<WalkShot step="a2-traceid" :spot="($clicks >= 1 ? [0] : [])" :zoom="($clicks >= 2 ? {x:50,y:56,w:50,h:26} : null)" at="tr" :width="54"
  caption="The same log lines. Now each one carries a traceId." />

<!--
Discover, enriched-*, query attributes.event.name:served_from_timetable. [click] Same lines, same stops_api_ms. One new column: traceId. [click] And it's a link. Click one.
-->

---
layout: full
clicks: 2
---

<WalkShot step="a3-board-trace" :spot="($clicks >= 1 ? [0, 1] : [])" :zoom="($clicks >= 2 ? {x:80,y:30,w:20,h:12} : null)" at="bl" :width="52"
  caption="One board request: our call to stops-api takes 1.2 s. stops-api itself: 9.5 ms, at the very end." />

<!--
Jaeger opens the trace. [click] departures-api, our call to stops-api, 1.2 s. And inside it, stops-api's own span. [click] 9.5 ms, at the very end. The time is lost before the call even leaves us: waiting for a connection in our pool of 5. That's why stops-api looked fine. So who holds the connections?
-->

---
layout: full
clicks: 1
---

<WalkShot step="a4-scatter" :spot="($clicks >= 1 ? ['dots'] : [])" :zoom="null" at="tr" :width="46"
  caption="Who holds the connections? All departures-api requests, last 5 minutes. Dot size = number of spans." />

<!--
Jaeger Search: departures-api, GET /departures, last 5 minutes. Most dots are tiny: 3 spans, a request and its one call. [click] A few are big. Click the biggest.
-->

---
layout: full
clicks: 2
---

<WalkShot step="a5-app5-trace" :spot="($clicks >= 2 ? [{x:24,y:31,w:76,h:68}] : $clicks >= 1 ? [{x:44,y:12.5,w:9,h:4}] : [])" :zoom="null" at="tr" :width="46"
  caption="One of the big ones: 53 spans. 26 calls to stops-api, in parallel, all through our 5 connections." />

<!--
[click] 53 spans. [click] 26 calls to stops-api, all at once, each one waiting for one of the 5 connections. Every request like this blocks the pool for close to a second. The boards queue behind it.
-->

---
layout: full
clicks: 2
---

<WalkShot step="a6-attributes" :spot="($clicks >= 1 ? [0, 1] : [])" :zoom="($clicks >= 2 ? {x:24.5,y:82,w:44,h:15} : null)" at="tr" :width="60"
  caption="Who sends it? JourneyApp 5.0, with include=route. Recorded by the zero-code instrumentation, not by app code." />

<!--
Click the top span, Attributes. [click] user_agent.original: JourneyApp/5.0.0. url.query: stop=...&include=route. [click] Another company's app, rolling out since a few minutes, polls like 4.0 did, but asks for the route. Each of those requests: 26 calls. Nobody here deployed anything. The Python agent recorded these; no code changed. Mitigation: raise the pool (in the lab: make fix), then talk to the vendor.
-->

---
layout: full
clicks: 1
---

<WalkShot step="a7-one-trace" :spot="($clicks >= 1 ? [{x:21,y:57,w:78.5,h:42.5}] : [])" :zoom="null" at="tr" :width="46"
  caption="One traceId in OpenSearch: that request's log lines and spans, both services, one list." />

<!--
Optional, if time. Back in OpenSearch: query traceId:<id>. [click] The request's log lines from both services and its spans, together. The logs we always had, now connected.
-->

---
layout: center
class: text-center
---

<div class="statement-big">And now ask an agent</div>
<div class="mt-4 text-xl dim">Same question, without and with context.</div>

<!--
[33:00] Recorded: Claude Code in a terminal against a scripted model (agent-demo/). The tool results are real data from the lab.
Same prompt twice: "The departure boards alert fired. Find out why."
Classic (logs only): it finds the contradiction (stops_api_ms ~1 s vs stops-api's own ~50 ms at most) and stops honestly at what the data can't tell.
Enriched: it opens a slow board trace, sees the wait for a connection, finds the 5.0 requests with the most calls, and names the root cause with trace ids as evidence.
The videos are on the next two slides. Each one starts on the next click; going back to the slide rewinds it.
-->

---
layout: full
class: agent-vid
---

<div class="vid-cue">Logs only</div>
<SlidevVideo v-click autoplay autoreset="slide" print-poster="/video/agent-classic-end.jpg" class="agent-video">
  <source src="/video/agent-classic.mp4" type="video/mp4" />
</SlidevVideo>

<!--
[34:00] 60 s. Same prompt. It finds the contradiction: departures-api says the stops-api call takes ~740 ms, stops-api says it answers everything within ~53 ms (p95). No errors, no deploy, one version. Then it stops honestly: the logs can't say where the time goes or who is calling.
-->

---
layout: full
class: agent-vid
---

<div class="vid-cue good">With context</div>
<SlidevVideo v-click autoplay autoreset="slide" print-poster="/video/agent-enriched-end.jpg" class="agent-video">
  <source src="/video/agent-enriched.mp4" type="video/mp4" />
</SlidevVideo>

<!--
[35:00] 74 s. Same prompt, same model. Fallback line → traceId → board trace: 982 ms client span, 6 ms stops-api span, so it waits for one of the 5 connections. Then the human path: traces sorted by span count, the top ones are all JourneyApp/5.0.0 with include=route, 53 spans. Root cause, evidence with trace ids, mitigation.
-->

---
clicks: 2
---

# 18:16, again

<div class="chat-row">
  <IncidentChat :round="3" :auto="1600" :run="$clicks >= 1" />
  <div class="uu good" :class="{ on: $clicks >= 2 }">
    <span class="arrow">←</span>
    same people, same checks.<br>now they know <b>where</b><br>and <b>why</b>
  </div>
</div>

<!--
[36:00] Back to the evening rush. Same check, same two people, same chat.
[click] This time: Alex opens one slow board request as a trace. Our call to stops-api takes 950 ms, but stops-api's own part of that call takes 6 ms: the time is lost before the call leaves departures-api, waiting for a free connection. That's why stops-api looked fine. Sam: who holds the connections? Requests from JourneyApp 5.0, the journey-planner app, with include=route, 26 calls each, holding the 5 connections, rolling out since 17:30. Raise the pool, call the vendor, check goes green at 18:27. Nobody here deployed anything.
[click] Same people, same checks. They didn't get smarter. Their telemetry got connected.
-->

---
layout: center
---

<SectionCard kicker="Act four" title="Next stop" art="/img/dino-van.png" />

---
clicks: 1
---

# What we added, and what's next

<LabMap :stage="1 + $clicks" brand />

<div class="vil-cap" style="margin-top: 1.1rem">
  <span v-if="$clicks === 0"><i class="chip add">added</i>A Collector, the same names everywhere, traces. The checks and graphs kept running the whole time.</span>
  <span v-else><i class="chip eq">next</i>The app speaks OTLP itself and the log files can go. The checks and the graphs stay.</span>
</div>

<!--
[38:00] What did we add? A Collector next to what we already run. The same names on every signal. Traces, without touching the code, and the trace_id in the log format we already had. Each step on its own is worth it and fits a normal sprint. The checks and graphs kept running through all of it.
[click] What's next: some things get replaced, some stay. The app speaks OTLP itself with the OTel SDK: metrics, logs and traces, with the trace context built in. That replaces the log files lane: no more parsing lines, no more appending trace_id to a format. Icinga and Prometheus stay: Icinga checks from the outside whether the boards answer, Prometheus has years of graphs and alert rules that work. They keep their value, and nothing forces you to move them. If you want their data next to the rest, they can feed the same pipeline (dashed): the Collector can scrape the same Prometheus endpoints, and Icinga's check results can go out as metrics too. Optional, not a migration. And because everything the app sends goes out as OTLP, the backend is a choice you can change later. One backend for all signals is the best case, for example Bronto.
-->

---
layout: center
class: text-center
---

<Villages :stage="4" />

<div class="formula small mt-4">
  <span class="f-mon">Monitoring</span>
  <span class="f-op">+</span>
  <span class="f-ctx">context enrichment</span>
  <span class="f-op">=</span>
  <span class="f-obs">observability</span>
</div>

<!--
[40:30] Back to the picture. Your monitoring now answers why, and not only what.
-->

---
layout: center
class: text-center
---

<div class="thanks">
  <div class="thanks-left">
    <h1 class="thanks-title">Thank you</h1>
    <div class="thanks-mail">severin@bronto.io</div>
    <div class="thanks-links">
      <div class="tl">
        <span class="tl-label">Run the lab yourself</span>
        <a class="tl-url" href="https://github.com/bronto-community/evolution-not-revolution" target="_blank" rel="noopener">github.com/bronto-community/evolution-not-revolution</a>
      </div>
      <QrCode url="https://github.com/bronto-community/evolution-not-revolution" :size="104" />
    </div>
  </div>

  <ThanksBronto>What does <em>your</em> monitoring not answer yet?</ThanksBronto>
</div>

<style>
.thanks { display: flex; align-items: center; justify-content: center; gap: 3.5rem; text-align: left; }
.thanks-title { font-size: 4rem; line-height: 1.05; }
.thanks-mail { margin-top: 1.2rem; font-family: 'Geist Mono', monospace; font-size: 1.05rem; color: var(--ink-dim); }
.thanks-links { display: flex; align-items: center; gap: 1.4rem; margin-top: 1.8rem; }
.tl { display: flex; flex-direction: column; align-items: flex-start; gap: 0.1rem; }
.tl-label { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: var(--ink-dim); }
.thanks em { font-style: italic; color: var(--sapphire); }
</style>

<!--
[41:00] Q&A. The repo has the deck, the lab and the agent demo.
-->
