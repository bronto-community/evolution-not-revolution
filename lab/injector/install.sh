#!/bin/bash
# Fetch the OpenTelemetry Injector and the Python agent bundle and unpack them into injector/root/,
# the way the .deb packages would install them on a box. Run once with network (`make build`).
#   libotelinject.so   open-telemetry/opentelemetry-injector release (raw shared library)
#   Python agent       open-telemetry/opentelemetry-packaging release (opentelemetry-python-autoinstrumentation .deb)
set -euo pipefail
cd "$(dirname "$0")"
INJECTOR=v0.12.0
PACKAGING=v0.0.3
ARCH=$(docker info --format '{{.Architecture}}' | sed 's/aarch64/arm64/; s/x86_64/amd64/')
sha() {   # pinned checksums (arm64, the tested arch)
  case $1 in
    libotelinject_arm64.so) echo 442483bc2db0253ef7fa622708d46b2afca32481cbcbe8db788b5e92197a5826 ;;
    opentelemetry-python-autoinstrumentation_0.0.3_arm64.deb) echo b01e899e7b773a5facb1af2be0b395133511e89025041b8a76323a9a892fe78e ;;
  esac
}
so=libotelinject_${ARCH}.so
deb=opentelemetry-python-autoinstrumentation_${PACKAGING#v}_${ARCH}.deb
mkdir -p downloads
cd downloads
[ -f "$so" ]  || curl -fsSLO "https://github.com/open-telemetry/opentelemetry-injector/releases/download/$INJECTOR/$so"
[ -f "$deb" ] || curl -fsSLO "https://github.com/open-telemetry/opentelemetry-packaging/releases/download/$PACKAGING/$deb"
for f in "$so" "$deb"; do
  want=$(sha "$f")
  if [ -n "$want" ]; then
    echo "$want  $f" | shasum -a 256 -c - >/dev/null || { echo "checksum mismatch: $f" >&2; exit 1; }
  else
    echo "no pinned checksum for $f (arch $ARCH), skipping verification" >&2
  fi
done
cd ..
rm -rf root && mkdir -p root
docker run --rm -v "$PWD:/w" -w /w debian:bookworm-slim dpkg-deb -x "downloads/$deb" root
mkdir -p root/usr/lib/opentelemetry/injector
cp "downloads/$so" root/usr/lib/opentelemetry/injector/libotelinject.so
rm -rf root/etc root/usr/share   # the config comes from injector/etc/ (ours)
echo "injector $INJECTOR + Python agent (packaging $PACKAGING, $ARCH) in injector/root/usr/lib/opentelemetry"
