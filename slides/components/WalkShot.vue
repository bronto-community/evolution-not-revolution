<script setup lang="ts">
// One step of the demo, replayed from a still of the real lab (lab/scripts/ui/walk.js -> walk.json).
// spot:  boxes to outline: indexes into the step's marks, 'dots' / 'click' (scatter step), or {x,y,w,h} in % of the image; the rest dims.
// zoom:  a region ({x,y,w,h} in %) shown enlarged in an inset, so the room can read it.
// at:    where the inset sits ('tr' | 'tl' | 'br' | 'bl' | 'c'), width: inset width in % of the slide.
import { computed } from 'vue'
import walk from './walk.json'

type Box = { x: number; y: number; w: number; h: number }
const props = withDefaults(defineProps<{
  step: string
  spot?: (number | Box | 'dots' | 'click')[]
  zoom?: Box | null
  at?: 'tr' | 'tl' | 'br' | 'bl' | 'c'
  width?: number
  caption?: string
}>(), { spot: () => [], zoom: null, at: 'tr', width: 46, caption: '' })

const s = computed(() => (walk as any).steps[props.step])
const ratio = (walk as any).vh / (walk as any).vw
const boxes = computed<Box[]>(() => props.spot
  .flatMap((m) => m === 'dots' ? (s.value?.dots ?? []) : m === 'click' ? [s.value?.click] : typeof m === 'number' ? [s.value?.marks?.[m]] : [m])
  .filter(Boolean))

const inset = computed(() => {
  const z = props.zoom
  if (!z) return null
  return {
    style: {
      width: `${props.width}%`,
      aspectRatio: `${z.w} / ${z.h * ratio}`,
      backgroundImage: `url(${s.value.img})`,
      backgroundSize: `${(100 / z.w) * 100}% auto`,
      backgroundPosition: `${z.w >= 100 ? 0 : (z.x / (100 - z.w)) * 100}% ${z.h >= 100 ? 0 : (z.y / (100 - z.h)) * 100}%`,
    },
    src: { left: `${z.x}%`, top: `${z.y}%`, width: `${z.w}%`, height: `${z.h}%` },
  }
})
</script>

<template>
  <div class="walk">
    <img :src="s.img" alt="" class="shot" />
    <svg v-if="boxes.length || inset" class="dimmer" viewBox="0 0 100 100" preserveAspectRatio="none">
      <defs><mask :id="`m-${step}`">
        <rect x="0" y="0" width="100" height="100" fill="#fff" />
        <rect v-for="(b, i) in boxes" :key="i" :x="b.x" :y="b.y" :width="b.w" :height="b.h" fill="#000" />
      </mask></defs>
      <rect x="0" y="0" width="100" height="100" fill="rgba(20,24,32,0.42)" :mask="`url(#m-${step})`" />
    </svg>
    <div v-for="(b, i) in boxes" :key="i" class="spot"
         :style="{ left: `${b.x}%`, top: `${b.y}%`, width: `${b.w}%`, height: `${b.h}%` }" />
    <template v-if="inset">
      <div class="src" :style="inset.src" />
      <div class="inset" :class="at" :style="inset.style" />
    </template>
    <div v-if="caption" class="cap">{{ caption }}</div>
  </div>
</template>

<style scoped>
.walk { position: absolute; inset: 0; overflow: hidden; background: #fff; }
.shot { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: top left; }
.dimmer { position: absolute; inset: 0; width: 100%; height: 100%; z-index: 1; pointer-events: none; }
.spot { position: absolute; z-index: 2; border: 4px solid var(--sapphire); border-radius: 6px; box-shadow: 0 0 0 2px #fff; }
.src { position: absolute; z-index: 2; border: 3px dashed var(--sapphire); border-radius: 4px; }
.inset { position: absolute; z-index: 3; background-repeat: no-repeat; background-color: #fff;
  border: 4px solid var(--sapphire); border-radius: 10px; box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35); }
.inset.tr { top: 9%; right: 2.5%; }
.inset.tl { top: 9%; left: 2.5%; }
.inset.br { bottom: 4%; right: 2.5%; }
.inset.bl { bottom: 4%; left: 2.5%; }
.inset.c { top: 50%; left: 50%; transform: translate(-50%, -50%); }
/* over the app's own dark header bar (no content there), so no row of the screen is covered */
.cap { position: absolute; z-index: 4; left: 0; right: 0; top: 0; height: 6.2%; display: flex; align-items: center;
  padding: 0 1.2rem; background: #1b2532; color: #fff; font-size: 1.02rem; font-weight: 600; line-height: 1.2; }
</style>
