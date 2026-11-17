# loadgen: the traffic of a city transit operator, sent to both labs alike (same parameters, same seeds).
#   departure boards   in the stations, poll /departures?stop=X every BOARD_POLL_S
#   JourneyApp phones  third-party app, polls /departures?stop=X every APP_POLL_S. App 5.0 adds &include=route;
#                      its share of the phones follows the rollout schedule (state/schedule.env)
#   website, ticket machines   call stops-api directly
# Writes what the riders saw to state/loadgen.json (for `make status`).
# Times come from the HOST clock (mtime of a file in the bind mount): the Docker VM clock can drift.
import asyncio
import json
import os
import random
import time
from collections import deque
from urllib.parse import urlsplit

from network import STOPS   # the same network the apps use

STATE = os.environ.get("STATE_DIR", "/state")
LABS = {name: urls.split("|") for name, urls in (t.split("=", 1) for t in os.environ["LABS"].split(","))}
BOARDS = int(os.environ.get("BOARDS", "30"))
BOARD_POLL_S = float(os.environ.get("BOARD_POLL_S", "3"))
PHONES = int(os.environ.get("PHONES", "180"))
APP_POLL_S = float(os.environ.get("APP_POLL_S", "5"))
OTHERS_RPS = float(os.environ.get("OTHERS_RPS", "60"))
BOARD_STOPS = ["hauptbahnhof", "plaerrer", "lorenzkirche", "weisser-turm", "opernhaus", "rathenauplatz",
               "fuerth-hauptbahnhof", "aufsessplatz", "friedrich-ebert-platz", "langwasser-mitte"]
PHONE_MODELS = ["Android 15; Pixel 8", "iOS 19.1; iPhone16,2", "Android 14; SM-S921B", "iOS 18.6; iPhone15,3"]
STOP_IDS = sorted(STOPS)


class HostClock:
    """time.time() corrected to the host's clock: the mtime the host file system sets on a file we write."""
    offset = 0.0

    def sync(self):
        try:
            before = time.time()
            with open(f"{STATE}/.clock", "w") as f:
                f.write(str(before))
            self.offset = os.stat(f"{STATE}/.clock").st_mtime - before
        except OSError as e:
            print(f"host clock: {e}", flush=True)

    def now(self):
        return time.time() + self.offset


clock = HostClock()
schedule, share = {}, 0.0


def read_schedule():
    """state/schedule.env: ROLLOUT_AT=<epoch> RAMP_S=<s> SHARE=<percent of phones on 5.0>. Missing: no rollout."""
    s = {}
    try:
        with open(f"{STATE}/schedule.env") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    s[k] = v
    except OSError:
        pass
    return s


def share_at(t):
    if "ROLLOUT_AT" not in schedule:
        return 0.0
    start, ramp, top = float(schedule["ROLLOUT_AT"]), float(schedule.get("RAMP_S", 300)), float(schedule.get("SHARE", 15))
    if t < start:
        return 0.0
    return top / 100 * (min(1.0, (t - start) / ramp) if ramp > 0 else 1.0)


