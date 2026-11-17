import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    watch: {
      // the lab and recordings will live next to the deck; changes there must never reload it on stage
      ignored: ['**/lab/**', '**/recording/**', '**/.vercel/**'],
    },
  },
})
