<script setup lang="ts">
// Systems keep getting more complex; the way we catch and fix problems has to keep up.
// stage 1 = the systems curve · 2 = the practices staircase
//       3 = Alex and Sam stopped at logs, checks, graphs (pre-2000): the gap to today's system
// Rough anchor years (the step is drawn where the practice became common, not invented):
//   logs: syslog, early 1980s · checks: SNMP 1988 (Nagios/NetSaint 1999) · graphs: MRTG 1995
//   traces: Google's Dapper paper 2010, Zipkin 2012 · OTel: 2019 (OpenTracing + OpenCensus)
//   semconv: stable HTTP semantic conventions, late 2023 · AI: agents helping investigate, 2025
//   systems: VMware/EC2 1999-2006 · Docker 2013, Kubernetes 2014 · AI coding agents 2024+
// The y axis is "complexity", deliberately unitless.
withDefaults(defineProps<{ stage?: number }>(), { stage: 0 })

const X0 = 80, X1 = 770, YB = 340, YT = 40
const Y0 = 1982, Y1 = 2027, LMAX = 6.4
const X = (yr: number) => X0 + ((yr - Y0) / (Y1 - Y0)) * (X1 - X0)
const Y = (l: number) => YB - (l / LMAX) * (YB - YT)

const sys = [
  { yr: 1982, l: 1.2 },
  { yr: 1990, l: 1.55, label: 'one server', dx: -4, dy: -18 },
  { yr: 2006, l: 2.3, label: 'VMs, cloud', dx: -10, dy: -14, anchor: 'end' },
  { yr: 2014, l: 3.5, label: 'containers, microservices', dx: -12, dy: -10, anchor: 'end' },
  { yr: 2024, l: 5.2, label: 'AI writes and ships code', dx: -12, dy: -8, anchor: 'end' },
  { yr: 2027, l: 6.3 },
]

// Catmull-Rom through the points, as cubic Béziers
const pts = sys.map(p => [X(p.yr), Y(p.l)])
const sysPath = pts.map((p, i) => {
  if (i === 0) return `M${p[0]} ${p[1]}`
  const p0 = pts[i - 2] ?? pts[i - 1], p1 = pts[i - 1], p3 = pts[i + 1] ?? p
  const c1 = [p1[0] + (p[0] - p0[0]) / 6, p1[1] + (p[1] - p0[1]) / 6]
  const c2 = [p[0] - (p3[0] - p1[0]) / 6, p[1] - (p3[1] - p1[1]) / 6]
  return `C${c1[0].toFixed(1)} ${c1[1].toFixed(1)} ${c2[0].toFixed(1)} ${c2[1].toFixed(1)} ${p[0].toFixed(1)} ${p[1].toFixed(1)}`
}).join(' ')

const steps = [
  { yr: 1984, l: 0.7, label: 'logs' },
  { yr: 1988, l: 1.0, label: 'checks' },
  { yr: 1995, l: 1.3, label: 'graphs' },
  { yr: 2010, l: 2.3, label: 'traces' },
  { yr: 2019, l: 3.3, label: 'OTel' },
  { yr: 2023, l: 3.9, label: 'semconv' },
  { yr: 2025, l: 4.6, label: 'AI' },
]
const stairPath = steps.map((s, i) => (i === 0 ? `M${X(s.yr)} ${Y(s.l)}` : `V${Y(s.l)}`) + ` H${X(steps[i + 1]?.yr ?? 2027)}`).join(' ')

const logs = steps[2] // Alex and Sam: logs, checks, graphs
const sysAt2027 = Y(6.3)
</script>