class Window:
    """What the riders saw in the last 60 s."""
    def __init__(self):
        self.events = deque()

    def add(self, kind, ms, timetable=False, error=False):
        now = time.time()
        self.events.append((now, kind, ms, timetable, error))
        while self.events and self.events[0][0] < now - 60:
            self.events.popleft()

    def summary(self):
        out = {}
        for kind in ("board", "app4", "app5", "website"):
            e = [x for x in self.events if x[1] == kind]
            ms = sorted(x[2] for x in e if not x[4])
            tt = sum(1 for x in e if x[3])
            out[kind] = {
                "requests": len(e), "errors": sum(1 for x in e if x[4]), "timetable": tt,
                "timetable_pct": round(100 * tt / len(e), 1) if e else 0,
                "p50_ms": round(ms[len(ms) // 2]) if ms else None,
                "p95_ms": round(ms[min(len(ms) - 1, int(len(ms) * 0.95))]) if ms else None,
            }
        return out


class Client:
    """A tiny HTTP/1.1 client with keep-alive connections (stdlib only)."""
    def __init__(self, base):
        u = urlsplit(base)
        self.host, self.port, self.idle = u.hostname, u.port or 80, []

    async def get(self, path, ua):
        conn = self.idle.pop() if self.idle else None
        try:
            if conn is None:
                conn = await asyncio.open_connection(self.host, self.port)
            reader, writer = conn
            writer.write(f"GET {path} HTTP/1.1\r\nHost: {self.host}\r\nUser-Agent: {ua}\r\n\r\n".encode())
            status = int((await reader.readline()).split()[1])
            length, close = 0, False
            while (line := await reader.readline()) not in (b"\r\n", b""):
                k, _, v = line.decode().partition(":")
                if k.lower() == "content-length":
                    length = int(v)
                elif k.lower() == "connection" and v.strip().lower() == "close":
                    close = True
            body = await reader.readexactly(length)
            if close:
                writer.close()
            else:
                self.idle.append(conn)
            return status, body
        except Exception:
            if conn:
                conn[1].close()
            raise


stats = {lab: Window() for lab in LABS}
clients = {lab: (Client(urls[0]), Client(urls[1])) for lab, urls in LABS.items()}


async def request(lab, kind, client, path, ua):
    t0 = time.perf_counter()
    try:
        status, body = await asyncio.wait_for(client.get(path, ua), 60)
        timetable = kind != "website" and b'"source":"timetable"' in body
        stats[lab].add(kind, (time.perf_counter() - t0) * 1000, timetable=timetable, error=status >= 500)
    except Exception:   # connection refused while an app restarts, timeouts
        stats[lab].add(kind, (time.perf_counter() - t0) * 1000, error=True)
        await asyncio.sleep(random.uniform(1, 5))   # back off, like the clients do


async def board(lab, i):
    stop = BOARD_STOPS[i % len(BOARD_STOPS)]
    ua = f"departure-board/3.2 (station={stop}; display={1 + i // len(BOARD_STOPS)})"
    await asyncio.sleep(random.Random(i).uniform(0, BOARD_POLL_S))
    while True:
        t0 = time.monotonic()
        await request(lab, "board", clients[lab][0], f"/departures?stop={stop}", ua)
        await asyncio.sleep(max(0.05, BOARD_POLL_S - (time.monotonic() - t0)))


async def phone(lab, i, rank):
    """rank: this phone's place in the rollout order (the app stores update phones in random order)."""
    rng = random.Random(i)
    model = rng.choice(PHONE_MODELS)
    await asyncio.sleep(rng.uniform(0, APP_POLL_S))
    while True:
        stop = rng.choice(STOP_IDS)
        if rank < share * PHONES:
            await request(lab, "app5", clients[lab][0], f"/departures?stop={stop}&include=route", f"JourneyApp/5.0.0 ({model})")
        else:
            await request(lab, "app4", clients[lab][0], f"/departures?stop={stop}", f"JourneyApp/4.0.7 ({model})")
        await asyncio.sleep(rng.uniform(0.6, 1.4) * APP_POLL_S)


async def website(lab):
    """website stop pages and ticket machines (fare zones): straight to stops-api, open loop."""
    rng = random.Random("web")
    while True:
        await asyncio.sleep(rng.expovariate(OTHERS_RPS))
        stop = rng.choice(STOP_IDS)
        if rng.random() < 0.7:
            path, ua = f"/stops/{stop}", "transit-website/2026.11 (stop page)"
        else:
            path, ua = f"/stops/{stop}/platforms", "ticket-machine/7.4"
        asyncio.create_task(request(lab, "website", clients[lab][1], path, ua))


async def control():
    global schedule, share
    while True:
        clock.sync()
        schedule = read_schedule()
        now = clock.now()
        share = share_at(now)
        state = {
            "host_time": now, "drift_s": round(-clock.offset, 1), "schedule": schedule,
            "share_pct": round(100 * share, 1), "phones": PHONES, "phones_on_5_0": int(share * PHONES + 0.999999),
            "labs": {lab: w.summary() for lab, w in stats.items()},
        }
        with open(f"{STATE}/loadgen.json.tmp", "w") as f:
            json.dump(state, f, indent=1)
        os.replace(f"{STATE}/loadgen.json.tmp", f"{STATE}/loadgen.json")
        await asyncio.sleep(2)


async def main():
    print(f"loadgen: {BOARDS} boards, {PHONES} phones, {OTHERS_RPS}/s website+ticket machines -> {', '.join(LABS)}", flush=True)
    order = list(range(PHONES))
    random.Random(42).shuffle(order)   # rollout order, the same in both labs
    tasks = [asyncio.create_task(control())]
    for lab in LABS:
        tasks += [asyncio.create_task(board(lab, i)) for i in range(BOARDS)]
        tasks += [asyncio.create_task(phone(lab, i, order[i])) for i in range(PHONES)]
        tasks.append(asyncio.create_task(website(lab)))
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
