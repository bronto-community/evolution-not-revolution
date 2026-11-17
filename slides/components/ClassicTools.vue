<script setup lang="ts">
import { computed } from 'vue'

// The three things on-call already has, as overlapping windows.
// stage 0 = the check list · 1 = + the per-line graph · 2 = + the terminal
// round 1 = the first incident: only U1, the logs say the stops lookups time out
// round 2 = two weeks later: a vaguer symptom. Every line is a bit worse, none stands
//           out, and the logs are full of warnings that point nowhere in particular.
const props = withDefaults(defineProps<{ stage?: number; round?: number }>(), { stage: 0, round: 1 })

// stale ratio per line over 20 minutes, one point per minute
const ROUNDS = {
  1: {
    hour: '11',
    max: 40,
    checks: [
      { host: 'departures-api', svc: 'stale-departures', state: 'CRITICAL', out: '38% served from timetable (crit 10%)' },
      { host: 'departures-api', svc: 'http', state: 'OK', out: 'HTTP 200, 14 ms' },
      { host: 'realtime-feed', svc: 'feed-freshness', state: 'OK', out: 'last update 3 s ago' },
      { host: 'stops-api', svc: 'http', state: 'OK', out: 'HTTP 200, 9 ms' },
      { host: 'nbg-transit-01', svc: 'load', state: 'OK', out: 'load average 0.82' },
      { host: 'nbg-transit-01', svc: 'disk /', state: 'OK', out: '41% used' },
    ],
    lines: [
      { id: 'u2', label: 'U2', dy: -2, pts: [2.2, 2, 2.4, 2.1, 1.8, 2.2, 2.3, 2, 1.9, 2.4, 2.1, 2, 2.3, 2.2, 1.9, 2.1, 2.4, 2.2, 2, 2.1, 2.3] },
      { id: 'u3', label: 'U3', dy: 11, pts: [1.6, 1.9, 1.7, 1.8, 2, 1.7, 1.6, 1.9, 1.8, 1.7, 2, 1.8, 1.6, 1.9, 1.7, 1.8, 2, 1.7, 1.9, 1.8, 1.7] },
      { id: 'u1', label: 'U1', dy: 5, pts: [2, 2.1, 1.9, 2.2, 2, 2.3, 2.8, 3.6, 4.9, 6.4, 8.3, 10.9, 13.8, 17.2, 20.6, 24.1, 27.9, 31, 34.2, 36.5, 38] },
    ],
    term: [
      { cmd: 'tail -f departures-api.log | grep -i timeout', out: ['11:16:02 WARN stops lookup timed out line=U1 after=2000ms', '11:16:05 WARN stops lookup timed out line=U1 after=2000ms', '11:16:09 WARN stops lookup timed out line=U1 after=2000ms'] },
    ],
  },
  2: {
    hour: '18',
    max: 20,
    checks: [
      { host: 'departures-api', svc: 'stale-departures', state: 'CRITICAL', out: '14% served from timetable (crit 10%)' },
      { host: 'departures-api', svc: 'http', state: 'OK', out: 'HTTP 200, 15 ms' },
      { host: 'realtime-feed', svc: 'feed-freshness', state: 'OK', out: 'last update 2 s ago' },
      { host: 'stops-api', svc: 'http', state: 'OK', out: 'HTTP 200, 8 ms' },
      { host: 'nbg-transit-01', svc: 'load', state: 'OK', out: 'load average 1.12' },
      { host: 'nbg-transit-01', svc: 'disk /', state: 'OK', out: '42% used' },
    ],
    lines: [
      { id: 'u1', label: 'U1', dy: -6, pts: [3, 3.4, 4.1, 5.6, 7.9, 10.8, 12.6, 13.4, 12.1, 10.2, 9.1, 9.8, 11.7, 13.9, 14.6, 13.2, 11.4, 10.6, 11.9, 13.5, 14] },
      { id: 'u2', label: 'U2', dy: 4, pts: [2.6, 3.1, 4.4, 6.2, 8.8, 11.2, 12.9, 12.2, 10.4, 9.3, 9.9, 11.4, 13.1, 13.8, 12.6, 11, 10.1, 11.2, 12.8, 13.6, 13.1] },
      { id: 'u3', label: 'U3', dy: 14, pts: [2.2, 2.8, 3.6, 5.1, 7.4, 9.6, 11.8, 12.7, 11.6, 9.8, 8.9, 10.3, 12.2, 13.1, 12.9, 11.6, 10.4, 10.9, 12.4, 12.9, 12.4] },
    ],
    term: [
      { cmd: 'grep WARN *.log | wc -l', out: ['41827'] },
      { cmd: 'grep WARN *.log | tail -3', out: ['departures-api.log: 18:16:07 WARN retrying upstream request', 'stops-api.log:      18:16:08 WARN slow query 812ms', 'realtime-feed.log:  18:16:09 WARN message out of order'] },
    ],
  },
} as const

const r = computed(() => ROUNDS[props.round as 1 | 2] ?? ROUNDS[1])

