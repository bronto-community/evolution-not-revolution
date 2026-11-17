#!/usr/bin/env node
// make screens: the before/after click paths, headless, while the incident is on. Screenshots into screens/.
// Every view is opened by URL, the way the README click path gets there, so the screenshots match the demo.
'use strict';
const fs = require('fs');
const path = require('path');
const { browser, discover, os, LAB, OSD, JAEGER, text } = require('./lib');

const OUT = path.join(LAB, 'screens');
const WARN = [];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function findTraces() {
  // a slow board request (the victim) and a JourneyApp 5.0 request from the same minutes, both already in Jaeger
  const q = (filter) => os('/enriched-spans-*/_search', {
    size: 5, sort: [{ '@timestamp': 'desc' }],
    query: { bool: { filter: [...filter, { term: { kind: 'Server' } }, { range: { '@timestamp': { gte: 'now-5m', lte: 'now-30s' } } }] } },
  });
  const board = await q([{ prefix: { 'attributes.user_agent.original': 'departure-board' } }, { range: { 'attributes.duration_ms': { gte: 800 } } }]);
  const app5 = await q([{ prefix: { 'attributes.user_agent.original': 'JourneyApp/5' } }]);
  const b = board.hits.hits[0], a = app5.hits.hits[0];
  if (!b || !a) throw new Error('no slow board request or no 5.0 request in the last 5 minutes: is the incident on? (make status)');
  return { board: b._source.traceId, app5: a._source.traceId };
}

async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  const t = await findTraces();
  console.log('traces:', t);
  const { b, ctx } = await browser();
  let p = await ctx.newPage();
  const snap = async (name, expect) => {
    const body = await text(p, 20000);
    for (const e of expect || []) if (!body.includes(e)) WARN.push(`${name}: expected "${e}" on the page`);
    await p.screenshot({ path: path.join(OUT, name) });
    console.log('saved', name);
  };
  // a fresh page per view: Discover keeps its state on hash-only navigation
  const go = async (url, wait = 4000) => {
    await p.close(); p = await ctx.newPage(); await p.goto(url);
    if (url.includes('discover')) await p.getByText(/Results \(/).first().waitFor({ timeout: 60000 }).catch(() => WARN.push(`no results: ${url}`));
    await sleep(wait);
  };

  // 1. the alert, both labs
  await go(`${OSD}/app/alerting#/dashboard`, 7000);
  await snap('1-alerting.png', ['departures served from timetable', 'Active']);

  // BEFORE (classic): the log lines of the alert, and stops-api's own lines
  await go(discover({ index: 'classic-logs', query: 'event:served_from_timetable', columns: ['host', 'app', 'stop', 'stops_api_ms', 'message'] }));
  await snap('2-classic-departures-timetable.png', ['served_from_timetable', 'stops_api_ms']);
  await go(discover({ index: 'classic-logs', query: 'app:stops-api', columns: ['host', 'app', 'path', 'duration_ms', 'message'] }));
  await snap('3-classic-stops-api.png', ['stops-api']);

  // AFTER (enriched): the same alert lines, now with a trace id
  await go(discover({ index: 'enriched', query: 'attributes.event.name:served_from_timetable', columns: ['resource.service.name', 'attributes.stops_api_ms', 'body', 'traceId'] }));
  await snap('4-enriched-timetable-lines.png', ['served_from_timetable']);

  // the slow board request's trace: client span ~1 s, stops-api server span a few ms
  await go(`${JAEGER}/trace/${t.board}`, 5000);
  await snap('5-jaeger-board-trace-gap.png', ['departures-api', 'stops-api']);

  // the bad requests and what they have in common: slow departures-api requests, field user_agent.original
  await go(discover({ index: 'enriched-spans', query: 'resource.service.name:departures-api and kind:Server and attributes.duration_ms >= 2000',
    columns: ['attributes.user_agent.original', 'attributes.url.query', 'attributes.duration_ms'] }));
  await p.getByRole('button', { name: /attributes\.user_agent\.original/ }).first().hover().catch(() => {});
  const details = p.locator('[data-test-subj="fieldToggle-attributes.user_agent.original"], [aria-label*="Show details for attributes.user_agent.original"], [data-test-subj="field-attributes.user_agent.original-showDetails"]').first();
  if (await details.count()) { await details.click(); } else { await p.getByText('attributes.user_agent.original', { exact: true }).first().click(); }
  await sleep(1500);
  await snap('6-enriched-slow-requests-user-agent.png', ['JourneyApp/5.0']);

  // a 5.0 request: ~25 parallel calls to stops-api
  await go(`${JAEGER}/trace/${t.app5}`, 5000);
  await p.getByText('GET /departures').nth(1).click();   // the root span's row: its tags
  await sleep(800);
  await p.getByText('Attributes:', { exact: false }).first().click().catch(() => {});
  await sleep(800);
  await snap('7-jaeger-app5-trace.png', ['JourneyApp/5.0', 'include=route']);

  // one trace id in Discover: that request's log lines and spans together
  await go(discover({ index: 'enriched', query: `traceId:${t.board}`, from: 'now-1h', columns: ['_index', 'resource.service.name', 'kind', 'name', 'attributes.duration_ms', 'body'] }));
  await snap('8-discover-one-trace-logs-and-spans.png', ['enriched-logs', 'enriched-spans']);

  await b.close();
  if (WARN.length) { console.log('WARNINGS:\n  ' + WARN.join('\n  ')); process.exit(1); }
}

main().catch((e) => { console.error(e); process.exit(2); });
