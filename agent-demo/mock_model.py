#!/usr/bin/env python3
"""A scripted stand-in for the Anthropic Messages API, so real Claude Code can run the demo.
(Nothing here talks to the real Anthropic API.)

Claude Code is pointed here with ANTHROPIC_BASE_URL. The path prefix says which
lab the agent is looking at: /classic (log lines only) or /enriched (logs + traces),
so the same prompt gets a different investigation in each terminal.
Requests from the main conversation (the ones that carry tools) get the next turn
of the scene from scenes.json, with {{placeholders}} filled from values.json:
narration and tool calls, which real Claude Code executes through fake_mcp.py.
Side requests (titles, summaries) get short, plausible answers. Every request is
logged to agent-demo/cc/requests.log.

Pacing: each scripted turn starts after PACE seconds on its own (or the turn's own
"wait" in scenes.json), or earlier when the presenter presses the clicker (GET /next). A tool block marked
"hold" in scenes.json waits once more after the text before it, so the agent's
sentence stays on screen before a long tool result scrolls it away. It never waits
forever, so a lost keyboard focus can't stall the demo on stage.

  python3 agent-demo/mock_model.py              # 5 s per turn, clicker skips ahead
  python3 agent-demo/mock_model.py --pace 0.3   # fast, for headless tests
  python3 agent-demo/mock_model.py --manual     # only the clicker advances (rehearsal)
"""
import json
import os
import re
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 8787
PACE = float(sys.argv[sys.argv.index('--pace') + 1]) if '--pace' in sys.argv else 5.0
if '--manual' in sys.argv:
    PACE = None
LOG = os.path.join(HERE, 'cc', 'requests.log')

# which scene each agent plays, matched on the typed prompt
AGENTS = {'classic': ['classic'], 'enriched': ['enriched']}
INVESTIGATE_WORDS = ('alert', 'board', 'timetable', 'why', 'departure')

gate = threading.Event()          # set by /next
state = {'waiting': False, 'agent': None, 'scene': None, 'turn': None, 'done': True}


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


def load_scenes():
    """scenes.json with values.json filled in (shared with fake_mcp.py, which has its own copy)."""
    with open(os.path.join(HERE, 'values.json')) as f:
        values = {k: v['value'] for k, v in json.load(f).items() if not k.startswith('_')}
    with open(os.path.join(HERE, 'scenes.json')) as f:
        scenes = json.load(f)
    for s in scenes.values():
        for turn in s['turns']:
            for b in turn:
                for k in ('text', 'result'):
                    if k in b:
                        b[k] = fill(b[k], values)
                if 'input' in b:
                    b['input'] = json.loads(re.sub(r'\{\{(\w+)\}\}', lambda m: values[m.group(1)], json.dumps(b['input'], ensure_ascii=False)))
    return scenes


def scenes():
    # re-read on every request, so editing story.py / values.json takes effect without a restart
    return load_scenes()


def log(entry):
    with open(LOG, 'a') as f:
        f.write(json.dumps(entry) + '\n')


def summarize(body):
    sysp = body.get('system')
    if isinstance(sysp, list):
        sysp = ' '.join(b.get('text', '') for b in sysp if isinstance(b, dict))
    msgs = body.get('messages', [])
    last = msgs[-1] if msgs else {}
    content = last.get('content')
    if isinstance(content, list):
        content = [c.get('type') + (':' + c.get('text', '')[:80] if c.get('type') == 'text' else '') for c in content]
    return {'model': body.get('model'), 'stream': body.get('stream'), 'tools': len(body.get('tools') or []),
            'msgs': len(msgs), 'system': (sysp or '')[:160], 'last': str(content)[:240]}


def current_prompt_and_turn(messages):
    """The latest typed prompt, and how many assistant turns have answered it so far."""
    idx, prompt = None, ''
    for i, m in enumerate(messages):
        if m.get('role') != 'user':
            continue
        c = m.get('content')
        texts = [c] if isinstance(c, str) else [b.get('text', '') for b in c if b.get('type') == 'text']
        has_result = not isinstance(c, str) and any(b.get('type') == 'tool_result' for b in c)
        # Claude Code wraps context in <system-reminder>-style text blocks; the prompt is the plain one
        typed = [t for t in texts if t.strip() and not t.lstrip().startswith('<')]
        if typed and not has_result:
            idx, prompt = i, typed[-1]
    turn = sum(1 for m in messages[idx + 1:] if m.get('role') == 'assistant') if idx is not None else 0
    return prompt, turn


def pick_scene(agent, prompt):
    p = (prompt or '').lower()
    options = AGENTS.get(agent, [])
    if any(w in p for w in INVESTIGATE_WORDS):
        return options[0] if options else None
    return None


def wait_for_presenter(seconds=None):
    """Wait PACE seconds (or a turn's own "wait"), or until the clicker hits /next."""
    state['waiting'] = True
    gate.clear()
    gate.wait(timeout=PACE if PACE is None or seconds is None else seconds)
    state['waiting'] = False


