#!/bin/bash
# scripts/watch.sh [seconds]: one status line every N seconds (default 30)
cd "$(dirname "$0")/.."
while true; do scripts/status.py --line; sleep "${1:-30}"; done
