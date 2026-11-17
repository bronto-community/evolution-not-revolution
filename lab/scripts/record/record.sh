#!/bin/bash
# make record: videos of the before/after click paths into recordings/ (needs the incident on). Parts: before after
set -euo pipefail
cd "$(dirname "$0")/../.."
exec node scripts/record/record.js "$@"
