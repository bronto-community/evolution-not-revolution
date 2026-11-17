<script setup lang="ts">
// The lab before the demo, as lanes: one lane per signal.
// stage 0 = what we have: the transit app, and Icinga / Prometheus / central logs next to it.
// stage 1 = what we add: a new traces lane; the log files and the traces flow into the Collector,
//           which sends them over OTLP to the backend. Icinga and Prometheus keep running unchanged.
// stage 2 = what's next: some things are replaced, some stay. The app speaks OTLP itself (OTel SDK: metrics,
//           logs, traces), which replaces the log files lane. Icinga and Prometheus stay, they keep their value.
// Icons match the houses in the villages picture (check, graph, log line).
import { useId } from 'vue'
withDefaults(defineProps<{ stage?: number }>(), { stage: 0 })
// marker ids per instance: the deck has two LabMaps, url(#id) would hit the hidden one
const uid = useId()
const mk = (c: string) => `url(#${uid}-${c})`

const lanes = [
  { y: 60, name: 'Icinga', icon: 'check', sig: ['M'], keep: true },
  { y: 140, name: 'Prometheus', icon: 'graph', sig: ['M'], keep: true },
  { y: 220, name: 'Log files', icon: 'log', sig: ['L'] },
  { y: 300, name: 'Traces', icon: 'trace', sig: ['T'], added: true },
]
const H = 60
const ALL = ['M', 'L', 'T']
// stage 2: the Collector (and the backend) grow to take every lane, Icinga and Prometheus can feed it too
const box = (st: number) => st >= 2 ? { y: 60, h: 300, mid: 210 } : { y: 220, h: 140, mid: 290 }
// stage 2: the SDK lane carries all signals; the log files lane is replaced by it
const sigs = (l: { added?: boolean; sig: string[] }, st: number) => l.added && st >= 2 ? ALL : l.sig
// badges centred on a wire from x0 to x1
const badgeX = (n: number, i: number, mid: number) => mid + (i - (n - 1) / 2) * 23
</script>

<template>
  <svg class="lab" viewBox="0 0 900 404" :data-stage="stage" role="img"
       :aria-label="stage >= 2 ? 'A transit app; Icinga and Prometheus stay and can also send their metrics to the Collector, the log files are replaced by the OTel SDK, which sends metrics, logs and traces through the Collector over OTLP to one backend' : 'A transit app with Icinga, Prometheus and log files; Icinga and Prometheus stay unchanged, the log files and new traces flow into a Collector and over OTLP into a backend for logs and traces'">
    <defs>
      <marker :id="`${uid}-g`" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
        <path d="M0 0 L10 5 L0 10 Z" fill="#A9A196" />
      </marker>
      <marker :id="`${uid}-n`" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
        <path d="M0 0 L10 5 L0 10 Z" fill="#1E8A5F" />
      </marker>
    </defs>

    <!-- column headers -->
    <text x="20" y="34" class="hd">What we have</text>
    <line x1="20" x2="500" y1="44" y2="44" class="hd-rule" />
    <g class="add">
      <text x="580" y="34" class="hd n">What we add</text>
      <line x1="580" x2="890" y1="44" y2="44" class="hd-rule n" />
    </g>

    <!-- the app -->
    <rect x="20" y="60" width="190" height="300" rx="14" class="have" />
    <text x="115" y="120" class="bt">transit app</text>
    <rect x="38" y="164" width="154" height="46" rx="9" class="svc" /><text x="115" y="193" class="st">departures-api</text>
    <rect x="38" y="244" width="154" height="46" rx="9" class="svc" /><text x="115" y="273" class="st">stops-api</text>
    <path d="M115 210 V244" class="call" />

    <!-- lanes -->
    <g v-for="l in lanes" :key="l.name" :class="[l.added ? 'add' : 'old', { gone: stage >= 2 && !l.added && !l.keep }]">
      <path :d="`M210 ${l.y + H / 2} H294`" :class="l.added ? 'flow' : 'link'" :marker-end="l.added ? mk('n') : mk('g')" />
      <g v-for="(sg, i) in sigs(l, stage)" :key="'in' + sg"
         :transform="`translate(${badgeX(sigs(l, stage).length, i, 250)} ${l.y + H / 2})`" class="sig" :class="{ grey: !l.added }">
        <circle r="11" /><text y="5">{{ sg }}</text>
      </g>
      <rect x="300" :y="l.y" width="200" :height="H" rx="10" :class="l.added ? 'new' : 'have'" />
      <g :transform="`translate(332 ${l.y + H / 2})`">
        <g v-if="l.icon === 'check'"><circle r="12" class="i-check" /><path d="M-5 0 L-1.5 4 L6 -4" class="i-tick" /></g>
        <path v-else-if="l.icon === 'graph'" d="M-13 9 L-6 0 L0 4 L7 -7 L13 -3" class="i-graph" />
        <path v-else-if="l.icon === 'log'" d="M-12 -7 H12 M-12 0 H8 M-12 7 H11" class="i-log" />
        <g v-else class="i-trace"><rect x="-13" y="-9" width="22" height="5" rx="2" /><rect x="-7" y="-2" width="12" height="5" rx="2" /><rect x="-1" y="5" width="14" height="5" rx="2" /></g>
      </g>
      <text x="358" :y="l.y + H / 2 + 7" class="bt left">{{ l.added && stage >= 2 ? 'OTel SDK' : l.name }}</text>
      <text v-if="l.keep && stage < 2" x="512" :y="l.y + H / 2 + 5" class="sub left add">unchanged</text>
      <text v-if="l.keep && stage >= 2" x="538" :y="l.y + H / 2 - 18" class="sub stays">stays</text>
      <!-- stage 2: optional, the checks and graphs can also send their metrics on -->
      <g v-if="l.keep && stage >= 2">
        <path class="flow opt" :d="`M500 ${l.y + H / 2} H574`" :marker-end="mk('n')" />
        <g :transform="`translate(538 ${l.y + H / 2})`" class="sig"><circle r="11" /><text y="5">M</text></g>
      </g>
      <path v-if="!l.keep" class="flow add" :d="`M500 ${l.y + H / 2} H574`" :marker-end="mk('n')" />
      <g v-if="!l.keep" class="add">
        <g v-for="(sg, i) in sigs(l, stage)" :key="sg"
           :transform="`translate(${badgeX(sigs(l, stage).length, i, 538)} ${l.y + H / 2})`" class="sig">
          <circle r="11" /><text y="5">{{ sg }}</text>
        </g>
      </g>
    </g>

    <!-- what we add -->
    <g class="add">
      <rect x="580" :y="box(stage).y" width="120" :height="box(stage).h" rx="14" class="new" />
      <text x="640" :y="box(stage).mid - 8" class="bt">Collector</text>
      <text x="640" :y="box(stage).mid + 16" class="sub">same names</text>
      <text x="640" :y="box(stage).mid + 33" class="sub">everywhere</text>

      <path :d="`M700 ${box(stage).mid} H746`" class="flow big" :marker-end="mk('n')" />
      <text x="725" :y="box(stage).mid - 18" class="proto">OTLP</text>
      <g v-for="(sg, i) in (stage >= 2 ? ALL : ['L', 'T'])" :key="'o' + sg" :transform="`translate(725 ${box(stage).mid + (stage >= 2 ? 28 : 28) + i * 27})`" class="sig"><circle r="11" /><text y="5">{{ sg }}</text></g>

      <rect x="754" :y="box(stage).y" width="136" :height="box(stage).h" rx="14" class="new" />
      <template v-if="stage >= 2">
        <text x="822" :y="box(stage).mid - 8" class="bt">One backend</text>
        <text x="822" :y="box(stage).mid + 15" class="bt">all signals</text>
      </template>
      <template v-else>
        <text x="822" y="282" class="bt">Logs and</text>
        <text x="822" y="305" class="bt">traces</text>
        <text x="822" y="330" class="sub">OpenSearch, Jaeger</text>
      </template>
    </g>
    <text x="890" y="402" class="key add" text-anchor="end">M metrics · L logs · T traces</text>
  </svg>
