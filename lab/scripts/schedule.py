#!/usr/bin/env python3
"""Show or set the JourneyApp 5.0 rollout. The loadgen reads state/schedule.env every 2 s (host clock).
  schedule.py                          show
  schedule.py ROLLOUT_AT=14:25 [RAMP=5m] [SHARE=15]
  schedule.py ROLLOUT_IN=10m   [RAMP=5m] [SHARE=15]
  schedule.py OFF=1"""
import datetime as dt
import os
import re
import sys
import time

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE = f"{LAB}/state/schedule.env"


def seconds(s):
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*([smh]?)", s.strip())
    if not m:
        raise SystemExit(f"not a duration: {s!r} (use e.g. 90s, 10m, 1h)")
    return float(m[1]) * {"": 60, "s": 1, "m": 60, "h": 3600}[m[2]]


def read():
    s = {}
    if os.path.exists(FILE):
        for line in open(FILE):
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                s[k] = v
    return s


def show():
    s = read()
    if "ROLLOUT_AT" not in s:
        print("schedule: no rollout (all JourneyApp phones on 4.0). Set one: make schedule ROLLOUT_AT=HH:MM or ROLLOUT_IN=10m")
        return
    at, ramp, top = float(s["ROLLOUT_AT"]), float(s.get("RAMP_S", 300)), float(s.get("SHARE", 15))
    now = time.time()
    t = dt.datetime.fromtimestamp(at).strftime("%H:%M:%S")
    full = dt.datetime.fromtimestamp(at + ramp).strftime("%H:%M:%S")
    if now < at:
        left = at - now
        print(f"schedule: JourneyApp 5.0 rollout starts at {t} (in {int(left // 60)}m{int(left % 60):02d}s), "
              f"ramps to {top:g}% of the phones by {full}")
    else:
        share = top * min(1.0, (now - at) / ramp) if ramp else top
        print(f"schedule: JourneyApp 5.0 rollout started at {t} ({int((now - at) // 60)} min ago), "
              f"{share:.1f}% of the phones on 5.0 now (ramp to {top:g}% by {full})")


def main(args):
    kv = dict(a.split("=", 1) for a in args if "=" in a)
    kv = {k: v for k, v in kv.items() if v}
    if not kv:
        return show()
    os.makedirs(os.path.dirname(FILE), exist_ok=True)
    if kv.get("OFF"):
        with open(FILE, "w") as f:
            f.write("# no rollout\n")
        return show()
    if "ROLLOUT_AT" in kv:
        hh, mm = map(int, kv["ROLLOUT_AT"].split(":"))
        now = dt.datetime.now()
        at = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if at < now - dt.timedelta(minutes=1):
            at += dt.timedelta(days=1)
        at = at.timestamp()
    elif "ROLLOUT_IN" in kv:
        at = time.time() + seconds(kv["ROLLOUT_IN"])
    else:
        s = read()
        if "ROLLOUT_AT" not in s:
            raise SystemExit("give ROLLOUT_AT=HH:MM or ROLLOUT_IN=10m")
        at = float(s["ROLLOUT_AT"])
    ramp = seconds(kv.get("RAMP", "5m"))
    share = float(kv.get("SHARE", "15"))
    with open(FILE, "w") as f:
        f.write(f"# written by make schedule at {dt.datetime.now():%Y-%m-%d %H:%M:%S}\n"
                f"ROLLOUT_AT={at:.0f}\nRAMP_S={ramp:.0f}\nSHARE={share:g}\n")
    show()


if __name__ == "__main__":
    main(sys.argv[1:])