<template>
  <svg class="evo" :data-stage="stage" viewBox="0 0 900 380">
    <!-- axes -->
    <line :x1="X0" :x2="X1 + 20" :y1="YB" :y2="YB" class="axis" />
    <line :x1="X0" :x2="X0" :y1="YB" :y2="YT - 14" class="axis" />
    <text v-for="yr in [1990, 2000, 2010, 2020]" :key="yr" :x="X(yr)" :y="YB + 22" class="tick" text-anchor="middle">{{ yr }}</text>
    <text :x="X0 - 14" :y="YT - 4" class="axl" text-anchor="end" transform="">complexity</text>
    <text :x="X1 + 20" :y="YB + 22" class="axl" text-anchor="end">time</text>

    <!-- legend -->
    <g class="legend sys-l">
      <line x1="120" x2="146" y1="32" y2="32" class="sys" />
      <text x="154" y="37">our systems</text>
    </g>
    <g class="legend prac-l">
      <line x1="280" x2="306" y1="32" y2="32" class="prac" />
      <text x="314" y="37">how we catch and fix problems</text>
    </g>

    <!-- the gap (stage 3) -->
    <g class="gap">
      <path :d="`M${X(logs.yr)} ${Y(logs.l)} H${X(2027)}`" class="stuck" />
      <path :d="`M${X(2027) + 26} ${Y(logs.l)} H${X(2027) + 36} V${sysAt2027} H${X(2027) + 26}`" class="bracket" />
      <text :x="X(2027) - 6" :y="Y(logs.l) - 12" class="stuck-l" text-anchor="end">Alex and Sam, 18:16</text>
      <text :x="X(2027) + 46" :y="(Y(logs.l) + sysAt2027) / 2 + 8" class="gap-l">the gap</text>
    </g>

    <!-- practices staircase -->
    <path :d="stairPath" class="prac draw" pathLength="1" />
    <g class="prac-labels">
      <text v-for="s in steps" :key="s.label" :x="X(s.yr) + 4" :y="s.above ? Y(s.l) - 9 : Y(s.l) + 20" class="step-l">{{ s.label }}<tspan v-if="s.label2" :x="X(s.yr) + 4" dy="17">{{ s.label2 }}</tspan></text>
    </g>

    <!-- systems curve -->
    <path :d="sysPath" class="sys draw" pathLength="1" />
    <g class="sys-labels">
      <template v-for="p in sys" :key="p.yr">
        <g v-if="p.label">
          <circle :cx="X(p.yr)" :cy="Y(p.l)" r="5" class="dot" />
          <text :x="X(p.yr) + p.dx" :y="Y(p.l) + p.dy" class="sys-t" :text-anchor="p.anchor ?? 'start'">{{ p.label }}</text>
        </g>
      </template>
    </g>
  </svg>
</template>

<style scoped>
.evo { display: block; width: 100%; height: auto; margin-top: 0.2rem; overflow: visible; }
.axis { stroke: var(--ink); stroke-width: 2; }
.tick { font-family: 'Geist Mono', monospace; font-size: 13px; fill: var(--ink-dim); }
.axl { font-family: 'Geist Mono', monospace; font-size: 12px; fill: var(--ink-dim); text-transform: uppercase; letter-spacing: 0.08em; }

.sys { fill: none; stroke: var(--claim); stroke-width: 4; stroke-linecap: round; }
.prac { fill: none; stroke: #1E8A5F; stroke-width: 4; stroke-linejoin: round; stroke-linecap: round; }
.dot { fill: var(--claim); }
.sys-t { font-family: 'Radio Canada Big', sans-serif; font-size: 16px; font-weight: 600; fill: var(--claim); }
.step-l { font-family: 'Radio Canada Big', sans-serif; font-size: 14px; font-weight: 600; fill: #1E8A5F; }
.legend text { font-family: 'Radio Canada Big', sans-serif; font-size: 15px; fill: var(--ink); }

.stuck { fill: none; stroke: #1E8A5F; stroke-width: 2.5; stroke-dasharray: 6 6; }
.bracket { fill: none; stroke: var(--ink); stroke-width: 2.5; }
.stuck-l { font-family: 'Kalam', cursive; font-size: 18px; fill: var(--ink); }
.gap-l { font-family: 'Kalam', cursive; font-size: 28px; font-weight: 700; fill: var(--claim); }

/* reveal */
.draw { stroke-dasharray: 1; stroke-dashoffset: 1; opacity: 0; transition: stroke-dashoffset 1.4s ease, opacity 0.1s; }
.sys-labels, .prac-labels, .sys-l, .prac-l, .gap { opacity: 0; transition: opacity 0.5s ease 0.3s; }
[data-stage="1"] .sys.draw, [data-stage="2"] .sys.draw, [data-stage="3"] .sys.draw,
[data-stage="2"] .prac.draw, [data-stage="3"] .prac.draw { stroke-dashoffset: 0; opacity: 1; }
[data-stage="1"] .sys-labels, [data-stage="2"] .sys-labels, [data-stage="3"] .sys-labels,
[data-stage="1"] .sys-l, [data-stage="2"] .sys-l, [data-stage="3"] .sys-l,
[data-stage="2"] .prac-labels, [data-stage="3"] .prac-labels,
[data-stage="2"] .prac-l, [data-stage="3"] .prac-l,
[data-stage="3"] .gap { opacity: 1; }
</style>
