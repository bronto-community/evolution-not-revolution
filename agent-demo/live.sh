#!/usr/bin/env bash
# Both demo terminals, loopback only (they're writable):
#   localhost:7681  classic:  real Claude Code, log search on classic-logs
#   localhost:7682  enriched: real Claude Code, logs + traces
# plus the scripted model on 127.0.0.1:8787. Extra args go to mock_model.py (e.g. --pace 3, --manual).
# Ctrl-C stops all three.
cd "$(dirname "$0")"
FONT_SIZE="${FONT_SIZE:-24}"
TTYD_OPTS=(--writable --interface lo0 --index cc/ttyd-index.html
  -t fontSize=$FONT_SIZE -t lineHeight=1.15 -t 'fontFamily=Menlo, Monaco, monospace'
  -t 'theme={"background":"#FAF8F4","foreground":"#2B2620","cursor":"#2B2620","cursorAccent":"#FAF8F4","selectionBackground":"#C2CEFF","black":"#2B2620","brightBlack":"#857B6E","white":"#E7E0D4","brightWhite":"#FFFFFF"}'
  -t rendererType=dom -t disableLeaveAlert=true -t disableResizeOverlay=true -t titleFixed=claude)
python3 -I mock_model.py "$@" & MOCK=$!
ttyd --port 7682 "${TTYD_OPTS[@]}" bash claude_live.sh enriched & ENR=$!
trap 'kill $MOCK $ENR 2>/dev/null' EXIT
ttyd --port 7681 "${TTYD_OPTS[@]}" bash claude_live.sh classic
