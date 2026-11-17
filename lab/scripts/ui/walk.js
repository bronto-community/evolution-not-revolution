#!/usr/bin/env node
// make walk: capture both click paths as stills for the deck (slides/public/walk/*.png + walk.json), while the
// incident is on. Each step: one screenshot (1440x810 @2x) and the boxes of what to look at (in % of the image),
// so the slides can outline and zoom them. The slides replay the demo from these; nothing live on stage.
'use strict';
const fs = require('fs');
const path = require('path');
const { chromium, discover, os, LAB, OSD, JAEGER } = require('./lib');

const OUT = path.resolve(LAB, '../slides/public/walk');
const VW = 1440, VH = 810;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const steps = {};

const pct = (b, pad = 0) => b && {
  x: +(((b.x - pad) / VW) * 100).toFixed(2), y: +(((b.y - pad) / VH) * 100).toFixed(2),
  w: +(((b.width + 2 * pad) / VW) * 100).toFixed(2), h: +(((b.height + 2 * pad) / VH) * 100).toFixed(2),
};
async function bbox(loc, pad = 4) {
  try { const b = await loc.first().boundingBox({ timeout: 3000 }); return pct(b, pad); } catch { return null; }
}
// a Discover column: header cell down to the bottom of the visible rows
async function column(p, name) {
  const th = p.locator('th', { hasText: new RegExp(`^\\s*${name.replace(/\./g, '\\.')}\\s*$`) });
  const b = await th.first().boundingBox({ timeout: 3000 }).catch(() => null);
  if (!b) return null;
  return pct({ x: b.x, y: b.y, width: b.width, height: VH - b.y - 8 }, 2);
}

async function monitorUrl(name) {
  const r = await os('/_plugins/_alerting/monitors/_search', { query: { match_phrase: { 'monitor.name': name } } });
  return `${OSD}/app/alerting#/monitors/${r.hits.hits[0]._id}`;
}

async function boardTrace() {
  const r = await os('/enriched-spans-*/_search', { size: 20, sort: [{ '@timestamp': 'desc' }], query: { bool: { filter: [
    { term: { kind: 'Server' } }, { prefix: { 'attributes.user_agent.original': 'departure-board' } },
    { range: { 'attributes.duration_ms': { gte: 900, lte: 1500 } } },
    { range: { '@timestamp': { gte: 'now-4m', lte: 'now-20s' } } }] } } });
  const h = r.hits.hits[0];
  if (!h) throw new Error('no slow board request in the last 4 min: is the incident on? (make status)');
  return h._source.traceId;
}

