#!/usr/bin/env python3
"""The two agent runs, written as code: run it to regenerate scenes.json.

  python3 agent-demo/story.py

Same prompt, same agent, two labs:
  classic   OpenSearch index classic-logs: log lines only
  enriched  OpenSearch logs + spans with semantic-convention attributes, trace_id on log lines

Scene format: {label, prompt, turns: [[{text} | {tool, input, result, hold?}]]}.
Each inner list is one model response. `{{key}}` refers to values.json (placeholders for the
real lab numbers); mock_model.py and fake_mcp.py fill them in when they read scenes.json, so
changing values.json needs no regeneration. Changing wording here does: rerun this script.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PROMPT = 'The departure boards alert fired: boards falling back to the timetable since 18:16. Find out why.'
S = 'mcp__opensearch__'


def hits(header, rows):
    """search_logs result: a summary line, then one hit per line as key=value.
    (Not JSON: Claude Code pretty-prints JSON results over many lines, which scrolls everything away.)
    Keys starting with '_' are shown as bare values (timestamp, service, level)."""
    return header + '\n' + '\n'.join(
        ' '.join(str(v) if k.startswith('_') else f'{k}={v}' for k, v in r.items()) for r in rows)


def table(title, cols, rows):
    """field_stats / search_traces result: a small aligned table.
    cols: [(header, width, '<' or '>')]; a cell '=key' is the values.json placeholder {{key}}."""
    def cell(v, w, al):
        return '{{%s:%s%d}}' % (v[1:], al, w) if v.startswith('=') else f'{v:{al}{w}}'
    line = lambda r: ''.join(cell(v, w, al) for v, (_, w, al) in zip(r, cols)).rstrip()
    return '\n'.join([title, line([h for h, _, _ in cols])] + [line(r) for r in rows])


def trace(trace_id, total_ms, spans):
    """get_trace result: the span tree, Jaeger-style. A span with no name is an attribute line."""
    out = [f'trace {trace_id}  {total_ms} ms']
    for prefix, svc, name, kind, dur in spans:
        out.append(prefix + svc if not name else f'{prefix + svc:<20}{name:<32}{kind:<8}{dur}'.rstrip())
    return '\n'.join(out)


STATS = [('time', 7, '<'), ('count', 8, '>'), ('p50 ms', 8, '>'), ('p95 ms', 8, '>')]
BUCKETS = ['18:09', '18:12', '18:15', '18:18', '18:21']     # 3-minute buckets of "now-15m" at ~18:24


# ── classic: log lines only ────────────────────────────────────────────────────
classic = [
    [{'text': 'Starting with the fallback events on departures-api.', 'wait': 2.5},
     {'tool': S + 'search_logs', 'input': {'index': 'classic-logs', 'query': 'app:departures-api AND event:served_from_timetable', 'from': 'now-15m', 'size': 3},
      'result': hits('{{fallback_count}} hits, first at {{first_fallback}}, showing 3', [
          {'_t': '{{hit1_ts}}', '_l': 'WARNING', 'event': 'served_from_timetable', 'stop': '{{stop1}}', 'reason': 'live_data_late', 'stops_api_ms': '{{hit1_stops_ms}}'},
          {'_t': '{{hit2_ts}}', '_l': 'WARNING', 'event': 'served_from_timetable', 'stop': '{{stop2}}', 'reason': 'live_data_late', 'stops_api_ms': '{{hit2_stops_ms}}'},
          {'_t': '{{hit3_ts}}', '_l': 'WARNING', 'event': 'served_from_timetable', 'stop': '{{stop3}}', 'reason': 'live_data_late', 'stops_api_ms': '{{hit3_stops_ms}}'}])}],

    [{'text': 'The boards get the timetable because live data is late, and the lines put the time on the call to stops-api. '
              'How long do /departures requests take, and how long is that call?'},
     {'tool': S + 'field_stats', 'input': {'index': 'classic-logs', 'query': 'app:departures-api AND path:"/departures"', 'field': 'duration_ms', 'stats': ['count', 'p50', 'p95'], 'interval': '3m', 'from': 'now-15m'},
      'result': table('duration_ms, 3m buckets', STATS, [
          [BUCKETS[i], f'=dep_count_{i}', f'=dep_p50_{i}', f'=dep_p95_{i}'] for i in range(5)])},
     {'tool': S + 'field_stats', 'input': {'index': 'classic-logs', 'query': 'app:departures-api AND event:served_from_timetable', 'field': 'stops_api_ms', 'stats': ['count', 'p50', 'p95'], 'from': 'now-6m'},
      'result': table('stops_api_ms, last 6m', STATS[1:], [['=fb_count_6m', '=fb_stops_p50', '=fb_stops_p95']])}],

    [{'text': 'Requests went from ~{{dep_p50_0}} ms to ~{{dep_p50_4}} ms at p50 with the same number of requests, and on the fallback lines '
              'departures-api says the stops-api call took {{fb_stops_p50}} ms (p50), up to {{fb_stops_p95}} ms (p95). '
              'What does stops-api see on its side?'},
     {'tool': S + 'field_stats', 'input': {'index': 'classic-logs', 'query': 'app:stops-api', 'field': 'duration_ms', 'stats': ['rate', 'p50', 'p95'], 'interval': '3m', 'from': 'now-15m'},
      'result': table('duration_ms, 3m buckets', [('time', 7, '<'), ('req/s', 8, '>'), ('p50 ms', 8, '>'), ('p95 ms', 8, '>')], [
          [BUCKETS[i], f'=stops_rps_{i}', f'=stops_p50_{i}', f'=stops_p95_{i}'] for i in range(5)])}],

    [{'text': 'By its own logs stops-api answers within ~{{stops_p95_4}} ms (p95), nowhere near {{fb_stops_p50}} ms. Its traffic is up about '
              '{{stops_ratio}}x ({{stops_rps_0}} to {{stops_rps_4}} req/s), which on its own isn\'t alarming at rush hour. '
              'Checking for errors and for a change on our side.'},
     {'tool': S + 'field_stats', 'input': {'index': 'classic-logs', 'query': 'level:ERROR OR status:>=500', 'field': 'app', 'from': 'now-2h'},
      'result': '0 matching log lines'},
     {'tool': S + 'field_stats', 'input': {'index': 'classic-logs', 'query': 'app:departures-api', 'field': 'version', 'from': 'now-24h'},
      'result': 'version   share   host\n{{version:<10}}100%    {{host}}'}],

    [{'text': (
        "**What the logs show**\n"
        "- Since about {{incident_start}}, /departures requests take ~{{dep_p50_4}} ms at p50 (p95 {{dep_p95_4}} ms) instead of "
        "~{{dep_p50_0}} ms, at the same request count. departures-api logs the stops-api call at {{fb_stops_p50}} ms (p50) on the fallback lines.\n"
        "- stops-api handles its requests within ~{{stops_p95_4}} ms (p95) by its own logs. Its traffic is up ~{{stops_ratio}}x; "
        "its logs don't say from whom.\n"
        "- No errors, all 200s, departures-api {{version}} on {{host}}, the only version in the last 24 h.\n\n"
        "**What I can't tell from this data**\n"
        "The ~{{fb_stops_p50}} ms are lost between departures-api and stops-api, not inside stops-api. Possible causes: the network, a load "
        "balancer in between, how departures-api handles its connections, or another client loading stops-api. "
        "The logs can't separate these: no request id links a departures-api line to the stops-api line it caused, "
        "and there are no query strings or client details.\n\n"
        "**To go further I'd need** traces across both services (or at least a shared request id in the logs), "
        "and who is calling departures-api and stops-api, with which parameters.")}],
]

# ── enriched: logs + traces, semantic-convention attributes ────────────────────
enriched = [
    [{'text': 'Starting with the fallback events on departures-api.', 'wait': 2.5},
     {'tool': S + 'search_logs', 'input': {'index': 'enriched-logs', 'query': 'resource.service.name:departures-api AND attributes.event.name:served_from_timetable', 'from': 'now-15m', 'size': 2},
      'result': hits('{{fallback_count_enr}} hits, first at {{first_fallback_enr}}, showing 2', [
          {'_t': '{{ehit1_ts}}', '_l': 'WARNING', 'stop': '{{estop1}}', 'stops_api_ms': '{{ehit1_stops_ms}}', 'traceId': '{{trace_board}}'},
          {'_t': '{{ehit2_ts}}', '_l': 'WARNING', 'stop': '{{estop2}}', 'stops_api_ms': '{{ehit2_stops_ms}}', 'traceId': '{{trace_board2}}'}])}],

    [{'text': 'Live data arrives too late. The log lines carry a traceId, so I can open the request behind the first one.'},
     {'tool': S + 'get_trace', 'input': {'trace_id': '{{trace_board}}'},
      'result': trace('{{trace_board}}', '{{board_total_ms}}', [
          ('', 'departures-api', 'GET /departures', 'server', '{{board_total_ms:>5}} ms'),
          ('│     ', 'user_agent.original={{board_ua}}', '', '', ''),
          ('│     ', 'url.query={{board_query}}', '', '', ''),
          ('└─ ', 'departures-api', 'GET', 'client', '{{board_client_ms:>5}} ms'),
          ('   └─ ', 'stops-api', 'GET /stops/<stop_id>/platforms', 'server', '{{board_server_ms:>5}} ms')])}],

    [{'text': (
        'The client span to stops-api takes {{board_client_ms}} ms, but stops-api itself needs {{board_server_ms}} ms. '
        'So ~{{board_wait_ms}} ms pass inside departures-api before the call goes out: it is waiting for one of the 5 '
        'connections in its pool to stops-api. Who holds the connections? Searching the last 2 minutes of departures-api traces, most spans first.')},
     {'tool': S + 'search_traces', 'hold': True, 'input': {'service': 'departures-api', 'operation': 'GET /departures', 'from': 'now-2m', 'sort': 'spans:desc', 'limit': 5},
      'result': table('{{win_traces}} traces {{window}}, top 5 by span count',
                      [('trace', 9, '<'), ('spans', 5, '>'), ('ms', 7, '>'), ('  user_agent.original', 44, '<'), ('url.query', 30, '<')], [
          [f'=wtop{i}_id', f'=wtop{i}_spans', f'=wtop{i}_ms', f'=wtop{i}_ua', f'=wtop{i}_query'] for i in range(1, 6)])
      + '\n…\nmore than 5 spans: {{win_big}} traces, all JourneyApp/5.0.0 with include=route'
      + '\n3 spans: {{win_small}} traces (departure-board/3.2: {{win_board}}, JourneyApp/4.0.7: {{win_j4}})'}],

    [{'text': 'The top traces are all JourneyApp/5.0.0 with include=route and ~{{journey_spans}} spans; boards and JourneyApp/4.0.7 have 3. Opening the first one:'},
     {'tool': S + 'get_trace', 'input': {'trace_id': '{{trace_journey}}'},
      'result': trace('{{trace_journey}}', '{{journey_total_ms}}', [
          ('', 'departures-api', 'GET /departures', 'server', '{{journey_total_ms:>5}} ms'),
          ('│     ', 'user_agent.original={{journey_ua}}', '', '', ''),
          ('│     ', 'url.query={{journey_query}}', '', '', ''),
          ('└─ ', 'departures-api', 'GET', 'client', '×{{journey_calls}} in parallel, {{journey_client_range}} ms'),
          ('   └─ ', 'stops-api', 'GET /stops/<stop_id>[/…]', 'server', '×{{journey_calls}}, {{journey_server_range}} ms')])}],

    [{'text': 'One request, {{journey_calls}} parallel calls to stops-api, all through the same 5 connections. When did JourneyApp/5.0.0 show up?'},
     {'tool': S + 'field_stats', 'input': {'index': 'enriched-spans', 'query': 'resource.service.name:departures-api AND kind:Server AND attributes.user_agent.original:JourneyApp/5.0.0*', 'field': 'attributes.url.query', 'stats': ['count'], 'interval': '3m', 'from': 'now-15m'},
      'result': table('first seen {{journey5_first_seen}}, 3m buckets', [('time', 7, '<'), ('requests', 9, '>'), ('with include=route', 21, '>')], [
          [BUCKETS[i], f'=j5_n_{i}', f'=j5_route_{i}'] for i in range(5)])}],

    [{'text': (
        "**Root cause:** the JourneyApp 5.0 rollout (another company's app, first seen {{journey5_first_seen}}). It polls the same "
        "endpoint as 4.0 but adds `include=route`, so departures-api makes {{journey_calls}} calls to stops-api in parallel for each "
        "of those requests. They take the 5 connections in the pool; board requests wait ~{{board_wait_ms}} ms for a free one, "
        "miss the 500 ms live-data budget and get the timetable.\n\n"
        "**Evidence**\n"
        "- Board request `{{trace_board}}`: client span to stops-api {{board_client_ms}} ms, stops-api server span {{board_server_ms}} ms.\n"
        "- Last 2 minutes: all {{win_big}} departures-api traces with more than 5 spans are JourneyApp/5.0.0 with include=route "
        "(~{{journey_spans}} spans, e.g. `{{trace_journey}}`); boards and 4.0.7 have 3.\n"
        "- stops-api is not the bottleneck: its server spans take {{journey_server_range}} ms, its traffic is up only ~{{stops_ratio_enr}}x.\n\n"
        "**Mitigation**\n"
        "- Now: raise the pool above 5, or give include=route its own, capped pool, so board requests always get a connection.\n"
        "- Then: cap include=route on our side (route stops per request, rate) and talk to the JourneyApp vendor.")}],
]

SCENES = {
    'classic': {'label': 'classic lab: log lines in OpenSearch', 'prompt': PROMPT, 'turns': classic},
    'enriched': {'label': 'enriched lab: logs + traces, OTel semantic conventions', 'prompt': PROMPT, 'turns': enriched},
}

if __name__ == '__main__':
    with open(os.path.join(HERE, 'scenes.json'), 'w') as f:
        json.dump(SCENES, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('wrote scenes.json:', {k: len(v['turns']) for k, v in SCENES.items()}, 'turns')