def blocks_for(agent, body):
    """Content blocks + stop reason for this request."""
    if not body.get('tools'):
        # side request: title / summary / topic; keep it short and harmless
        sysp = json.dumps(body.get('system', ''))[:2000].lower()
        if 'json' in sysp and 'title' in sysp:
            return [{'type': 'text', 'text': '{"isNewTopic": true, "title": "Departure boards on timetable"}'}], 'end_turn'
        return [{'type': 'text', 'text': 'Departure boards alert'}], 'end_turn'

    prompt, turn = current_prompt_and_turn(body.get('messages', []))
    name = pick_scene(agent, prompt)
    if name is None:
        return [{'type': 'text', 'text': "I'm set up for the transit demo. Ask me about the departure boards alert."}], 'end_turn'
    turns = scenes()[name]['turns']
    state.update(agent=agent, scene=name, turn=turn, done=False)
    if turn >= len(turns):
        state['done'] = True
        return [{'type': 'text', 'text': 'Done.'}], 'end_turn'

    wait_for_presenter(turns[turn][0].get('wait'))
    blocks = []
    for b in turns[turn]:
        if 'tool' in b:
            blocks.append({'type': 'tool_use', 'id': 'toolu_' + uuid.uuid4().hex[:24], 'name': b['tool'],
                           'input': b['input'], 'hold': b.get('hold', False)})
        else:
            blocks.append({'type': 'text', 'text': b['text']})
    last = turn == len(turns) - 1
    state['done'] = last
    return blocks, 'end_turn' if last else 'tool_use'


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *a):
        pass

    def send_json(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(data)

    def route(self):
        """('classic' | 'enriched' | None, path without the agent prefix)."""
        path = self.path.split('?')[0]
        for agent in AGENTS:
            if path.startswith('/' + agent + '/'):
                return agent, path[len(agent) + 1:]
        return None, path

    def do_GET(self):
        if self.path.startswith('/next'):
            was = state['waiting']
            gate.set()
            return self.send_json(200, {'advanced': was, **state})
        if self.path.startswith('/state'):
            return self.send_json(200, state)
        log({'t': time.time(), 'method': 'GET', 'path': self.path})
        self.send_json(404, {'type': 'error', 'error': {'type': 'not_found_error', 'message': 'not mocked'}})

    def do_POST(self):
        n = int(self.headers.get('Content-Length') or 0)
        body = json.loads(self.rfile.read(n) or b'{}')
        agent, path = self.route()
        log({'t': time.time(), 'method': 'POST', 'path': self.path, 'agent': agent, **summarize(body)})
        if os.environ.get('MOCK_DUMP'):
            json.dump(body, open(os.path.join(HERE, 'cc', 'last_request.json'), 'w'), indent=1)
        if path.endswith('/messages/count_tokens'):
            return self.send_json(200, {'input_tokens': 1200 + 40 * len(body.get('messages', []))})
        if not path.endswith('/messages'):
            return self.send_json(404, {'type': 'error', 'error': {'type': 'not_found_error', 'message': 'not mocked'}})

        blocks, stop = blocks_for(agent, body)
        model = body.get('model', 'claude-opus-5-5')
        usage_in = 1500 + 300 * len(body.get('messages', []))
        if body.get('stream'):
            return self.stream(model, blocks, stop, usage_in)
        blocks = [{k: v for k, v in b.items() if k != 'hold'} for b in blocks]
        self.send_json(200, {'id': 'msg_' + uuid.uuid4().hex[:24], 'type': 'message', 'role': 'assistant',
                             'model': model, 'content': blocks, 'stop_reason': stop, 'stop_sequence': None,
                             'usage': {'input_tokens': usage_in, 'output_tokens': 120}})

    def stream(self, model, blocks, stop, usage_in):
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'close')
        self.end_headers()

        def ev(kind, data):
            self.wfile.write(f'event: {kind}\ndata: {json.dumps({"type": kind, **data})}\n\n'.encode())
            self.wfile.flush()

        ev('message_start', {'message': {'id': 'msg_' + uuid.uuid4().hex[:24], 'type': 'message', 'role': 'assistant',
                                         'model': model, 'content': [], 'stop_reason': None, 'stop_sequence': None,
                                         'usage': {'input_tokens': usage_in, 'output_tokens': 1}}})
        out_tokens = 1
        for i, b in enumerate(blocks):
            if b['type'] == 'text':
                ev('content_block_start', {'index': i, 'content_block': {'type': 'text', 'text': ''}})
                text = b['text']
                for j in range(0, len(text), 6):          # stream like real tokens
                    ev('content_block_delta', {'index': i, 'delta': {'type': 'text_delta', 'text': text[j:j + 6]}})
                    time.sleep(0.02)
                out_tokens += len(text) // 4
            else:
                if b.get('hold'):
                    wait_for_presenter()             # the sentence above stays readable until the next click
                ev('content_block_start', {'index': i, 'content_block': {'type': 'tool_use', 'id': b['id'],
                                                                          'name': b['name'], 'input': {}}})
                ev('content_block_delta', {'index': i, 'delta': {'type': 'input_json_delta',
                                                                 'partial_json': json.dumps(b['input'])}})
                out_tokens += 40
            ev('content_block_stop', {'index': i})
        ev('message_delta', {'delta': {'stop_reason': stop, 'stop_sequence': None}, 'usage': {'output_tokens': out_tokens}})
        ev('message_stop', {})
        self.close_connection = True


if __name__ == '__main__':
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    print(f'mock model on http://127.0.0.1:{PORT} ({f"{PACE:g} s per turn, clicker skips ahead" if PACE else "clicker only"})', flush=True)
    ThreadingHTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
