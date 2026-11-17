#!/usr/bin/env node
// make record: videos of the before and after click paths (1920x1080 H.264) into recordings/, while the incident is on.
//   before.mp4  classic: alert -> timetable lines (stops_api_ms ~1 s) -> stops-api's own lines (a few ms) -> dead end
//   after.mp4   enriched: alert -> the same lines with traceId -> the trace (client span ~1 s, stops-api ~6 ms)
//               -> Jaeger search, click the biggest dot -> one 5.0 trace (26 calls, its UA and query) -> one trace id
//               in Discover (logs + spans)
// Each part is one browser context with Playwright's recordVideo; a caption bar says what we are looking at.
'use strict';
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const { chromium, discover, os, LAB, OSD, JAEGER } = require('../ui/lib');

const OUT = path.join(LAB, 'recordings');
const WORK = path.join(OUT, '.work');
const FFMPEG = process.env.FFMPEG || '/opt/homebrew/bin/ffmpeg';
const SIZE = { width: 1920, height: 1080 };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function caption(p, text) {
  await p.evaluate((t) => {
    let el = document.getElementById('lab-caption');
    if (!el) {
      el = document.createElement('div');
      el.id = 'lab-caption';
      Object.assign(el.style, { position: 'fixed', left: '0', right: '0', bottom: '0', zIndex: 2147483647, padding: '14px 28px',
        background: 'rgba(20,30,45,.88)', color: '#fff', font: '600 26px/1.3 system-ui, sans-serif' });
      document.body.appendChild(el);
    }
    el.textContent = t;
  }, text).catch(() => {});
}

async function traces() {
  const q = (filter) => os('/enriched-spans-*/_search', { size: 1, sort: [{ '@timestamp': 'desc' }], query: { bool: { filter: [
    ...filter, { term: { kind: 'Server' } }, { range: { '@timestamp': { gte: 'now-5m', lte: 'now-30s' } } }] } } });
  const b = (await q([{ prefix: { 'attributes.user_agent.original': 'departure-board' } }, { range: { 'attributes.duration_ms': { gte: 800 } } }])).hits.hits[0];
  const a = (await q([{ prefix: { 'attributes.user_agent.original': 'JourneyApp/5' } }, { range: { 'attributes.duration_ms': { gte: 1500 } } }])).hits.hits[0];
  if (!b || !a) throw new Error('incident not on (no slow board / 5.0 request in the last 5 min): make status');
  return { board: b._source.traceId, app5: a._source.traceId };
}

// the monitor's own page (not the Alerting overview, which lists every alert of both labs)
async function monitor(name) {
  const r = await os('/_plugins/_alerting/monitors/_search', { query: { match_phrase: { 'monitor.name': name } } });
  const hit = r.hits.hits[0];
  if (!hit) throw new Error(`monitor not found: ${name}`);
  return `${OSD}/app/alerting#/monitors/${hit._id}`;
}

async function part(name, steps) {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: SIZE, timezoneId: 'Europe/Berlin', locale: 'en-GB', colorScheme: 'light',
    recordVideo: { dir: WORK, size: SIZE } });
  const p = await ctx.newPage();
  const go = async (url, text, hold = 6000) => {
    if (url.includes('discover')) await p.goto('about:blank');   // Discover keeps its old query on a hash-only change
    await p.goto(url);
    if (url.includes('discover')) await p.getByText(/Results \(/).first().waitFor({ timeout: 60000 }).catch(() => {});
    else await sleep(2500);
    await caption(p, text);
    await sleep(hold);
  };
  const t0 = Date.now();
  await steps(p, go);
  const video = p.video();
  await ctx.close();
  await b.close();
  const raw = await video.path();
  const mp4 = path.join(OUT, `${name}.mp4`);
  execFileSync(FFMPEG, ['-y', '-loglevel', 'error', '-i', raw, '-vf', 'scale=1920:1080,fps=25', '-c:v', 'libx264',
    '-pix_fmt', 'yuv420p', '-crf', '23', '-movflags', '+faststart', mp4]);
  console.log(`${mp4} (${((Date.now() - t0) / 1000).toFixed(0)} s)`);
}

