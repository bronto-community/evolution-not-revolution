#!/bin/bash
# CPU use per container (cores), averaged over N seconds, from the cgroup counters in the Docker VM.
#   scripts/cpu.sh [seconds]       (default 30)
N=${1:-30}
ids=$(docker ps -q --no-trunc)
docker run --rm --privileged --pid=host -v /sys/fs/cgroup:/cg:ro alpine:3.20 sh -c "
  read_all() { for id in $(echo $ids); do f=\$(ls -d /cg/docker/\$id /cg/system.slice/docker-\$id.scope 2>/dev/null | head -1); [ -n \"\$f\" ] && echo \$id \$(grep usage_usec \$f/cpu.stat | cut -d' ' -f2); done; }
  read_all > /tmp/a; sleep $N; read_all > /tmp/b; awk 'NR==FNR {a[\$1]=\$2; next} (\$1 in a) {print \$1, a[\$1], \$2}' /tmp/a /tmp/b" |
while read id a b; do
  printf '%-40s %5.2f\n' "$(docker inspect -f '{{.Name}}' $id | tr -d /)" "$(echo "($b - $a) / ($N * 1000000)" | bc -l)"
done | sort -k2 -rn | awk '{print} /transit|lg-test/ {t+=$2} END {printf "%-40s %5.2f\n", "TOTAL transit-*", t}'
