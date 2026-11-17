// Records one agent run (real Claude Code in ttyd, scripted model) to recordings/agent-<lab>.mp4.
//   node agent-demo/recording/record.mjs classic|enriched [--pace 6] [--tail 18] [--font 24]
// Starts its own mock model (127.0.0.1:8787) and ttyd (localhost:7689), so stop live.sh first.
// Frames are lossless screenshots of a 1920x1080 page, timed by the wall clock and
// encoded to h264 with ffmpeg (sharper text than Playwright's built-in webm recorder).
import { spawn, execFileSync } from 'child_process'
import { mkdirSync, rmSync, writeFileSync, readFileSync } from 'fs'
import { dirname, join } from 'path'
import { fileURLToPath } from 'url'
import { chromium } from 'playwright-chromium'

const HERE = dirname(fileURLToPath(import.meta.url))
const D = join(HERE, '..')
const args = process.argv.slice(2)
const lab = args[0]
if (!['classic', 'enriched'].includes(lab)) { console.error('usage: record.mjs classic|enriched [--pace s] [--tail s] [--font px]'); process.exit(2) }
const opt = (name, dflt) => (args.includes(name) ? args[args.indexOf(name) + 1] : dflt)
const PACE = opt('--pace', '6')
const TAIL = +opt('--tail', '18')          // seconds the final answer stays on screen
const FONT = opt('--font', '24')
const FPS = 10
const PORT = 7689
const scenes = JSON.parse(readFileSync(join(D, 'scenes.json'), 'utf8'))
const PROMPT = scenes[lab].prompt
const OUT = join(D, 'recordings', `agent-${lab}.mp4`)
const FRAMES = join(D, 'recordings', `frames-${lab}`)
rmSync(FRAMES, { recursive: true, force: true }); mkdirSync(FRAMES, { recursive: true })

const THEME = JSON.stringify({ background: '#FAF8F4', foreground: '#2B2620', cursor: '#2B2620', cursorAccent: '#FAF8F4',
  selectionBackground: '#C2CEFF', black: '#2B2620', brightBlack: '#857B6E', white: '#E7E0D4', brightWhite: '#FFFFFF' })
const procs = []
const run = (cmd, a) => { const p = spawn(cmd, a, { cwd: D, stdio: ['ignore', 'inherit', 'inherit'] }); procs.push(p); return p }
const cleanup = () => { for (const p of procs) { try { p.kill('SIGTERM') } catch {} } }
process.on('exit', cleanup)
process.on('SIGINT', () => process.exit(130))

run('python3', ['-I', 'mock_model.py', '--pace', PACE])
run('ttyd', ['--port', String(PORT), '--writable', '--interface', 'lo0', '--index', 'cc/ttyd-index.html', '--once',
  '-t', `fontSize=${FONT}`, '-t', 'lineHeight=1.15', '-t', 'fontFamily=Menlo, Monaco, monospace', '-t', `theme=${THEME}`,
  '-t', 'rendererType=dom', '-t', 'disableLeaveAlert=true', '-t', 'disableResizeOverlay=true', '-t', 'titleFixed=claude',
  'bash', 'claude_live.sh', lab])
const sleep = ms => new Promise(r => setTimeout(r, ms))
const state = async () => (await fetch('http://127.0.0.1:8787/state')).json()
for (let i = 0; i < 50; i++) { try { await state(); break } catch { await sleep(200) } }

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 })
await page.goto(`http://localhost:${PORT}/`, { waitUntil: 'load' })
await page.addStyleTag({ content: 'html,body{background:#FAF8F4!important;margin:0} #terminal-container{margin:28px 0 0 40px;width:calc(100vw - 80px)!important;height:calc(100vh - 48px)!important}' })
await page.evaluate(() => window.dispatchEvent(new Event('resize')))
await sleep(6000)                          // Claude Code boots, MCP server connects

// capture loop: screenshots stamped with wall-clock time
const shots = []
let capturing = true
const t0 = Date.now()
const capture = (async () => {
  let n = 0
  while (capturing) {
    const t = Date.now()
    const f = join(FRAMES, `${String(n++).padStart(5, '0')}.png`)
    await page.screenshot({ path: f })
    shots.push({ f, t: t - t0 })
    const left = 1000 / FPS - (Date.now() - t)
    if (left > 0) await sleep(left)
  }
})()

await sleep(1500)
await page.locator('.xterm').click()
await page.keyboard.type(PROMPT, { delay: 30 })
await sleep(700)
await page.keyboard.press('Enter')
// until the last turn has been sent, then a bit for streaming / rendering
for (;;) { await sleep(300); const s = await state(); if (s.done && s.scene === lab) break }
await sleep(TAIL * 1000)
capturing = false
await capture
await browser.close()
cleanup()

// concat list with each frame's real duration
const end = Date.now() - t0
const lines = []
shots.forEach((s, i) => { lines.push(`file '${s.f}'`, `duration ${(((shots[i + 1]?.t ?? end) - s.t) / 1000).toFixed(3)}`) })
lines.push(`file '${shots.at(-1).f}'`)
writeFileSync(join(FRAMES, 'list.txt'), lines.join('\n') + '\n')
execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', join(FRAMES, 'list.txt'),
  '-vf', 'fps=25,format=yuv420p', '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-tune', 'stillimage',
  '-movflags', '+faststart', OUT], { stdio: 'inherit' })
if (!args.includes('--keep-frames')) rmSync(FRAMES, { recursive: true, force: true })
console.log(`wrote ${OUT} (${(end / 1000).toFixed(1)} s)`)
process.exit(0)
