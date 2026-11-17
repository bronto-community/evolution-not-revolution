<script setup lang="ts">
// The motif of act three: neighbouring villages that grow together.
// A village is any spot where some telemetry already fits together. The mix differs
// in every village (check / graph / log icons on the houses), on purpose: no village
// is "the logs" or "Icinga".
// stage 0 = villages, life inside each one
//       1 = dirt tracks between some of them (hostname, timestamp), people walking
//       2 = same street names everywhere: signposts, paved roads, all villages reached, cars
//       3 = a train line through every village: a trace, one passenger's whole journey
//       4 = grown into one town; the old village centres are still there
// Everything that moves is SMIL, so it runs without any JS timers.
// plain = no labels (hostname, service.name, trace_id ...), e.g. for the teaser video
withDefaults(defineProps<{ stage?: number; plain?: boolean }>(), { stage: 0, plain: false })

type Icon = 'check' | 'graph' | 'log'
type P = [number, number]

const villages: { id: string; at: P; icons: Icon[] }[] = [
  { id: 'a', at: [130, 115], icons: ['check', 'graph', 'log'] },
  { id: 'b', at: [400, 85], icons: ['log', 'log'] },
  { id: 'c', at: [690, 105], icons: ['graph', 'check'] },
  { id: 'd', at: [170, 295], icons: ['log', 'graph'] },
  { id: 'e', at: [470, 285], icons: ['check', 'log', 'check'] },
  { id: 'f', at: [770, 295], icons: ['graph', 'graph', 'check', 'log'] },
]
const V = Object.fromEntries(villages.map(v => [v.id, v.at])) as Record<string, P>
const HOUSE_OFF: P[] = [[-24, -8], [8, -16], [-8, 14], [24, 8]]

// roads as quadratic curves: from, control, to
const roads = [
  { k: 'ab', a: 'a', b: 'b', c: [265, 60] as P, track: true, label: 'hostname' },
  { k: 'ad', a: 'a', b: 'd', c: [110, 210] as P, track: true },
  { k: 'be', a: 'b', b: 'e', c: [470, 180] as P, track: true },
  { k: 'ef', a: 'e', b: 'f', c: [620, 335] as P, track: true, label: 'timestamp' },
  { k: 'bc', a: 'b', b: 'c', c: [545, 60] as P, track: false },
  { k: 'de', a: 'd', b: 'e', c: [320, 330] as P, track: false },
  { k: 'cf', a: 'c', b: 'f', c: [800, 200] as P, track: false },
].map(r => ({ ...r, d: `M${V[r.a][0]} ${V[r.a][1]} Q${r.c[0]} ${r.c[1]} ${V[r.b][0]} ${V[r.b][1]}` }))

function q(r: typeof roads[number], t: number): P {
  const p0 = V[r.a], p2 = V[r.b], u = 1 - t
  return [u * u * p0[0] + 2 * u * t * r.c[0] + t * t * p2[0], u * u * p0[1] + 2 * u * t * r.c[1] + t * t * p2[1]]
}
function normal(r: typeof roads[number], t: number): P {
  const p0 = V[r.a], p2 = V[r.b]
  const dx = 2 * (1 - t) * (r.c[0] - p0[0]) + 2 * t * (p2[0] - r.c[0])
  const dy = 2 * (1 - t) * (r.c[1] - p0[1]) + 2 * t * (p2[1] - r.c[1])
  const l = Math.hypot(dx, dy) || 1
  return [-dy / l, dx / l]
}
const trackLabels = roads.filter(r => r.label).map(r => {
  const p = q(r, 0.5), n = normal(r, 0.5)
  return { text: r.label!, x: p[0] - n[0] * 20, y: p[1] - n[1] * 20 + 6 }
})

// the town that grows in between (stage 4): plain houses along every road
const newHouses = roads.flatMap((r, i) => [0.3, 0.42, 0.58, 0.7].map((t, j) => {
  const p = q(r, t), n = normal(r, t), s = (i + j) % 2 ? 1 : -1
  return { x: p[0] + n[0] * 17 * s, y: p[1] + n[1] * 17 * s, delay: (i * 4 + j) * 0.05 }
}))

