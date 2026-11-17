#!/bin/bash
# docker compose for one project, with the right files:
#   scripts/lab.sh classic|enriched|shared <compose args...>
set -euo pipefail
cd "$(dirname "$0")/.."
unset LAB   # comes from env/<lab>.env, never from the caller
export STOPS_API_POOL_SIZE=${STOPS_API_POOL_SIZE:-$(cat state/pool-size 2>/dev/null || echo 5)}
lab=${1:?usage: lab.sh classic|enriched|shared <compose args>}; shift
case $lab in
  classic)  exec docker compose -p transit-classic  --env-file env/classic.env  -f compose.yaml -f compose.classic.yaml "$@" ;;
  enriched) exec docker compose -p transit-enriched --env-file env/enriched.env -f compose.yaml -f compose.enriched.yaml "$@" ;;
  shared)   exec docker compose -f compose.shared.yaml "$@" ;;
  *) echo "unknown lab $lab" >&2; exit 2 ;;
esac