async function main() {
  fs.mkdirSync(WORK, { recursive: true });
  const t = await traces();
  const which = process.argv.slice(2);
  const want = (n) => !which.length || which.includes(n);

  if (want('before')) await part('before', async (p, go) => {
    await go(await monitor('classic: departures served from timetable'), 'Before (classic). The alert: departure boards are being served the printed timetable.');
    await go(discover({ index: 'classic-logs', query: 'event:served_from_timetable', columns: ['app', 'stop', 'stops_api_ms', 'message'] }),
      'departures-api: "served_from_timetable", all stops, the call to stops-api took ~1 s (stops_api_ms).', 9000);
    await go(discover({ index: 'classic-logs', query: 'app:stops-api', columns: ['app', 'path', 'duration_ms', 'message'] }),
      'stops-api, its own log: every request done in under ~50 ms. The two teams\' logs contradict each other.', 9000);
    await go(discover({ index: 'classic-logs', query: 'app:departures-api and path:"/departures"', columns: ['app', 'method', 'path', 'status', 'duration_ms'] }),
      'Every request: GET /departures 200. Same path for everyone, no errors, no link to the stops-api line. Dead end.', 9000);
  });

  if (want('after')) await part('after', async (p, go) => {
    await go(await monitor('enriched: departures served from timetable'), 'After (enriched). The same alert, the same moment.');
    await go(discover({ index: 'enriched', query: 'attributes.event.name:served_from_timetable', columns: ['resource.service.name', 'attributes.stops_api_ms', 'body', 'traceId'] }),
      'The same log lines, now with a trace id (a link to the trace).', 8000);
    await go(`${JAEGER}/trace/${t.board}`, 'One board request: departures-api waits ~1 s for its call; stops-api answers in a few ms, at the very end.', 10000);
    const end = Date.now() * 1000, start = end - 5 * 60 * 1e6;
    await go(`${JAEGER}/search?service=departures-api&operation=${encodeURIComponent('GET /departures')}&lookback=5m&limit=500&start=${start}&end=${end}`,
      'Who holds the connections? All departures-api requests of the last 5 minutes. Dot size = number of spans.', 9000);
    const dot = await p.evaluate(() => {
      let best = null;
      for (const c of document.querySelectorAll('circle.recharts-dot')) {   // the scatter dots, not icons
        const bb = c.getBoundingClientRect(), r = bb.width;
        if (bb.width && (!best || r > best.r)) best = { r, x: bb.x + bb.width / 2, y: bb.y + bb.height / 2 };
      }
      return best;
    });
    if (!dot) throw new Error('no dots in the Jaeger scatter plot');
    await caption(p, 'A few requests are much bigger than the rest. Click one ...');
    await sleep(2500);
    await p.mouse.click(dot.x, dot.y);
    await sleep(3000);
    await caption(p, 'One of them: 53 spans, 26 calls to stops-api in parallel, each waiting for one of the 5 connections.');
    await sleep(8000);
    await p.getByText('GET /departures').nth(1).click().catch(() => {});
    await sleep(700);
    await p.getByText('Attributes:', { exact: false }).first().click().catch(() => {});
    await caption(p, 'user_agent.original = JourneyApp/5.0.0, url.query = ...&include=route. From the zero-code instrumentation, not app code.');
    await sleep(9000);
    await go(discover({ index: 'enriched', query: `traceId:${t.board}`, from: 'now-1h', columns: ['_index', 'resource.service.name', 'kind', 'name', 'attributes.duration_ms', 'body'] }),
      'One trace id in Discover: the request\'s spans and its log lines from both services.', 9000);
  });
  fs.rmSync(WORK, { recursive: true, force: true });
}

main().catch((e) => { console.error(e); process.exit(2); });