// train line: closed Catmull-Rom loop past every village
// inner loop, so it doesn't run on top of the roads; stations sit on each village's inner edge
const stations: P[] = [[178, 130], [418, 132], [644, 124], [722, 280], [442, 242], [217, 280]]
const trainPath = (() => {
  const n = stations.length
  let d = `M${stations[0][0]} ${stations[0][1]}`
  for (let i = 0; i < n; i++) {
    const p0 = stations[(i - 1 + n) % n], p1 = stations[i], p2 = stations[(i + 1) % n], p3 = stations[(i + 2) % n]
    const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6]
    const c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6]
    d += ` C${c1[0].toFixed(1)} ${c1[1].toFixed(1)} ${c2[0].toFixed(1)} ${c2[1].toFixed(1)} ${p2[0]} ${p2[1]}`
  }
  return d + ' Z'
})()

const signs = [
  { at: [130, 175] as P, text: 'service.name' },
  { at: [690, 162] as P, text: 'transit.line' },
  { at: [470, 345] as P, text: 'service.name' },
]
const walkers = roads.filter(r => r.track).map((r, i) => ({ k: r.k, dur: 13 + i * 2, begin: -i * 3 }))
const cars = roads.map((r, i) => ({ k: r.k, dur: 4 + (i % 3), begin: -i * 1.3, color: i % 2 ? 'var(--sapphire)' : 'var(--claim)' }))
</script>

