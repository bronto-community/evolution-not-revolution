#!/usr/bin/env bash
# Real Claude Code (pinned in agent-demo/cc) talking to the scripted model in mock_model.py.
#   bash agent-demo/claude_live.sh classic    agent with log search on classic-logs only
#   bash agent-demo/claude_live.sh enriched   same agent, logs + traces
# Nothing here calls the real Anthropic API: ANTHROPIC_BASE_URL is the local mock.
D="$(cd "$(dirname "$0")" && pwd)"
LAB="${1:-classic}"
case "$LAB" in
  classic|enriched) ;;
  *) echo "usage: claude_live.sh classic|enriched" >&2; exit 2 ;;
esac
# A fresh Claude Code home per start (one per lab, so both terminals can run side by side):
# no history, no resumed session, onboarding done, light theme.
HOME_DIR="$D/cc/home-$LAB"
# The seed and the MCP config name this directory as @DEMO_DIR@; fill in where the repo is checked out.
rm -rf "$HOME_DIR"; mkdir -p "$HOME_DIR"
sed "s#@DEMO_DIR@#$D#g" "$D/cc/claude.seed.json" > "$HOME_DIR/.claude.json"
MCP="$HOME_DIR/mcp.json"; sed "s#@DEMO_DIR@#$D#g" "$D/cc/mcp.$LAB.json" > "$MCP"
cd "$D/transit-platform"
# Start clean: drop anything inherited from a parent Claude Code session.
for v in $(env | grep -oE '^(CLAUDE|ANTHROPIC)[A-Z_]*'); do unset "$v"; done
export CLAUDE_CONFIG_DIR="$HOME_DIR"
export ANTHROPIC_BASE_URL="http://127.0.0.1:8787/$LAB"         # the path tells the mock which lab is asking
export ANTHROPIC_API_KEY="sk-ant-demo-mock-not-a-real-key"     # placeholder; the mock ignores it
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 DISABLE_AUTOUPDATER=1
exec "$D/cc/node_modules/.bin/claude" --mcp-config "$MCP" --strict-mcp-config ${DEMO_CLAUDE_FLAGS---verbose}
