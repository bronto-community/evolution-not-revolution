<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'

// round 1: the first incident ends well. The logs point at stops-api, someone has
//          seen it before, they scale it, the check goes green.
// round 2: two weeks later, the same two people have no idea. No resolution.
// round 3: the same incident replayed after the demo, now with shared attributes and traces:
//          a connection pool held by a third-party app's new release (JourneyApp 5.0, include=route).
// One message per click. `compact` is the smaller window that sits on top of ClassicTools.
// `auto` (ms): ignore `stage` and post the messages one after another on their own,
// starting when `run` turns true (default: on mount). One click shows the whole conversation.
const props = withDefaults(defineProps<{ stage?: number; round?: number; compact?: boolean; auto?: number; run?: boolean }>(), { stage: 0, round: 1, compact: false, auto: 0, run: true })

const ticks = ref(0)
let timer: ReturnType<typeof setInterval> | undefined
watch(() => props.run, (run) => {
  clearInterval(timer)
  ticks.value = 0
  if (!props.auto || !run) return
  timer = setInterval(() => {
    ticks.value++
    if (ticks.value >= msgs.value.length) clearInterval(timer)
  }, props.auto)
}, { immediate: true })
onUnmounted(() => clearInterval(timer))
const shown = computed(() => props.auto ? (props.run ? ticks.value : -1) : props.stage)

const ROUNDS = {
  1: [
    { at: 0, who: 'Alex', role: 'on call', time: '11:18', text: 'Only U1. The logs say the stops lookups time out.' },
    { at: 1, who: 'Sam', role: 'platform', time: '11:20', text: 'Seen that before. stops-api gets slow when it\'s busy. Give it more replicas.' },
    { at: 2, who: 'Alex', role: 'on call', time: '11:22', text: 'Scaled stops-api from 2 to 4.' },
  ],
  2: [
    { at: 0, who: 'Alex', role: 'on call', time: '18:18', text: 'stale-departures is critical again. All lines this time.' },
    { at: 1, who: 'Sam', role: 'platform', time: '18:20', text: 'stops-api looks fine. 4 replicas, 8 ms. It\'s not that.' },
    { at: 2, who: 'Alex', role: 'on call', time: '18:23', text: '41k warnings in the logs. Where do I even start?' },
    { at: 3, who: 'Sam', role: 'platform', time: '18:24', text: 'No idea. Restart departures-api and see?' },
  ],
  3: [
    { at: 0, who: 'Alex', role: 'on call', time: '18:18', text: 'stale-departures is critical again. All lines this time.' },
    { at: 1, who: 'Alex', role: 'on call', time: '18:19', text: 'One slow board request, one trace: our call to stops-api takes 950 ms, stops-api\'s own part 6 ms. We wait before the call even leaves.' },
    { at: 2, who: 'Sam', role: 'platform', time: '18:20', text: 'That\'s our pool, 5 connections. Holding them: JourneyApp/5.0 with include=route, 26 calls to stops-api each. Rolling out since 17:30.' },
    { at: 3, who: 'Alex', role: 'on call', time: '18:22', text: 'Pool raised to 50, boards recovering. Calling their vendor about include=route.' },
  ],
} as const
const msgs = computed(() => ROUNDS[props.round as 1 | 2 | 3] ?? ROUNDS[1])
</script>

<template>
  <div class="chat" :class="{ compact }">
    <div class="head"># incident-departures</div>
    <div class="list">
      <transition-group name="msg">
        <div v-for="m in msgs.filter(m => shown >= m.at)" :key="m.time" class="msg">
          <div class="avatar" :class="m.who.toLowerCase()">{{ m.who[0] }}</div>
          <div class="body">
            <div class="meta"><b>{{ m.who }}</b><span>{{ m.role }}</span><span class="t">{{ m.time }}</span></div>
            <div class="text">{{ m.text }}</div>
          </div>
        </div>
        <div v-if="round !== 2 && shown >= (round === 1 ? 3 : 4)" key="ok" class="resolved">
          <span class="st">OK</span>
          <span class="svc">departures-api · stale-departures</span>
          <span class="val">{{ round === 1 ? '2.1%' : '1.8%' }}</span>
          <span class="t">{{ round === 1 ? '11:31' : '18:27' }}</span>
        </div>
      </transition-group>
    </div>
  </div>
</template>

<style scoped>
.chat {
  margin: 1.2rem auto 0; max-width: 720px; background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; overflow: hidden; box-shadow: 0 16px 36px rgba(43, 38, 32, 0.12);
}
.head { padding: 0.6rem 1.1rem; background: #F1ECE3; font-family: 'Geist Mono', monospace; font-size: 0.8rem; color: var(--ink-dim); }
.list { padding: 0.6rem 1.1rem 1rem; display: flex; flex-direction: column; gap: 0.9rem; min-height: 290px; }
.msg { display: flex; gap: 0.8rem; align-items: flex-start; }
.avatar {
  width: 38px; height: 38px; border-radius: 9px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; color: #fff; background: var(--sapphire);
}
.avatar.sam { background: #E8A33D; }
.meta { display: flex; gap: 0.6rem; align-items: baseline; font-size: 0.85rem; }
.meta span { color: var(--ink-dim); }
.meta .t { font-family: 'Geist Mono', monospace; font-size: 0.75rem; }
.text { font-size: 1.05rem; line-height: 1.4; margin-top: 0.1rem; }

.resolved {
  display: flex; align-items: center; gap: 0.8rem; margin-top: 0.3rem;
  padding: 0.65rem 0.9rem; border-radius: 10px; background: var(--mint-soft); border: 1px solid var(--mint);
}
.resolved .st { background: #3C9A5F; color: #fff; font-weight: 700; font-size: 0.75rem; padding: 2px 12px; border-radius: 4px; }
.resolved .svc { font-family: 'Geist Mono', monospace; font-size: 0.85rem; }
.resolved .val { font-weight: 700; }
.resolved .t { margin-left: auto; font-family: 'Geist Mono', monospace; font-size: 0.75rem; color: var(--ink-dim); }

/* the small window on top of the incident 2 slide */
.chat.compact { margin: 0; max-width: none; width: 100%; box-shadow: 0 20px 44px rgba(43, 38, 32, 0.28); }
.compact .head { padding: 0.45rem 0.8rem; font-size: 0.68rem; }
.compact .list { padding: 0.5rem 0.8rem 0.8rem; gap: 0.6rem; min-height: 0; }
.compact .avatar { width: 28px; height: 28px; border-radius: 7px; font-size: 0.8rem; }
.compact .meta { font-size: 0.72rem; }
.compact .text { font-size: 0.85rem; }

.msg-enter-active { transition: all 0.35s ease; }
.msg-enter-from { opacity: 0; transform: translateY(10px); }
</style>