<template>
  <svg class="vil" :class="{ plain }" viewBox="0 0 900 400" :data-stage="stage" role="img"
       aria-label="Villages that get connected by tracks, roads and a train line, and grow into one town">
    <defs>
      <path v-for="r in roads" :id="`vr-${r.k}`" :key="r.k" :d="r.d" />
      <path id="vr-train" :d="trainPath" />
    </defs>

    <path class="land" d="M30 60 C120 0 330 20 470 22 C640 24 820 10 880 80 C910 160 900 300 860 360 C760 410 560 390 450 392 C300 394 110 410 40 350 C0 280 -10 140 30 60 Z" />
    <path class="town" d="M90 70 C200 30 340 40 450 45 C600 50 760 40 820 110 C860 180 850 300 810 340 C700 370 560 345 450 345 C320 345 160 365 110 330 C60 270 50 130 90 70 Z" />

    <!-- tracks (stage 1) and roads (stage 2+) -->
    <g class="roads">
      <path v-for="r in roads.filter(r => r.track)" :key="'t' + r.k" :d="r.d" class="dirt" />
      <path v-for="(r, i) in roads" :key="r.k" :d="r.d" class="road" pathLength="1" :style="{ transitionDelay: (r.track ? 0 : 0.5) + i * 0.08 + 's' }" />
    </g>
    <g class="track-l">
      <text v-for="l in trackLabels" :key="l.text" :x="l.x" :y="l.y" text-anchor="middle">{{ l.text }}</text>
    </g>

    <!-- people walking the tracks -->
    <g class="walkers">
      <circle v-for="w in walkers" :key="w.k" r="4">
        <animateMotion :dur="`${w.dur}s`" :begin="`${w.begin}s`" repeatCount="indefinite" keyPoints="0;1;0" keyTimes="0;0.5;1" calcMode="linear">
          <mpath :href="`#vr-${w.k}`" />
        </animateMotion>
      </circle>
    </g>

    <!-- cars on the paved roads -->
    <g class="cars">
      <rect v-for="c in cars" :key="c.k" x="-7" y="-4" width="14" height="8" rx="2" :fill="c.color">
        <animateMotion :dur="`${c.dur}s`" :begin="`${c.begin}s`" repeatCount="indefinite" rotate="auto" keyPoints="0;1;0" keyTimes="0;0.5;1" calcMode="linear">
          <mpath :href="`#vr-${c.k}`" />
        </animateMotion>
      </rect>
    </g>

    <!-- train line (stage 3) -->
    <g class="rail">
      <path :d="trainPath" class="rail-bed" pathLength="1" />
      <path :d="trainPath" class="rail-ties" />
      <g v-for="n in 3" :key="n" class="car">
        <rect x="-13" y="-6" width="26" height="12" rx="4" :class="{ loco: n === 1 }" />
        <animateMotion dur="12s" :begin="`${-(n - 1) * 0.22}s`" repeatCount="indefinite" rotate="auto">
          <mpath href="#vr-train" />
        </animateMotion>
      </g>
    </g>

    <!-- the town in between (stage 4) -->
    <g class="new-houses">
      <g v-for="(h, i) in newHouses" :key="i" :transform="`translate(${h.x} ${h.y})`">
        <g class="pop" :style="{ transitionDelay: h.delay + 's' }">
          <rect x="-7" y="-4" width="14" height="10" />
          <path d="M-9 -4 L0 -12 L9 -4 Z" />
        </g>
      </g>
    </g>

    <!-- villages -->
    <g v-for="v in villages" :key="v.id" :transform="`translate(${v.at[0]} ${v.at[1]})`" class="village">
      <circle r="44" class="green" />
      <g v-for="(icon, i) in v.icons" :key="i" :transform="`translate(${HOUSE_OFF[i][0]} ${HOUSE_OFF[i][1]})`" class="house">
        <rect x="-13" y="-8" width="26" height="20" />
        <path d="M-16 -8 L0 -22 L16 -8 Z" class="roof" />
        <g v-if="icon === 'check'" class="ic"><circle cx="0" cy="2" r="6" class="ic-check" /><path d="M-3 2 L-1 4.5 L3.5 -1" class="ic-tick" /></g>
        <path v-else-if="icon === 'graph'" d="M-8 7 L-4 1 L0 4 L4 -3 L8 0" class="ic ic-graph" />
        <g v-else class="ic ic-log"><path d="M-8 -2 H8 M-8 2 H5 M-8 6 H7" /></g>
      </g>
      <!-- smoke from the first chimney -->
      <circle :cx="HOUSE_OFF[0][0] + 7" :cy="HOUSE_OFF[0][1] - 22" r="4" class="smoke">
        <animate attributeName="cy" :from="HOUSE_OFF[0][1] - 22" :to="HOUSE_OFF[0][1] - 46" dur="3s" repeatCount="indefinite" :begin="`${-v.at[0] % 3}s`" />
        <animate attributeName="opacity" values="0.6;0" dur="3s" repeatCount="indefinite" :begin="`${-v.at[0] % 3}s`" />
        <animate attributeName="r" values="3;8" dur="3s" repeatCount="indefinite" :begin="`${-v.at[0] % 3}s`" />
      </circle>
      <!-- someone pottering about inside the village -->
      <circle r="3" class="local">
        <animateMotion :dur="`${5 + (v.at[1] % 4)}s`" repeatCount="indefinite" path="M-30 24 C-10 34 20 32 32 22 C20 30 -10 30 -30 24 Z" />
      </circle>
    </g>

    <!-- stations on top of the villages (stage 3+) -->
    <g class="rail stations">
      <g v-for="(s, i) in stations" :key="i" :transform="`translate(${s[0]} ${s[1]})`" class="station">
        <rect x="-9" y="-6" width="18" height="12" rx="3" class="pop" :style="{ transitionDelay: 0.3 + i * 0.2 + 's' }" />
      </g>
      <text x="418" y="158" class="station-l" text-anchor="middle">trace_id</text>
    </g>

    <!-- street signs (stage 2+) -->
    <g class="signs">
      <g v-for="(s, k) in signs" :key="s.at.join()" :transform="`translate(${s.at[0]} ${s.at[1]})`">
        <g class="pop" :style="{ transitionDelay: 0.2 + k * 0.25 + 's' }">
        <line x1="0" y1="0" x2="0" y2="18" class="post" />
        <rect :x="-s.text.length * 3.6 - 6" y="-15" :width="s.text.length * 7.2 + 12" height="18" rx="3" />
        <text x="0" y="-2" text-anchor="middle">{{ s.text }}</text>
      </g>
</g>
    </g>
  </svg>
</template>

