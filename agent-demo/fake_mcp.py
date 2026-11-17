#!/usr/bin/env python3
"""Tiny stdio MCP server that answers the demo's tool calls from scenes.json.

  python3 agent-demo/fake_mcp.py classic     OpenSearch, index classic-logs: log lines only
  python3 agent-demo/fake_mcp.py enriched    OpenSearch logs + spans (Jaeger-style trace view)

Both register as the MCP server `opensearch`, so the tool calls look the same in both
runs; the enriched one simply has the trace tools. A call is answered with the result
stored next to the identical call in that scene, with values.json filled in.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = {
    'classic': {
        'search_logs': 'Search log lines in OpenSearch (index classic-logs)',
        'field_stats': 'Count / percentiles / top values of a log field over time',
    },
    'enriched': {
        'search_logs': 'Search log records in OpenSearch (OTel attributes, trace_id)',
        'field_stats': 'Count / percentiles / top values of a log or span attribute over time',
        'search_traces': 'Search and group spans by attributes (service.name, user_agent.original, url.query, ...)',
        'get_trace': 'Get one trace as a span tree (Jaeger)',
    },
}


def fill(text, values):
    """{{key}} -> values.json; {{key:>6}} pads (for table columns).
    Inside JSON strings ("{{key}}") and after key= a plain number drops its quotes and thousands separators."""
    def quoted(m):
        v = values[m.group(1)]
        return v.replace(',', '') if re.fullmatch(r'[0-9][0-9,]*', v) else '"' + v + '"'

    def plain(m):
        v = values[m.group(1)]
        return f'{v:{m.group(2)}{m.group(3)}}' if m.group(2) else v
    text = re.sub(r'"\{\{(\w+)\}\}"', quoted, text)
    text = re.sub(r'=\{\{(\w+)\}\}', lambda m: '=' + quoted(m).strip('"'), text)
    return re.sub(r'\{\{(\w+)(?::([<>])(\d+))?\}\}', plain, text)


def scene_calls(scene):
    with open(os.path.join(HERE, 'values.json')) as f:
        values = {k: v['value'] for k, v in json.load(f).items() if not k.startswith('_')}
    with open(os.path.join(HERE, 'scenes.json')) as f:
        turns = json.load(f)[scene]['turns']
    calls = []
    for turn in turns:
        for b in turn:
            if 'tool' in b:
                inp = json.loads(re.sub(r'\{\{(\w+)\}\}', lambda m: values[m.group(1)], json.dumps(b['input'], ensure_ascii=False)))
                calls.append((b['tool'], inp, fill(b['result'], values)))
    return calls


def canned(scene, tool, args):
    name = f'mcp__opensearch__{tool}'
    calls = [c for c in scene_calls(scene) if c[0] == name]
    for _, inp, result in calls:
        if inp == args:
            return result
    return calls[0][2] if calls else '{"total": 0, "hits": []}'


def main():
    scene = sys.argv[1]
    for line in sys.stdin:
        msg = json.loads(line)
        mid, method = msg.get('id'), msg.get('method')
        if mid is None:
            continue                                   # notification
        if method == 'initialize':
            result = {'protocolVersion': msg['params'].get('protocolVersion', '2025-06-18'),
                      'capabilities': {'tools': {}}, 'serverInfo': {'name': 'opensearch', 'version': '1.0.0'}}
        elif method == 'tools/list':
            result = {'tools': [{'name': t, 'description': d, 'inputSchema': {'type': 'object', 'additionalProperties': True}}
                                for t, d in TOOLS[scene].items()]}
        elif method == 'tools/call':
            p = msg['params']
            result = {'content': [{'type': 'text', 'text': canned(scene, p['name'], p.get('arguments') or {})}]}
        else:
            result = {}
        sys.stdout.write(json.dumps({'jsonrpc': '2.0', 'id': mid, 'result': result}, ensure_ascii=False) + '\n')
        sys.stdout.flush()


if __name__ == '__main__':
    main()
