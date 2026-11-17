<script setup lang="ts">
// Cold open: the rider's view, then the on-call view.
// stage 0 = the app looks fine · 1 = "it left 4 minutes ago" · 2 = the check goes critical
defineProps<{ stage: number }>()

const rows = [
  { line: 'U1', to: 'Fürth Hardhöhe', min: '2 min', hero: true },
  { line: 'U2', to: 'Flughafen', min: '4 min' },
  { line: 'U3', to: 'Gustav-Adolf-Str.', min: '6 min' },
  { line: 'U1', to: 'Langwasser Süd', min: '7 min' },
]

// stale ratio over the last 30 min, in %: flat around 2, then climbing past 10
const points = [2, 2.2, 1.9, 2.1, 2.4, 2, 2.3, 3.1, 4.6, 7.2, 11.5, 17, 24, 31, 38]
const W = 420, H = 96, MAX = 40
const x = (i: number) => (i / (points.length - 1)) * W
const y = (v: number) => H - (v / MAX) * H
const line = points.map((v, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)} ${y(v).toFixed(1)}`).join(' ')
const area = `${line} L${W} ${H} L0 ${H} Z`
const threshold = y(10)
</script>

<template>
  <div class="cold">
    <div class="phone">
      <div class="notch" />
      <div class="app-head">
        <span class="stop">Plärrer</span>
        <span class="live"><i />live</span>
      </div>
      <ul class="deps">
        <li v-for="(r, i) in rows" :key="i" :class="{ hero: r.hero, lie: r.hero && stage >= 1 }">
          <span class="line" :class="r.line">{{ r.line }}</span>
          <span class="to">{{ r.to }}</span>
          <span class="min">{{ r.min }}</span>
        </li>
      </ul>
      <transition name="fade">
        <div v-if="stage >= 1" class="truth">left 4 minutes ago</div>
      </transition>
    </div>

    <transition name="slide">
      <div v-if="stage >= 2" class="alert">
        <div class="a-top"><span class="sev">CRITICAL</span><span class="src">service check</span><span class="time">11:16</span></div>
        <div class="a-svc">departures-api · stale-departures</div>
        <div class="a-msg"><span class="a-big">38%</span> served from the timetable</div>
        <svg class="a-chart" :viewBox="`0 0 ${W} ${H}`" preserveAspectRatio="none">
          <path :d="area" fill="rgba(245, 81, 46, 0.18)" />
          <line x1="0" :y1="threshold" :x2="W" :y2="threshold" stroke="#C9C2B6" stroke-dasharray="5 5" stroke-width="1.5" />
          <path :d="line" fill="none" stroke="#F5512E" stroke-width="3" stroke-linejoin="round" />
        </svg>
        <div class="a-sub"><span>last 30 min</span><span>critical at 10%</span></div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.cold { display: flex; align-items: center; justify-content: center; gap: 3.5rem; height: 100%; }

.phone {
  position: relative; width: 300px; height: 400px; padding: 34px 16px 16px;
  background: var(--surface); border: 10px solid var(--ink); border-radius: 38px;
  box-shadow: 0 18px 40px rgba(43, 38, 32, 0.16);
}
.notch {
  position: absolute; top: 6px; left: 50%; transform: translateX(-50%);
  width: 80px; height: 18px; border-radius: 10px; background: var(--ink);
}
.app-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.8rem; }
.stop { font-weight: 700; font-size: 1.05rem; }
.live { font-size: 0.75rem; color: var(--ink-dim); display: flex; align-items: center; gap: 4px; }
.live i { width: 7px; height: 7px; border-radius: 50%; background: var(--mint); display: inline-block; }

.deps { list-style: none; padding: 0; margin: 0; }
.deps li {
  display: grid; grid-template-columns: 38px 1fr auto; align-items: center; gap: 8px;
  padding: 9px 6px; border-bottom: 1px solid var(--border); font-size: 0.92rem;
  transition: background 0.3s ease;
}
.deps li.hero { font-size: 1.05rem; font-weight: 700; }
.deps li.lie { background: #FDE3DC; }
.deps li.lie .min { text-decoration: line-through; color: var(--claim); }
.line {
  font-size: 0.8rem; font-weight: 700; color: #fff; text-align: center;
  padding: 2px 0; border-radius: 4px; background: var(--sapphire);
}
.line.U2 { background: #D9473B; }
.line.U3 { background: #2BA3A0; }
.to { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.min { font-family: 'Geist Mono', monospace; white-space: nowrap; }

.truth {
  margin-top: 1rem; text-align: center; font-family: 'Kalam', cursive;
  font-size: 1.5rem; color: var(--claim); transform: rotate(-3deg);
}

.alert {
  width: 470px; padding: 1.1rem 1.2rem 0.9rem; border-radius: 14px;
  background: #1F2022; color: #fff; box-shadow: 0 18px 40px rgba(43, 38, 32, 0.25);
}
.a-top { display: flex; align-items: center; gap: 0.6rem; font-size: 0.95rem; }
.sev { background: var(--claim); color: #fff; padding: 1px 9px; border-radius: 999px; font-weight: 700; letter-spacing: 0.04em; }
.src { color: #C9C2B6; }
.time { margin-left: auto; font-family: 'Geist Mono', monospace; color: #C9C2B6; }
.a-svc { margin-top: 0.7rem; font-family: 'Geist Mono', monospace; font-size: 1.05rem; color: var(--sapphire-soft); }
.a-msg { margin-top: 0.2rem; font-size: 1.3rem; font-weight: 700; line-height: 1.2; }
.a-big { font-size: 2.3rem; color: var(--claim); }
.a-chart { display: block; width: 100%; height: 96px; margin-top: 0.6rem; border-radius: 6px; background: #2A2B2E; }
.a-sub { display: flex; justify-content: space-between; margin-top: 0.3rem; font-size: 0.85rem; color: #C9C2B6; }

.fade-enter-active, .slide-enter-active, .fade-leave-active, .slide-leave-active { transition: all 0.4s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.slide-enter-from, .slide-leave-to { opacity: 0; transform: translateX(40px); }
</style>