const W = 440, H = 150
const x = (i: number) => (i / 20) * W
const y = (v: number) => H - (v / r.value.max) * H
const path = (pts: readonly number[]) => pts.map((v, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)} ${y(v).toFixed(1)}`).join(' ')
const ticks = [0, 5, 10, 15, 20]
const grid = computed(() => [0, 0.25, 0.5, 0.75, 1].map(f => f * r.value.max))
const labels = computed(() => [0, 0.5, 1].map(f => f * r.value.max))
</script>

<template>
  <div class="ct">
    <div class="win checks">
      <div class="bar"><i /><i /><i /><span>Problems · nbg-transit</span></div>
      <table>
        <tr v-for="c in r.checks" :key="c.host + c.svc" :class="c.state.toLowerCase()">
          <td><span class="st">{{ c.state }}</span></td>
          <td class="h">{{ c.host }}<br><b>{{ c.svc }}</b></td>
          <td class="o">{{ c.out }}</td>
        </tr>
      </table>
    </div>

    <transition name="pop">
      <div v-if="stage >= 1" class="win graph">
        <div class="bar"><i /><i /><i /><span>stale-departures · per line · last 20 min</span></div>
        <svg :viewBox="`-34 -10 ${W + 70} ${H + 34}`">
          <line v-for="v in grid" :key="v" x1="0" :x2="W" :y1="y(v)" :y2="y(v)" class="grid" />
          <text v-for="v in labels" :key="'l' + v" x="-8" :y="y(v) + 4" class="ax" text-anchor="end">{{ v }}%</text>
          <text v-for="t in ticks" :key="'t' + t" :x="x(t)" :y="H + 20" class="ax" text-anchor="middle">{{ r.hour }}:{{ String(t).padStart(2, '0') }}</text>
          <line x1="0" :x2="W" :y1="y(10)" :y2="y(10)" class="thr" />
          <text :x="round === 2 ? 4 : W - 2" :y="round === 2 ? y(10) + 14 : y(10) - 6" class="ax thr-l" :text-anchor="round === 2 ? 'start' : 'end'">critical 10%</text>
          <path v-for="l in r.lines" :key="l.id" :d="path(l.pts)" class="ln" :class="[l.id, { hero: round === 1 && l.id === 'u1' }]" />
          <text v-for="l in r.lines" :key="'t' + l.id" :x="W + 6" :y="y(l.pts[20]) + l.dy" class="tag" :class="l.id + 't'">{{ l.label }}</text>
        </svg>
      </div>
    </transition>

    <transition name="pop">
      <div v-if="stage >= 2" class="win term" :class="{ r2: round === 2 }">
        <div class="bar dark"><i /><i /><i /><span>ops@nbg-transit-01: /var/log/transit</span></div>
        <pre><template v-for="(c, i) in r.term" :key="i"><span class="p">$</span> {{ c.cmd }}
<template v-for="l in c.out" :key="l">{{ l }}
</template></template><span class="p">$</span> <span class="cursor" /></pre>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.ct { position: relative; height: 410px; margin-top: 0.6rem; }
.win {
  position: absolute; background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; overflow: hidden; box-shadow: 0 16px 36px rgba(43, 38, 32, 0.16);
}
.bar { display: flex; align-items: center; gap: 6px; padding: 0.45rem 0.8rem; background: #F1ECE3; font-family: 'Geist Mono', monospace; font-size: 0.68rem; color: var(--ink-dim); }
.bar i { width: 9px; height: 9px; border-radius: 50%; background: #D8D0C3; display: inline-block; }
.bar span { margin-left: 0.5rem; }
.bar.dark { background: #2A2B2E; color: #C9C2B6; }
.bar.dark i { background: #55575C; }

.checks { left: 0; top: 0; width: 470px; }
.checks table { width: 100%; border-collapse: collapse; font-size: 0.72rem; }
.checks td { padding: 0.42rem 0.7rem; border-top: 1px solid var(--border); vertical-align: middle; }
.checks .h { font-family: 'Geist Mono', monospace; color: var(--ink-dim); line-height: 1.3; }
.checks .h b { color: var(--ink); font-weight: 600; }
.checks .o { color: var(--ink-dim); }
.st { display: inline-block; min-width: 4.8rem; text-align: center; padding: 2px 0; border-radius: 4px; font-weight: 700; font-size: 0.66rem; letter-spacing: 0.04em; color: #fff; background: #3C9A5F; }
.critical .st { background: var(--claim); }
.critical .o { color: var(--ink); font-weight: 600; }
.critical td { background: #FDE9E3; }

.graph { left: 490px; top: 24px; width: 380px; }
.graph svg { display: block; width: 100%; padding: 0.4rem 0.4rem 0.2rem; }
.grid { stroke: var(--border); stroke-width: 1; }
.ax { font-family: 'Geist Mono', monospace; font-size: 10px; fill: var(--ink-dim); }
.thr { stroke: var(--claim); stroke-width: 1.5; stroke-dasharray: 5 4; }
.thr-l { fill: var(--claim); }
.ln { fill: none; stroke-width: 2.6; stroke-linejoin: round; }
.u1 { stroke: var(--sapphire); }
.hero { stroke-width: 3.4; }
.u2 { stroke: #D9473B; }
.u3 { stroke: #2BA3A0; }
.tag { font-family: 'Geist Mono', monospace; font-size: 12px; font-weight: 700; }
.u1t { fill: var(--sapphire); }
.u2t { fill: #D9473B; }
.u3t { fill: #2BA3A0; }

.term { left: 150px; top: 262px; width: 620px; background: #1F2022; border-color: #1F2022; }
.term pre { margin: 0; padding: 0.7rem 1rem 0.8rem; color: #EDE8DF; font-family: 'Geist Mono', monospace; font-size: 0.74rem; line-height: 1.6; background: transparent; }
.term.r2 { top: 214px; left: 30px; }
.term .p { color: var(--mint); }
.cursor { display: inline-block; width: 0.55em; height: 1em; vertical-align: -0.15em; background: #EDE8DF; animation: blink 1s steps(1) infinite; }
@keyframes blink { 50% { opacity: 0; } }

.pop-enter-active { transition: all 0.35s ease; }
.pop-enter-from { opacity: 0; transform: translateY(16px) scale(0.98); }
</style>
