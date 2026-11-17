// Shared helpers for the headless UI scripts (Playwright: npm install in lab/).
'use strict';
const path = require('path');
const LAB = path.resolve(__dirname, '../..');
const PW = process.env.PLAYWRIGHT || path.resolve(LAB, 'node_modules/playwright-chromium');
const { chromium } = require(PW);
const OSD = 'http://localhost:5601';
const JAEGER = 'http://localhost:16686';
const OS = 'http://localhost:9200';

// Discover URL: index pattern, query (DQL), time range, columns
function discover({ index, query = '', from = 'now-15m', to = 'now', columns = ['_source'], sort = [['@timestamp', 'desc']] }) {
  const q = query.replace(/'/g, "!'");
  const cols = columns.map((c) => `'${c}'`).join(',');
  const s = sort.map(([f, d]) => `!('${f}',${d})`).join(',');
  return `${OSD}/app/data-explorer/discover#?_a=(discover:(columns:!(${cols}),isDirty:!f,sort:!(${s})),metadata:(indexPattern:'${index}',view:discover))` +
    `&_g=(filters:!(),refreshInterval:(pause:!t,value:0),time:(from:${from},to:${to}))` +
    `&_q=(filters:!(),query:(language:kuery,query:'${encodeURIComponent(q)}'))`;
}

async function os(pathAndQuery, body) {
  const r = await fetch(OS + pathAndQuery, body ? { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) } : {});
  return r.json();
}

async function browser() {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1920, height: 1080 }, timezoneId: 'Europe/Berlin', locale: 'en-GB', colorScheme: 'light' });
  return { b, ctx };
}

const text = async (p, n = 3000) => (await p.innerText('body')).replace(/\n+/g, ' | ').slice(0, n);

module.exports = { chromium, OSD, JAEGER, OS, LAB, discover, os, browser, text };