</template>

<style scoped>
.lab { width: 100%; max-width: 880px; height: auto; display: block; margin: 0.8rem auto 0; overflow: visible; }
.have { fill: #F1ECE3; stroke: #C9C0B3; stroke-width: 2; }
.new { fill: var(--mint-soft); stroke: #1E8A5F; stroke-width: 2.5; }
.svc { fill: var(--surface); stroke: #C9C0B3; stroke-width: 1.5; }
.bt { font-family: 'Radio Canada Big', sans-serif; font-size: 19px; font-weight: 600; fill: var(--ink); text-anchor: middle; }
.bt.left { text-anchor: start; }
.st { font-family: 'Geist Mono', monospace; font-size: 13px; fill: var(--ink); text-anchor: middle; }
.sub.left { text-anchor: start; }
.sub { font-family: 'Geist Mono', monospace; font-size: 12px; fill: var(--ink-dim); text-anchor: middle; }
.proto { font-family: 'Geist Mono', monospace; font-size: 12px; font-weight: 700; fill: #1E8A5F; text-anchor: middle; }
.hd { font-family: 'Geist Mono', monospace; font-size: 13px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; fill: var(--ink-dim); }
.hd.n { fill: #1E8A5F; }
.hd-rule { stroke: #C9C0B3; stroke-width: 2; }
.hd-rule.n { stroke: #1E8A5F; }

.link { fill: none; stroke: #A9A196; stroke-width: 3; }
.call { stroke: #C9C0B3; stroke-width: 2; }
.flow { fill: none; stroke: #1E8A5F; stroke-width: 3; }
.flow.big { stroke-width: 5; }

.sig circle { fill: var(--surface); stroke: #1E8A5F; stroke-width: 2; }
.sig text { font-family: 'Geist Mono', monospace; font-size: 13px; font-weight: 700; fill: var(--ink); text-anchor: middle; }
.sig.grey circle { stroke: #A9A196; }
.key { font-family: 'Geist Mono', monospace; font-size: 13px; fill: var(--ink-dim); }
.i-check { fill: var(--mint); }
.i-tick { fill: none; stroke: var(--ink); stroke-width: 2.4; stroke-linecap: round; stroke-linejoin: round; }
.i-graph { fill: none; stroke: var(--sapphire); stroke-width: 3; stroke-linejoin: round; stroke-linecap: round; }
.i-log { fill: none; stroke: var(--ink-dim); stroke-width: 2.6; stroke-linecap: round; }
.i-trace rect { fill: var(--sapphire); }

.add { opacity: 0; transition: opacity 0.6s ease; }
[data-stage="1"] .add, [data-stage="2"] .add { opacity: 1; }
.old { transition: opacity 0.6s ease; }
.gone { opacity: 0.25; }
.sub.stays { fill: #1E8A5F; font-weight: 700; }
.flow.opt { stroke-dasharray: 7 6; }
</style>
