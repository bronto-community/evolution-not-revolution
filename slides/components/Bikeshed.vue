<script setup lang="ts">
// The detour. stage 0 = a bike shed covered in the usual debates.
// stage 1 = the notes fade, the definition of bikeshedding appears.
// stage 2 = "Not today." stamped across it. Detour closed.
withDefaults(defineProps<{ stage?: number }>(), { stage: 0 })

const notes = [
  { text: 'unknown unknowns?', x: 40, y: 150, r: -5, c: '#FCE8A0' },
  { text: 'monitoring vs. observability', x: 560, y: 120, r: 4, c: '#CFE3FF' },
  { text: 'three pillars?', x: 120, y: 300, r: 3, c: '#FAD2C8' },
  { text: 'what is observability?', x: 500, y: 290, r: -4, c: '#D4F2E4' },
  { text: 'is it just APM?', x: 330, y: 360, r: 2, c: '#FCE8A0' },
]
</script>

<template>
  <div class="bs" :data-stage="stage">
    <div class="shed-layer">
      <svg class="shed" viewBox="0 0 460 300">
        <!-- back wall with planks -->
        <path d="M50 78 L410 58 L410 272 L50 272 Z" class="wall" />
        <path v-for="px in [95, 140, 185, 230, 275, 320, 365]" :key="px" :d="`M${px} ${78 - (px - 50) * 0.056} L${px} 272`" class="plank" />
        <!-- lean-to roof and posts, open front -->
        <path d="M24 70 L436 46 L436 62 L24 88 Z" class="roof" />
        <path d="M50 86 L50 272 M410 62 L410 272" class="post" />
        <!-- rack -->
        <path d="M70 250 L390 250" class="rack" />
        <!-- two bikes -->
        <g v-for="bx in [84, 258]" :key="bx" :transform="`translate(${bx} 0)`" class="bike">
          <circle cx="0" cy="240" r="30" />
          <circle cx="104" cy="240" r="30" />
          <path d="M0 240 L46 240 L36 186 Z M36 186 L88 188 L46 240 M88 188 L104 240 M28 178 L46 178 M36 186 L36 178 M88 188 L84 174 L100 170" />
        </g>
        <path d="M10 274 L450 272" class="ground" />
      </svg>
      <div v-for="n in notes" :key="n.text" class="note"
           :style="{ left: n.x + 'px', top: n.y + 'px', transform: `rotate(${n.r}deg)`, background: n.c }">
        {{ n.text }}
      </div>
    </div>

    <div class="def-layer">
      <div class="def">
        <div class="word">bike·shed·ding</div>
        <p>Arguing at length about the easy thing everyone has an opinion on, like the colour of the bike shed,
          while the hard thing, the power plant next door, gets waved through.</p>
        <div class="src">Parkinson's law of triviality, 1957</div>
        <div class="stamp">Not today.</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bs { position: relative; height: 430px; margin-top: 0.4rem; }
.shed-layer, .def-layer { position: absolute; inset: 0; transition: opacity 0.5s ease, transform 0.5s ease; }

.shed { position: absolute; left: 50%; top: 10px; width: 540px; transform: translateX(-50%); }
.shed path, .shed circle { fill: none; stroke: var(--ink); stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }
.shed .wall { fill: #EFE6D6; stroke-width: 0; }
.shed .plank { stroke: #D9C9AE; stroke-width: 2; }
.shed .roof { fill: #A0522D; stroke: #6E3A1F; }
.shed .post { stroke: #6E3A1F; stroke-width: 7; }
.shed .rack { stroke: var(--ink-dim); stroke-width: 4; }
.shed .bike circle, .shed .bike path { stroke: var(--ink); stroke-width: 3.5; }
.shed .ground { stroke: var(--ink-dim); }

.note {
  position: absolute; padding: 0.7rem 1rem; max-width: 15rem;
  font-family: 'Kalam', cursive; font-size: 1.35rem; line-height: 1.2; color: var(--ink);
  box-shadow: 0 8px 18px rgba(43, 38, 32, 0.18); transition: opacity 0.4s ease;
}

.def-layer { display: flex; align-items: center; justify-content: center; opacity: 0; transform: translateY(20px); pointer-events: none; }
.def {
  position: relative; width: 620px; padding: 1.6rem 2rem 1.4rem;
  background: var(--surface); border: 1px solid var(--border); border-radius: 14px;
  box-shadow: 0 20px 44px rgba(43, 38, 32, 0.2);
}
.word { font-family: 'Source Serif 4', Georgia, serif; font-size: 2.2rem; font-weight: 600; }
.def p { margin: 0.6rem 0 0; font-size: 1.15rem; line-height: 1.45; }
.src { margin-top: 0.8rem; font-family: 'Geist Mono', monospace; font-size: 0.75rem; color: var(--ink-dim); }
.stamp {
  position: absolute; right: -36px; bottom: -34px; padding: 0.3rem 1.1rem;
  font-family: 'Kalam', cursive; font-size: 2.6rem; font-weight: 700; color: var(--claim);
  border: 4px solid var(--claim); border-radius: 10px; background: rgba(255, 255, 255, 0.85);
  transform: rotate(-9deg) scale(1.6); opacity: 0; transition: all 0.25s cubic-bezier(0.3, 1.6, 0.6, 1);
}

[data-stage="1"] .note, [data-stage="2"] .note { opacity: 0; }
[data-stage="1"] .shed-layer, [data-stage="2"] .shed-layer { opacity: 0.35; }
[data-stage="1"] .def-layer, [data-stage="2"] .def-layer { opacity: 1; transform: translateY(0); }
[data-stage="2"] .stamp { opacity: 1; transform: rotate(-9deg) scale(1); }
</style>