async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: VW, height: VH }, deviceScaleFactor: 2, timezoneId: 'Europe/Berlin', locale: 'en-GB', colorScheme: 'light' });
  const p = await ctx.newPage();
  const go = async (url, wait = 3000) => {
    if (url.includes('discover')) url = url.replace('time:(from:now-15m', 'time:(from:now-10m');
    await p.goto('about:blank');
    await p.goto(url);
    if (url.includes('discover')) await p.getByText(/Results \(/).first().waitFor({ timeout: 60000 }).catch(() => {});
    await sleep(wait);
  };
  // the alert itself: Alerting overview, search the lab, open the newest trigger group -> the alert's flyout
  const monitorPage = async (lab) => {
    await go(`${OSD}/app/alerting#/dashboard?from=0&search=${lab}&severityLevel=ALL&size=20&sortDirection=desc&sortField=start_time&state=ALL`, 6000);
    await p.getByText(/^\d+ alerts?$/).first().click();
    await sleep(3000);
  };
  const shot = async (id, marks, extra = {}) => {
    await p.mouse.move(VW - 2, VH - 2);
    await p.screenshot({ path: path.join(OUT, `${id}.png`) });
    steps[id] = { img: `/walk/${id}.png`, marks: marks.filter(Boolean), ...extra };
    console.log(id, JSON.stringify(steps[id].marks));
  };

  // ---------- before (classic) ----------
  await monitorPage('classic');
  await shot('b1-alert', [await bbox(p.getByText('Trigger start time').first().locator('xpath=..'), 8),
    await bbox(p.getByText('Monitor', { exact: true }).first().locator('xpath=..'), 8)]);

  await go(discover({ index: 'classic-logs', query: 'event:served_from_timetable', columns: ['app', 'stop', 'stops_api_ms', 'message'] }));
  await shot('b2-timetable', [await column(p, 'stops_api_ms'), await column(p, 'stop')]);

  await go(discover({ index: 'classic-logs', query: 'app:stops-api', columns: ['app', 'path', 'duration_ms', 'message'] }));
  await shot('b3-stops-api', [await column(p, 'duration_ms')]);

  await go(discover({ index: 'classic-logs', query: 'app:departures-api and path:"/departures"', columns: ['app', 'method', 'path', 'status', 'duration_ms'] }));
  await shot('b4-dead-end', [await bbox(p.locator('[data-test-subj="dscSideBarFieldList"], .dscSidebar, nav').first(), 0),
    await column(p, 'path'), await column(p, 'status')]);

  // ---------- after (enriched) ----------
  await monitorPage('enriched');
  await shot('a1-alert', [await bbox(p.getByText('Trigger start time').first().locator('xpath=..'), 8),
    await bbox(p.getByText('Monitor', { exact: true }).first().locator('xpath=..'), 8)]);

  await go(discover({ index: 'enriched', query: 'attributes.event.name:served_from_timetable', columns: ['resource.service.name', 'attributes.stops_api_ms', 'traceId'] }));
  await shot('a2-traceid', [await column(p, 'traceId'), await column(p, 'attributes.stops_api_ms')]);

  const board = await boardTrace();
  await go(`${JAEGER}/trace/${board}`, 3500);
  await shot('a3-board-trace', [
    await bbox(p.locator('.span-row', { hasText: 'departures-api' }).nth(1), 2),
    await bbox(p.locator('.span-row', { hasText: 'stops-api' }).first(), 2)], { traceId: board });

  const end = (Date.now() - 20000) * 1000, start = end - 5 * 60 * 1e6;   // only finished traces
  await go(`${JAEGER}/search?service=departures-api&operation=${encodeURIComponent('GET /departures')}&lookback=5m&limit=500&start=${start}&end=${end}`, 5000);
  const dots = await p.evaluate(() => [...document.querySelectorAll('circle.recharts-dot')]
    .map((c) => { const r = c.getBoundingClientRect(); return { x: r.x, y: r.y, width: r.width, height: r.height }; })
    .filter((r) => r.width > 0).sort((a, b) => b.width - a.width));
  const big = dots[0];
  const bigs = dots.filter((d) => d.width >= big.width * 0.8).slice(0, 12).map((d) => pct(d, 4));
  const plot = await bbox(p.locator('.recharts-wrapper').first(), 4);
  await shot('a4-scatter', [plot], { dots: bigs, click: pct(big, 4) });

  await p.mouse.click(big.x + big.width / 2, big.y + big.height / 2);
  await sleep(3500);
  const app5 = p.url().split('/trace/')[1];
  await shot('a5-app5-trace', [await bbox(p.locator('.TracePageHeader, [class*="TracePageHeader"]').first(), 0)], { traceId: app5 });

  await p.locator('.span-row').first().locator('.span-name').first().click().catch(() => {});
  await sleep(800);
  await p.getByText('Attributes:', { exact: false }).first().click().catch(() => {});
  await sleep(800);
  await shot('a6-attributes', [await bbox(p.locator('tr', { hasText: 'user_agent.original' })),
    await bbox(p.locator('tr', { hasText: 'url.query' }))], { traceId: app5 });

  await go(discover({ index: 'enriched', query: `traceId:${board}`, from: 'now-1h', columns: ['_index', 'resource.service.name', 'kind', 'name', 'attributes.duration_ms', 'attributes.event.name'] }));
  await shot('a7-one-trace', [await column(p, '_index'), await column(p, 'resource.service.name')], { traceId: board });

  await b.close();
  fs.writeFileSync(path.resolve(LAB, '../slides/components/walk.json'), JSON.stringify({ captured: new Date().toISOString(), vw: VW, vh: VH, steps }, null, 1));
  console.log('slides/components/walk.json');
}

main().catch((e) => { console.error(e); process.exit(2); });
