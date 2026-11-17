#!/bin/bash
# One full rehearsal cycle on a running lab, with measurements, logged to runs/cycle-<time>.log:
#   normal (NORMAL_S) -> rollout (ramp RAMP) -> incident (INCIDENT_S) -> make fix -> recovered (FIX_S) -> make reset
# Every phase ends with assertions on scripts/status.py --json and a few direct checks.
#   scripts/cycle.sh            defaults: NORMAL_S=180 RAMP=3m INCIDENT_S=420 FIX_S=150
set -uo pipefail
cd "$(dirname "$0")/.."
NORMAL_S=${NORMAL_S:-180}; RAMP=${RAMP:-3m}; INCIDENT_S=${INCIDENT_S:-420}; FIX_S=${FIX_S:-150}
mkdir -p runs
LOG=runs/cycle-$(date +%Y%m%d-%H%M%S).log
exec > >(tee "$LOG") 2>&1
FAIL=0
say() { echo "[$(date +%T)] $*"; }
check() { if eval "$2"; then say "PASS $1"; else say "FAIL $1"; FAIL=$((FAIL + 1)); fi; }
js() { scripts/status.py --json | python3 -c "import json,sys; d=json.load(sys.stdin); print($1)"; }
watch_for() { local end=$(( $(date +%s) + $1 )); while [ "$(date +%s)" -lt "$end" ]; do scripts/status.py --line; sleep 30; done; }

say "cycle start: NORMAL_S=$NORMAL_S RAMP=$RAMP INCIDENT_S=$INCIDENT_S FIX_S=$FIX_S"
make -s reset >/dev/null
say "phase 1: normal"; watch_for "$NORMAL_S"
for lab in classic enriched; do
  check "$lab: boards from timetable < 2% before rollout" "[ \$(js 'd[\"labs\"][\"$lab\"][\"riders\"][\"board\"][\"timetable_pct\"] < 2') = True ]"
  check "$lab: board p95 < 150 ms before rollout" "[ \$(js 'd[\"labs\"][\"$lab\"][\"riders\"][\"board\"][\"p95_ms\"] < 150') = True ]"
done
base_c=$(js 'd["labs"]["classic"]["stops_api"]["rps"]'); base_e=$(js 'd["labs"]["enriched"]["stops_api"]["rps"]')
say "stops-api baseline req/s: classic $base_c enriched $base_e"

say "phase 2: rollout"; make -s schedule ROLLOUT_IN=5s RAMP="$RAMP"; t0=$(date +%s)
alert_c=""; alert_e=""
end=$(( t0 + INCIDENT_S )); while [ "$(date +%s)" -lt "$end" ]; do
  scripts/status.py --line
  [ -z "$alert_c" ] && [ "$(js '(d["labs"]["classic"]["alert"] or {}).get("state")')" = ACTIVE ] && alert_c=$(( $(date +%s) - t0 ))
  [ -z "$alert_e" ] && [ "$(js '(d["labs"]["enriched"]["alert"] or {}).get("state")')" = ACTIVE ] && alert_e=$(( $(date +%s) - t0 ))
  sleep 30
done
say "alert fired after rollout start: classic ${alert_c:-never} s, enriched ${alert_e:-never} s"
check "alert fired in both labs" "[ -n '$alert_c' ] && [ -n '$alert_e' ]"
for lab in classic enriched; do
  check "$lab: boards from timetable > 10% during incident" "[ \$(js 'd[\"labs\"][\"$lab\"][\"riders\"][\"board\"][\"timetable_pct\"] > 10') = True ]"
  check "$lab: stops-api p95 handling < 60 ms during incident" "[ \$(js 'd[\"labs\"][\"$lab\"][\"stops_api\"][\"p95_ms\"] < 60') = True ]"
done
inc_c=$(js 'd["labs"]["classic"]["stops_api"]["rps"]'); inc_e=$(js 'd["labs"]["enriched"]["stops_api"]["rps"]')
say "stops-api req/s during incident: classic $inc_c (x$(echo "scale=2; $inc_c / $base_c" | bc)), enriched $inc_e (x$(echo "scale=2; $inc_e / $base_e" | bc))"
check "stops-api rate rise < 2x (classic)" "[ \$(echo '$inc_c < 2 * $base_c' | bc) = 1 ]"
check "stops-api rate rise < 2x (enriched)" "[ \$(echo '$inc_e < 2 * $base_e' | bc) = 1 ]"
scripts/verify.py incident || FAIL=$((FAIL + 1))
scripts/cpu.sh 20 | grep TOTAL

say "phase 3: make fix"; make -s fix; t1=$(date +%s); rec_c=""; rec_e=""
end=$(( t1 + FIX_S )); while [ "$(date +%s)" -lt "$end" ]; do
  sleep 15; scripts/status.py --line
  [ -z "$rec_c" ] && [ "$(js 'd["labs"]["classic"]["riders"]["board"]["timetable_pct"] < 2')" = True ] && rec_c=$(( $(date +%s) - t1 ))
  [ -z "$rec_e" ] && [ "$(js 'd["labs"]["enriched"]["riders"]["board"]["timetable_pct"] < 2')" = True ] && rec_e=$(( $(date +%s) - t1 ))
done
say "boards < 2% from timetable (60 s window) after fix: classic ${rec_c:-never} s, enriched ${rec_e:-never} s"
check "recovered within ${FIX_S}s in both labs" "[ -n '$rec_c' ] && [ -n '$rec_e' ]"

say "phase 4: make reset"; make -s reset
check "schedule off after reset" "! grep -q ROLLOUT_AT state/schedule.env"
check "pool size back to 5" "[ \"\$(js 'd[\"pool_size\"]')\" = 5 ]"
scripts/verify.py classic || FAIL=$((FAIL + 1))
say "cycle done: $FAIL failure(s). Log: $LOG"
exit $FAIL