<style scoped>
.plain .track-l, .plain .signs, .plain .station-l { display: none; }
.vil { width: 100%; max-width: 860px; height: auto; display: block; margin: 0 auto; overflow: visible; }
.land { fill: #EEF5C4; }
.town { fill: #E2EBB0; opacity: 0; transition: opacity 1s ease; }

.village .green { fill: #D6E89A; }
.house rect { fill: var(--surface); stroke: var(--ink); stroke-width: 2; }
.house .roof { fill: #C9603A; stroke: var(--ink); stroke-width: 2; stroke-linejoin: round; }
.ic-check { fill: var(--mint); }
.ic-tick { fill: none; stroke: var(--ink); stroke-width: 1.6; stroke-linecap: round; stroke-linejoin: round; }
.ic-graph { fill: none; stroke: var(--sapphire); stroke-width: 2; stroke-linejoin: round; }
.ic-log path { fill: none; stroke: var(--ink-dim); stroke-width: 1.6; }
.smoke { fill: #B9B2A6; }
.local { fill: var(--ink); }

.road { fill: none; stroke: #A9A196; stroke-width: 9; stroke-linecap: round; stroke-dasharray: 1; stroke-dashoffset: 1; opacity: 0;
  transition: stroke-dashoffset 1s ease, stroke 0.6s ease, opacity 0.1s; }
.dirt { fill: none; stroke: #B98C55; stroke-width: 3; stroke-dasharray: 2 7; stroke-linecap: round; opacity: 0; transition: opacity 0.6s ease; }
.track-l text { font-family: 'Kalam', cursive; font-size: 18px; fill: #8A6235; opacity: 0; transition: opacity 0.5s ease; }
.walkers circle { fill: var(--ink); opacity: 0; transition: opacity 0.5s ease; }
.cars rect { opacity: 0; transition: opacity 0.5s ease; }

.signs .pop { opacity: 0; }
.signs rect { fill: var(--sapphire); }
.signs text { font-family: 'Geist Mono', monospace; font-size: 11px; font-weight: 600; fill: #fff; }
.signs .post { stroke: var(--ink); stroke-width: 2; }

.rail-bed { fill: none; stroke: var(--ink); stroke-width: 6; stroke-dasharray: 1; stroke-dashoffset: 1; opacity: 0;
  transition: stroke-dashoffset 1.6s ease, stroke 0.6s ease, opacity 0.1s; }
.rail-ties, .car, .station-l { opacity: 0; transition: opacity 0.6s ease 1.4s; }
.rail-ties { fill: none; stroke: var(--ink); stroke-width: 12; stroke-dasharray: 2 9; }
.station .pop { opacity: 0; }
.station rect { fill: var(--surface); stroke: var(--sapphire); stroke-width: 3; }
.car rect { fill: var(--sapphire); stroke: var(--ink); stroke-width: 1.5; }
.car rect.loco { fill: var(--sapphire-dark); }
.station-l { font-family: 'Geist Mono', monospace; font-size: 12px; font-weight: 600; fill: var(--sapphire-dark); }

.new-houses .pop { opacity: 0; }
.new-houses rect { fill: var(--surface); stroke: var(--ink-dim); stroke-width: 1.5; }
.new-houses path { fill: #E0A487; stroke: var(--ink-dim); stroke-width: 1.5; stroke-linejoin: round; }

/* everything that gets ADDED pops in or draws on, and is mint while it's new */
.pop { transform-box: fill-box; transform-origin: 50% 100%; transform: scale(0);
  transition: transform 0.45s cubic-bezier(0.3, 1.6, 0.6, 1), opacity 0.2s ease; }

/* stage 1: tracks */
[data-stage="1"] .dirt, [data-stage="1"] .track-l text, [data-stage="1"] .walkers circle { opacity: 1; }
/* stage 2+: paved roads everywhere, signs, cars (walkers stay) */
[data-stage="2"] .road, [data-stage="3"] .road, [data-stage="4"] .road { stroke-dashoffset: 0; opacity: 1; }
[data-stage="2"] .road { stroke: var(--mint); }
[data-stage="2"] .signs .pop, [data-stage="3"] .signs .pop, [data-stage="4"] .signs .pop { opacity: 1; transform: scale(1); }
[data-stage="2"] .cars rect, [data-stage="3"] .cars rect, [data-stage="4"] .cars rect,
[data-stage="2"] .walkers circle, [data-stage="3"] .walkers circle, [data-stage="4"] .walkers circle { opacity: 1; }
/* stage 3+: the train */
[data-stage="3"] .rail-bed, [data-stage="4"] .rail-bed { stroke-dashoffset: 0; opacity: 1; }
[data-stage="3"] .rail-bed { stroke: #1E8A5F; }
[data-stage="3"] .rail-ties, [data-stage="4"] .rail-ties, [data-stage="3"] .car, [data-stage="4"] .car,
[data-stage="3"] .station-l, [data-stage="4"] .station-l { opacity: 1; }
[data-stage="3"] .station .pop, [data-stage="4"] .station .pop { opacity: 1; transform: scale(1); }
/* stage 4: one town */
[data-stage="4"] .town { opacity: 1; }
[data-stage="4"] .new-houses .pop { opacity: 1; transform: scale(1); }
[data-stage="4"] .new-houses path { fill: var(--mint); }
</style>
